import os
import re
import urllib.parse
import pyhtml
import nav

ROWS_PER_PAGE = 10

def _esc(s):
    return str(s).replace("'", "''")

def _antigen_name(full_name):
    n = full_name.split(",")[0]
    return re.sub(r'-containing vaccine', '', n, flags=re.IGNORECASE).strip()

def _cov_class(v):
    if v is None: return "cov-mid"
    return "cov-high" if v >= 90 else ("cov-mid" if v >= 70 else "cov-low")

def _delta_class(v):
    if v is None: return "delta-zero"
    if v > 0:  return "delta-pos"
    if v < 0:  return "delta-neg"
    return "delta-zero"


def get_page_html(form_data):
    def _get(key, default=""):
        v = form_data.get(key)
        return (v[0] if v else default).strip()

    antigen_f    = _get("antigen")
    start_year_f = _get("start_year", "2000")
    end_year_f   = _get("end_year",   "2024")
    top_f        = _get("top",        "10")
    sort_f       = _get("sort",       "increase_desc")

    try: page = max(1, int(_get("page", "1")))
    except: page = 1

    db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'immunisation.db')

    antigen_opts = pyhtml.get_results_from_query(db,
        "SELECT AntigenID, name FROM Antigen ORDER BY AntigenID")
    year_opts = pyhtml.get_results_from_query(db,
        "SELECT DISTINCT year FROM Vaccination ORDER BY year DESC")

    # Parse + validate years
    try: start_y = int(start_year_f)
    except: start_y = 2000
    try: end_y = int(end_year_f)
    except: end_y = 2024
    if end_y < start_y:
        start_y, end_y = end_y, start_y  # swap silently

    # Top N
    TOP_OPTS = [("5","Top 5"), ("10","Top 10"), ("20","Top 20"), ("50","Top 50"), ("100","Top 100")]
    TOP_MAP  = {v: int(v) for v, _ in TOP_OPTS}
    top_n    = TOP_MAP.get(top_f, 10)

    # Sort options
    SORT_MAP = {
        "increase_desc":  "(e.coverage - s.coverage) DESC",
        "increase_asc":   "(e.coverage - s.coverage) ASC",
        "country_asc":    "c.name ASC",
        "country_desc":   "c.name DESC",
        "region_asc":     "r.region ASC",
        "region_desc":    "r.region DESC",
        "start_desc":     "s.coverage DESC",
        "start_asc":      "s.coverage ASC",
        "end_desc":       "e.coverage DESC",
        "end_asc":        "e.coverage ASC",
    }
    SORT_LABELS = {
        "increase_desc": "Highest Increase",
        "increase_asc":  "Lowest Increase",
        "country_asc":   "Country (A→Z)",
        "country_desc":  "Country (Z→A)",
        "region_asc":    "Region (A→Z)",
        "region_desc":   "Region (Z→A)",
        "start_desc":    "Start Rate (High→Low)",
        "start_asc":     "Start Rate (Low→High)",
        "end_desc":      "End Rate (High→Low)",
        "end_asc":       "End Rate (Low→High)",
    }
    order_expr = SORT_MAP.get(sort_f, "(e.coverage - s.coverage) DESC")

    # Antigen WHERE condition (optional — applied inside both subqueries)
    a_cond = f"AND antigen = '{_esc(antigen_f)}'" if antigen_f else ""

    # ══════════════════════════════════════════════════════════════════
    # Core SQL: two subquery JOINs (start year + end year dataset).
    # INNER JOIN guarantees BOTH years must have real data for the country.
    # typeof='real' excludes 5415 rows where missing data is stored as '' not NULL.
    # AVG+GROUP BY collapses to 1 row per country — prevents cross-product
    # duplicates when no antigen is selected (N antigens × M antigens = N×M rows).
    # When antigen IS selected: one row per country → AVG = that single value.
    # All sorting and limiting done in SQL — no Python post-processing.
    # ══════════════════════════════════════════════════════════════════
    def _sub(yr):
        # Vaccination rate = doses / total country population × 100
        # JOIN CountryPopulation to get total population for that year.
        # AVG + GROUP BY collapses to 1 row per country (prevents cross-product
        # duplicates when multiple antigens exist and no antigen filter is set).
        # typeof='real' excludes rows where doses is stored as '' not NULL.
        return f"""(
            SELECT v.country,
                   AVG(v.doses / p.population * 100) AS coverage
            FROM Vaccination v
            JOIN CountryPopulation p ON v.country = p.country AND p.year = {yr}
            WHERE v.year = {yr} AND typeof(v.doses) = 'real'
              AND p.population > 0 {a_cond}
            GROUP BY v.country
        )"""

    join_sql = f"""
        FROM Country c
        JOIN Region  r ON c.region     = r.RegionID
        JOIN {_sub(start_y)} s ON c.CountryID = s.country
        JOIN {_sub(end_y)}   e ON c.CountryID = e.country"""

    select_cols = """
        c.name                                      AS country_name,
        r.region                                    AS region_name,
        ROUND(s.coverage, 2)                        AS start_rate,
        ROUND(e.coverage, 2)                        AS end_rate,
        ROUND(e.coverage - s.coverage, 2)           AS increase"""

    # Total matching countries (for results bar)
    n_total = pyhtml.get_results_from_query(db,
        f"SELECT COUNT(*) {join_sql}")[0][0]

    # Top N rows (sorted, limited — all in SQL)
    top_rows = pyhtml.get_results_from_query(db, f"""
        SELECT {select_cols}
        {join_sql}
        ORDER BY {order_expr}
        LIMIT {top_n}""")

    # Paginate within the already-limited top_rows
    cnt         = len(top_rows)
    total_pages = max(1, -(-cnt // ROWS_PER_PAGE))
    page        = min(page, total_pages)
    rows        = top_rows[(page-1)*ROWS_PER_PAGE : page*ROWS_PER_PAGE]

    # ── URL builder ──
    def url(**kw):
        p = {}
        if antigen_f:        p["antigen"]    = antigen_f
        p["start_year"]  = str(start_y)
        p["end_year"]    = str(end_y)
        if top_f != "10":    p["top"]        = top_f
        if sort_f != "increase_desc": p["sort"] = sort_f
        p["page"] = str(page)
        p.update(kw)
        qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in p.items() if v)
        return f"/binh_page_3?{qs}#results-section" if qs else "/binh_page_3#results-section"

    # ── Filter tags ──
    filter_tags = ""
    if antigen_f:
        nm = next((_antigen_name(n) for aid, n in antigen_opts if aid == antigen_f), antigen_f)
        filter_tags += f'<span class="filter-tag">{nm}</span> '
    filter_tags += f'<span class="filter-tag">{start_y} → {end_y}</span> '
    filter_tags += f'<span class="filter-tag">Top {top_n}</span> '

    # ── Dropdown builders ──
    def sel_antigen():
        o = '<option value="">All Antigens</option>'
        for aid, an in antigen_opts:
            s = "selected" if aid == antigen_f else ""
            o += f'<option value="{aid}" {s}>{_antigen_name(an)}</option>'
        return f'<select name="antigen" class="filter-select">{o}</select>'

    def sel_start_year():
        o = ""
        for (yr,) in year_opts:
            s = "selected" if int(yr) == start_y else ""
            o += f'<option value="{yr}" {s}>{yr}</option>'
        return f'<select name="start_year" class="filter-select">{o}</select>'

    def sel_end_year():
        o = ""
        for (yr,) in year_opts:
            s = "selected" if int(yr) == end_y else ""
            o += f'<option value="{yr}" {s}>{yr}</option>'
        return f'<select name="end_year" class="filter-select">{o}</select>'

    def sel_top():
        o = ""
        for val, label in TOP_OPTS:
            s = "selected" if val == top_f else ""
            o += f'<option value="{val}" {s}>{label}</option>'
        return f'<select name="top" class="filter-select">{o}</select>'

    def sel_sort():
        o = ""
        for val, label in SORT_LABELS.items():
            s = "selected" if val == sort_f else ""
            o += f'<option value="{val}" {s}>{label}</option>'
        return f'<select name="sort" class="filter-select">{o}</select>'

    # ── Table rows ──
    def rows_html():
        if not rows:
            return '<tr><td colspan="6" class="no-data">No countries found — check that both years have population and vaccination data.</td></tr>'
        out = ""
        for i, (cname, rname, start_r, end_r, delta) in enumerate(rows):
            rank   = (page - 1) * ROWS_PER_PAGE + i + 1
            s_html = f"{start_r}%" if start_r is not None else "—"
            e_html = f"{end_r}%"   if end_r   is not None else "—"
            if delta is not None:
                sign   = "+" if delta > 0 else ""
                d_html = f'<span class="delta-badge {_delta_class(delta)}">{sign}{delta}%</span>'
            else:
                d_html = "—"
            out += (f"<tr>"
                    f"<td><strong>{rank}</strong></td>"
                    f"<td>{cname}</td>"
                    f"<td>{rname}</td>"
                    f"<td>{s_html}</td>"
                    f"<td>{e_html}</td>"
                    f"<td>{d_html}</td>"
                    f"</tr>")
        return out

    # ── Pagination ──
    def paginate():
        if total_pages <= 1:
            return ""
        shown = {1, total_pages, page}
        if page > 1: shown.add(page - 1)
        if page < total_pages: shown.add(page + 1)

        def purl(p_): return url(page=str(p_))

        first = (f'<a href="{purl(1)}" class="page-btn">&#8810;</a>'
                 if page > 1 else '<span class="page-btn disabled">&#8810;</span>')
        prev  = (f'<a href="{purl(page-1)}" class="page-btn">&lsaquo;</a>'
                 if page > 1 else '<span class="page-btn disabled">&lsaquo;</span>')
        nxt   = (f'<a href="{purl(page+1)}" class="page-btn">&rsaquo;</a>'
                 if page < total_pages else '<span class="page-btn disabled">&rsaquo;</span>')
        last  = (f'<a href="{purl(total_pages)}" class="page-btn">&#8811;</a>'
                 if page < total_pages else '<span class="page-btn disabled">&#8811;</span>')

        mid, prev_p = [], 0
        for p_ in sorted(shown):
            if p_ - prev_p > 1:
                mid.append('<span class="page-ellipsis">...</span>')
            mid.append(f'<span class="page-btn active">{p_}</span>' if p_ == page
                       else f'<a href="{purl(p_)}" class="page-btn">{p_}</a>')
            prev_p = p_

        start_r = (page - 1) * ROWS_PER_PAGE + 1
        end_r   = min(page * ROWS_PER_PAGE, cnt)
        return f"""<div class="pagination">
            <span class="pagination-info">Showing {start_r}&#8211;{end_r} of {cnt}</span>
            <div class="pagination-btns">{first}{prev}{"".join(mid)}{nxt}{last}</div>
        </div>"""

    # ── Sortable headers ──
    _SIMG = '<img src="/images/order%20icon.png" class="sort-icon-img" alt="">'

    def th(label, asc_key, desc_key):
        is_asc = sort_f == asc_key
        next_k = desc_key if is_asc else asc_key
        cls    = " sort-asc" if is_asc else (" sort-desc" if sort_f == desc_key else "")
        return (f'<th class="sortable{cls}">'
                f'<a href="{url(sort=next_k, page="1")}" class="sort-link">'
                f'{label} {_SIMG}</a></th>')

    # ── Excel export (all top_rows, not just current page) ──
    def _xls_export():
        def esc(v):
            s = str(v if v is not None else "")
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        headers = ["Rank", "Country", "Region",
                   f"Coverage {start_y} (%)", f"Coverage {end_y} (%)", "Increase (%)"]
        ths = "".join(f"<th>{esc(h)}</th>" for h in headers)
        trs = ""
        for i, (cn, rn, sc, ec, d) in enumerate(top_rows):
            sign = "+" if (d or 0) > 0 else ""
            trs += (f"<tr><td>{i+1}</td><td>{esc(cn)}</td><td>{esc(rn)}</td>"
                    f"<td>{sc}</td><td>{ec}</td>"
                    f"<td>{sign}{d if d is not None else ''}</td></tr>")
        html = (f'<html xmlns:x="urn:schemas-microsoft-com:office:excel">'
                f'<head><meta charset="UTF-8"></head>'
                f'<body><table><tr>{ths}</tr>{trs}</table></body></html>')
        return "data:application/vnd.ms-excel;charset=utf-8," + urllib.parse.quote(html)

    export_href = _xls_export()

    # ── CSS + nav ──
    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
    with open(css_file, 'r', encoding='utf-8') as f:
        css = f.read()

    nav_html    = nav.get_nav_html("/binh_page_3")
    footer_html = nav.get_footer_html()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>ImmuniData - Vaccination Improvement Explorer</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
</head>
<body>

{nav_html}

<div class="page-header">
    <h1>Vaccination Improvement Explorer</h1>
    <p>Identify countries with the biggest improvement in vaccination rates between two selected years for a specific antigen</p>
</div>

<div class="filter-card">
    <form method="GET" action="/binh_page_3">
        <div class="filter-row">
            <div class="filter-group"><label>Antigen</label>{sel_antigen()}</div>
            <div class="filter-group"><label>Start Year</label>{sel_start_year()}</div>
            <div class="filter-group"><label>End Year</label>{sel_end_year()}</div>
            <div class="filter-group"><label>Top</label>{sel_top()}</div>
            <div class="filter-group"><label>Sort by</label>{sel_sort()}</div>
            <div class="filter-actions">
                <button type="submit" class="btn-apply">
                    <img src="/images/filter%20icon.png" alt=""> Apply Filters
                </button>
                <a href="/binh_page_3" class="btn-reset">
                    <img src="/images/reset%20icon.png" alt=""> Reset
                </a>
            </div>
        </div>
    </form>
</div>

<div class="results-bar" id="results-section">
    <img src="/images/showing_result%20icon.png" class="results-icon" alt="">
    <span class="results-label">Showing result for:</span>
    {filter_tags}
    <span class="ready-badge">Ready</span>
    <span class="results-count">{n_total} countries with data in both years</span>
    <span class="results-sep">|</span>
    <span class="results-note">Last updated WHO dataset 2000&#8211;2024</span>
</div>

<div class="single-table-wrap">
    <div class="table-card">
        <input type="radio" id="t3-table" name="t3-view" checked class="tab-radio">
        <input type="radio" id="t3-chart" name="t3-view"         class="tab-radio">
        <div class="tab-bar">
            <div class="tab-btn-group">
                <label for="t3-table" class="tab-btn t3-table-label">
                    <img src="/images/table%20icon.png" alt=""> Table
                </label>
                <label for="t3-chart" class="tab-btn t3-chart-label">
                    <img src="/images/chart%20icon.png" alt=""> Chart
                </label>
            </div>
        </div>

        <div class="t3-table-panel">
            <div class="table-header-row">
                <span class="table-title">TOP COUNTRIES BY VACCINATION RATE INCREASE</span>
                <a href="{export_href}" download="vaccination_improvement.xls" class="export-btn">
                    <img src="/images/export%20icon.png" alt=""> Export Data
                </a>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead><tr>
                        <th>Rank</th>
                        {th("Country",                        "country_asc",  "country_desc")}
                        {th("Region",                         "region_asc",   "region_desc")}
                        {th(f"Vaccination Rate In {start_y}", "start_asc",    "start_desc")}
                        {th(f"Vaccination Rate In {end_y}",   "end_asc",      "end_desc")}
                        {th("Vaccination Rate Increase",      "increase_asc", "increase_desc")}
                    </tr></thead>
                    <tbody>{rows_html()}</tbody>
                </table>
            </div>
            {paginate()}
        </div>

        <div class="t3-chart-panel">
            <div class="chart-placeholder">&#9650; Chart view coming soon</div>
        </div>
    </div>
</div>

<div class="info-note">
    <img src="/images/iconinfo.png" class="info-icon-img" alt="">
    <span>Note: Only countries with vaccination and population data for <strong>BOTH</strong>
    {start_y} and {end_y} are included.
    <strong>Vaccination Rate = doses administered &divide; total country population &times; 100</strong>.
    Increase = End Year Rate &minus; Start Year Rate (percentage points).
    If no antigen is selected, rates are averaged across all available antigens.</span>
</div>

{footer_html}

</body>
</html>"""
