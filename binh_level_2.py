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


def get_page_html(form_data):
    def _get(key, default=""):
        v = form_data.get(key)
        return (v[0] if v else default).strip()

    antigen_f = _get("antigen")
    year_f    = _get("year")
    region_f  = _get("region")
    country_f = _get("country")
    sort_f    = _get("sort",  "coverage_desc")
    sort2_f   = _get("sort2", "countries_desc")

    try: page1 = max(1, int(_get("page1", "1")))
    except: page1 = 1
    try: page2 = max(1, int(_get("page2", "1")))
    except: page2 = 1

    db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'immunisation.db')

    antigen_opts = pyhtml.get_results_from_query(db, "SELECT AntigenID, name FROM Antigen ORDER BY AntigenID")
    year_opts    = pyhtml.get_results_from_query(db, "SELECT DISTINCT year FROM Vaccination ORDER BY year DESC")
    region_opts  = pyhtml.get_results_from_query(db, "SELECT RegionID, region FROM Region ORDER BY region")

    # Auto-derive region from country so filtering is always consistent
    if country_f:
        _r = pyhtml.get_results_from_query(db,
            f"SELECT region FROM Country WHERE CountryID = '{_esc(country_f)}'")
        if _r:
            region_f = str(_r[0][0])

    # Country list limited to the selected region (if any)
    if region_f:
        country_opts = pyhtml.get_results_from_query(db,
            f"SELECT CountryID, name FROM Country WHERE region = '{_esc(region_f)}' ORDER BY name")
    else:
        country_opts = pyhtml.get_results_from_query(db,
            "SELECT CountryID, name FROM Country ORDER BY name")

    # ── WHERE conditions (applied to both tables) ──
    def base_conds():
        c = ["v.coverage IS NOT NULL"]
        if antigen_f: c.append(f"v.antigen = '{_esc(antigen_f)}'")
        if year_f and year_f.isdigit(): c.append(f"v.year = {int(year_f)}")
        if region_f:  c.append(f"c.region  = '{_esc(region_f)}'")
        if country_f: c.append(f"v.country = '{_esc(country_f)}'")
        return " AND ".join(c)

    where_base = "WHERE " + base_conds()

    # Shared JOIN used in inner queries
    JOINS = """FROM Vaccination v
        JOIN Country c ON v.country = c.CountryID
        JOIN Region  r ON c.region  = r.RegionID
        JOIN Antigen a ON v.antigen  = a.AntigenID"""

    SORT_MAP = {
        "coverage_desc": "ROUND(AVG(v.coverage),1) DESC",
        "coverage_asc":  "ROUND(AVG(v.coverage),1) ASC",
        "year_desc":     "v.year DESC",
        "year_asc":      "v.year ASC",
        "country_asc":   "c.name ASC",
        "country_desc":  "c.name DESC",
        "antigen_asc":   "a.AntigenID ASC",
        "antigen_desc":  "a.AntigenID DESC",
        "region_asc":    "r.region ASC",
        "region_desc":   "r.region DESC",
    }
    SORT_LABELS = {
        "coverage_desc": "% of Target (High→Low)",
        "coverage_asc":  "% of Target (Low→High)",
        "year_desc":     "Year (Newest First)",
        "year_asc":      "Year (Oldest First)",
        "country_asc":   "Country (A→Z)",
        "country_desc":  "Country (Z→A)",
        "antigen_asc":   "Antigen (A→Z)",
        "antigen_desc":  "Antigen (Z→A)",
        "region_asc":    "Region (A→Z)",
        "region_desc":   "Region (Z→A)",
    }
    order_by  = SORT_MAP.get(sort_f,  "ROUND(AVG(v.coverage),1) DESC")
    SORT2_MAP = {
        "countries_desc": "countries_met DESC",
        "countries_asc":  "countries_met ASC",
        "year2_desc":     "sub.year DESC",
        "year2_asc":      "sub.year ASC",
        "antigen2_asc":   "a.AntigenID ASC",
        "antigen2_desc":  "a.AntigenID DESC",
        "region2_asc":    "r.region ASC",
        "region2_desc":   "r.region DESC",
    }
    order_by2 = SORT2_MAP.get(sort2_f, "countries_met DESC")

    # ══════════════════════════════════════════════════════
    # TABLE 1: Countries meeting ≥90% vaccination target
    # Duplicates handled with GROUP BY + AVG(coverage)
    # ══════════════════════════════════════════════════════
    t1_inner = f"""
        SELECT a.AntigenID, v.year, c.name  AS country_name,
               r.region   AS region_name,
               ROUND(AVG(v.coverage), 1) AS pct
        {JOINS}
        {where_base}
        GROUP BY a.AntigenID, v.year, v.country
        HAVING AVG(v.coverage) >= 90"""

    cnt1  = pyhtml.get_results_from_query(db, f"SELECT COUNT(*) FROM ({t1_inner})")[0][0]
    n_ctr = pyhtml.get_results_from_query(db, f"""
        SELECT COUNT(DISTINCT v.country) {JOINS} {where_base}
        AND v.coverage >= 90""")[0][0]

    total_p1 = max(1, -(-cnt1 // ROWS_PER_PAGE))
    page1    = min(page1, total_p1)
    rows1    = pyhtml.get_results_from_query(db, f"""
        {t1_inner}
        ORDER BY {order_by}
        LIMIT {ROWS_PER_PAGE} OFFSET {(page1-1)*ROWS_PER_PAGE}""")

    # ══════════════════════════════════════════════════════
    # TABLE 2: Per region — how many countries met ≥90%
    # ══════════════════════════════════════════════════════
    t2_inner = f"""
        SELECT a.AntigenID, sub.year, r.region AS region_name,
               COUNT(*) AS countries_met
        FROM (
            SELECT v.antigen, v.year, v.country, c.region AS reg_id
            FROM Vaccination v
            JOIN Country c ON v.country = c.CountryID
            {where_base}
            GROUP BY v.antigen, v.year, v.country
            HAVING AVG(v.coverage) >= 90
        ) sub
        JOIN Region  r ON sub.reg_id  = r.RegionID
        JOIN Antigen a ON sub.antigen = a.AntigenID
        GROUP BY a.AntigenID, sub.year, r.RegionID"""

    cnt2     = pyhtml.get_results_from_query(db, f"SELECT COUNT(*) FROM ({t2_inner})")[0][0]
    total_p2 = max(1, -(-cnt2 // ROWS_PER_PAGE))
    page2    = min(page2, total_p2)
    rows2    = pyhtml.get_results_from_query(db, f"""
        {t2_inner}
        ORDER BY {order_by2}
        LIMIT {ROWS_PER_PAGE} OFFSET {(page2-1)*ROWS_PER_PAGE}""")

    # ── Export: all filtered rows (no pagination) ──
    _exp1 = pyhtml.get_results_from_query(db, f"{t1_inner} ORDER BY {order_by}")
    _exp2 = pyhtml.get_results_from_query(db, f"{t2_inner} ORDER BY {order_by2}")

    def _xls_export(headers, rows):
        def esc(v):
            s = str(v if v is not None else "")
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        ths = "".join(f"<th>{esc(h)}</th>" for h in headers)
        trs = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in rows)
        html = (f'<html xmlns:x="urn:schemas-microsoft-com:office:excel">'
                f'<head><meta charset="UTF-8"></head>'
                f'<body><table><tr>{ths}</tr>{trs}</table></body></html>')
        return "data:application/vnd.ms-excel;charset=utf-8," + urllib.parse.quote(html)

    export1_href = _xls_export(["Antigen", "Year", "Country", "Region", "% of Target"], _exp1)
    export2_href = _xls_export(["Antigen", "Year", "Region", "Countries Met >=90%"], _exp2)

    # ── URL builder (preserves all filters) ──
    def url(**kw):
        p = {}
        if antigen_f: p["antigen"] = antigen_f
        if year_f:    p["year"]    = year_f
        if region_f:  p["region"]  = region_f
        if country_f: p["country"] = country_f
        if sort_f  and sort_f  != "coverage_desc":  p["sort"]  = sort_f
        if sort2_f and sort2_f != "countries_desc": p["sort2"] = sort2_f
        p["page1"] = str(page1)
        p["page2"] = str(page2)
        p.update(kw)
        qs = "&".join(f"{k}={v}" for k, v in p.items() if v)
        return f"/binh_page_2?{qs}" if qs else "/binh_page_2"

    # ── Active filter tags ──
    filter_tags = ""
    if antigen_f:
        nm = next((_antigen_name(n) for aid, n in antigen_opts if aid == antigen_f), antigen_f)
        filter_tags += f'<span class="filter-tag">{nm}</span> '
    if year_f:
        filter_tags += f'<span class="filter-tag">{year_f}</span> '
    if region_f:
        rn = next((rn for rid, rn in region_opts if str(rid) == str(region_f)), region_f)
        filter_tags += f'<span class="filter-tag">{rn}</span> '
    if country_f:
        cn = next((cn for cid, cn in country_opts if cid == country_f), country_f)
        filter_tags += f'<span class="filter-tag">{cn}</span> '
    if not filter_tags:
        filter_tags = '<span style="color:#777;font-size:13px">All data</span> '

    # ── Dropdown builders ──
    def sel_antigen():
        o = '<option value="">All Antigens</option>'
        for aid, an in antigen_opts:
            s = "selected" if aid == antigen_f else ""
            o += f'<option value="{aid}" {s}>{_antigen_name(an)}</option>'
        return f'<select name="antigen" class="filter-select">{o}</select>'

    def sel_year():
        o = '<option value="">All Years</option>'
        for (yr,) in year_opts:
            s = "selected" if str(yr) == year_f else ""
            o += f'<option value="{yr}" {s}>{yr}</option>'
        return f'<select name="year" class="filter-select">{o}</select>'

    def sel_region():
        o = '<option value="">All Regions</option>'
        for rid, rn in region_opts:
            s = "selected" if str(rid) == str(region_f) else ""
            o += f'<option value="{rid}" {s}>{rn.replace("&","&amp;")}</option>'
        return f'<select id="sel-region" name="region" class="filter-select">{o}</select>'

    def sel_country():
        o = '<option value="">All Countries</option>'
        for cid, cn in country_opts:
            s = "selected" if cid == country_f else ""
            o += f'<option value="{cid}" {s}>{cn}</option>'
        return f'<select id="sel-country" name="country" class="filter-select">{o}</select>'

    def sel_sort():
        o = ""
        for val, label in SORT_LABELS.items():
            s = "selected" if val == sort_f else ""
            o += f'<option value="{val}" {s}>{label}</option>'
        return f'<select name="sort" class="filter-select">{o}</select>'

    # ── Table row builders ──
    def rows1_html():
        if not rows1:
            return '<tr><td colspan="5" class="no-data">No countries found for the selected filters</td></tr>'
        out = ""
        for aid, yr, cname, rname, pct in rows1:
            badge = f'<span class="cov-badge {_cov_class(pct)}">{pct}%</span>' if pct else "—"
            out += f"<tr><td>{aid}</td><td>{yr}</td><td>{cname}</td><td>{rname}</td><td>{badge}</td></tr>"
        return out

    def rows2_html():
        if not rows2:
            return '<tr><td colspan="4" class="no-data">No region data for the selected filters</td></tr>'
        out = ""
        for aid, yr, rname, cnt in rows2:
            out += f"<tr><td>{aid}</td><td>{yr}</td><td><strong>{cnt}</strong></td><td>{rname}</td></tr>"
        return out

    # ── Pagination ──
    def paginate(cur, total, key, total_cnt):
        shown = {1, total, cur}
        if cur > 1:     shown.add(cur - 1)
        if cur < total: shown.add(cur + 1)

        def purl(p): return url(**{key: str(p)})

        prev_btn = f'<a href="{purl(cur-1)}" class="page-btn">&lsaquo;</a>' if cur > 1 \
                   else '<span class="page-btn disabled">&lsaquo;</span>'
        next_btn = f'<a href="{purl(cur+1)}" class="page-btn">&rsaquo;</a>' if cur < total \
                   else '<span class="page-btn disabled">&rsaquo;</span>'

        mid = []
        last = 0
        for p in sorted(shown):
            if p - last > 1:
                mid.append('<span class="page-ellipsis">...</span>')
            if p == cur:
                mid.append(f'<span class="page-btn active">{p}</span>')
            else:
                mid.append(f'<a href="{purl(p)}" class="page-btn">{p}</a>')
            last = p

        start = (cur - 1) * ROWS_PER_PAGE + 1
        end   = min(cur * ROWS_PER_PAGE, total_cnt)
        return f"""<div class="pagination">
            <span class="pagination-info">Showing {start}&#8211;{end} of {total_cnt}</span>
            <div class="pagination-btns">{prev_btn}{"".join(mid)}{next_btn}</div>
        </div>"""

    # ── Sortable column header builders ──
    _SIMG = '<img src="/images/order%20icon.png" class="sort-icon-img" alt="">'

    def th1(label, asc_key, desc_key):
        is_asc  = sort_f == asc_key
        next_k  = desc_key if is_asc else asc_key
        cls     = " sort-asc" if is_asc else (" sort-desc" if sort_f == desc_key else "")
        return (f'<th class="sortable{cls}">'
                f'<a href="{url(sort=next_k, page1="1")}" class="sort-link">'
                f'{label} {_SIMG}</a></th>')

    def th2(label, asc_key, desc_key):
        is_asc  = sort2_f == asc_key
        next_k  = desc_key if is_asc else asc_key
        cls     = " sort-asc" if is_asc else (" sort-desc" if sort2_f == desc_key else "")
        return (f'<th class="sortable{cls}">'
                f'<a href="{url(sort2=next_k, page2="1")}" class="sort-link">'
                f'{label} {_SIMG}</a></th>')

    # ── CSS + nav ──
    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
    with open(css_file, 'r', encoding='utf-8') as f:
        css = f.read()

    nav_html    = nav.get_nav_html("/binh_page_2")
    footer_html = nav.get_footer_html()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>ImmuniData - Vaccination Data Explorer</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
</head>
<body>

{nav_html}

<div class="page-header">
    <h1>Vaccination Data Explorer</h1>
    <p>Explore vaccination rates and herd immunity levels by country and region</p>
</div>

<div class="filter-card">
    <form method="GET" action="/binh_page_2">
        <input type="hidden" name="sort2" value="{sort2_f}">
        <div class="filter-row">
            <div class="filter-group"><label>Antigen</label>{sel_antigen()}</div>
            <div class="filter-group"><label>Year</label>{sel_year()}</div>
            <div class="filter-group"><label>Region</label>{sel_region()}</div>
            <div class="filter-group"><label>Country</label>{sel_country()}</div>
            <div class="filter-group"><label>Sort by</label>{sel_sort()}</div>
            <div class="filter-actions">
                <button type="submit" class="btn-apply"><img src="/images/filter%20icon.png" alt=""> Apply Filters</button>
                <a href="/binh_page_2" class="btn-reset"><img src="/images/reset%20icon.png" alt=""> Reset</a>
            </div>
        </div>
    </form>
</div>

<div class="results-bar">
    <img src="/images/showing_result%20icon.png" class="results-icon" alt="">
    <span class="results-label">Showing result for:</span>
    {filter_tags}
    <span class="ready-badge">Ready</span>
    <span class="results-count">{n_ctr} countries found</span>
    <span class="results-sep">|</span>
    <span class="results-note">Last updated WHO dataset 2000&#8211;2024</span>
</div>

<div class="tables-row">

    <!-- Table 1: Countries meeting ≥90% target -->
    <div class="table-card">
        <input type="radio" id="t1-table" name="t1-view" checked class="tab-radio">
        <input type="radio" id="t1-chart" name="t1-view" class="tab-radio">
        <div class="tab-bar">
            <div class="tab-btn-group">
                <label for="t1-table" class="tab-btn t1-table-label"><img src="/images/table%20icon.png" alt=""> Table</label>
                <label for="t1-chart" class="tab-btn t1-chart-label"><img src="/images/chart%20icon.png" alt=""> Chart</label>
            </div>
        </div>
        <div class="t1-table-panel">
            <div class="table-header-row">
                <span class="table-title">Table 1: Countries Meeting &ge;90% Vaccination Target</span>
                <a href="{export1_href}" download="vaccination_table1.xls" class="export-btn"><img src="/images/export%20icon.png" alt=""> Export Data</a>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead><tr>
                        {th1("Antigen",           "antigen_asc",  "antigen_desc")}
                        {th1("Year",              "year_asc",     "year_desc")}
                        {th1("Country",           "country_asc",  "country_desc")}
                        {th1("Region",            "region_asc",   "region_desc")}
                        {th1("% of Target",       "coverage_asc", "coverage_desc")}
                    </tr></thead>
                    <tbody>{rows1_html()}</tbody>
                </table>
            </div>
            {paginate(page1, total_p1, "page1", cnt1)}
        </div>
        <div class="t1-chart-panel">
            <div class="chart-placeholder">&#9650; Chart view coming soon</div>
        </div>
    </div>

    <!-- Table 2: Countries meeting ≥90% per region -->
    <div class="table-card">
        <input type="radio" id="t2-table" name="t2-view" checked class="tab-radio">
        <input type="radio" id="t2-chart" name="t2-view" class="tab-radio">
        <div class="tab-bar">
            <div class="tab-btn-group">
                <label for="t2-table" class="tab-btn t2-table-label"><img src="/images/table%20icon.png" alt=""> Table</label>
                <label for="t2-chart" class="tab-btn t2-chart-label"><img src="/images/chart%20icon.png" alt=""> Chart</label>
            </div>
        </div>
        <div class="t2-table-panel">
            <div class="table-header-row">
                <span class="table-title">Table 2: Region Summary</span>
                <a href="{export2_href}" download="vaccination_table2.xls" class="export-btn"><img src="/images/export%20icon.png" alt=""> Export Data</a>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead><tr>
                        {th2("Antigen",            "antigen2_asc",   "antigen2_desc")}
                        {th2("Year",               "year2_asc",      "year2_desc")}
                        {th2("Countries met ≥90%", "countries_asc", "countries_desc")}
                        {th2("Region",             "region2_asc",    "region2_desc")}
                    </tr></thead>
                    <tbody>{rows2_html()}</tbody>
                </table>
            </div>
            {paginate(page2, total_p2, "page2", cnt2)}
        </div>
        <div class="t2-chart-panel">
            <div class="chart-placeholder">&#9650; Chart view coming soon</div>
        </div>
    </div>

</div>

<div class="info-note">
    <img src="/images/iconinfo.png" class="info-icon-img" alt="">
    <span>Note: Both tables update automatically when you click &#8220;Apply Filters&#8221;. Use &#8220;Reset&#8221; to clear all selections. Duplicate records are averaged automatically.</span>
</div>

{footer_html}

</body>
</html>"""
