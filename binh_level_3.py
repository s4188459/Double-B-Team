import os
import sqlite3
import urllib.parse
import pyhtml
import nav
import translations as tr

ROWS_PER_PAGE = 10
SAVED_VIEWS_TABLE = "BinhLevel3SavedViews"


def _html(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


# basic SQL escaping to prevent injection in filter queries
def _esc(s):
    return str(s).replace("'", "''")


# CSS class for coverage badge coloring
def _cov_class(v):
    if v is None: return "cov-mid"
    return "cov-high" if v >= 90 else ("cov-mid" if v >= 70 else "cov-low")

# CSS class for the improvement delta badge: green positive, red negative, gray zero
def _delta_class(v):
    if v is None: return "delta-zero"
    if v > 0:  return "delta-pos"
    if v < 0:  return "delta-neg"
    return "delta-zero"


def _load_saved_views(db):
    with sqlite3.connect(db) as conn:
        rows = conn.execute(f"""
            SELECT id, label, antigen, start_year, end_year, top
            FROM {SAVED_VIEWS_TABLE}
            ORDER BY id DESC
        """).fetchall()
    return [
        {"id": str(r[0]), "label": r[1], "antigen": r[2],
         "start_year": r[3], "end_year": r[4], "top": r[5]}
        for r in rows
    ]


def _add_saved_view(db, view):
    with sqlite3.connect(db) as conn:
        cur = conn.execute(f"""
            INSERT OR IGNORE INTO {SAVED_VIEWS_TABLE} (label, antigen, start_year, end_year, top)
            VALUES (?, ?, ?, ?, ?)
        """, (view["label"], view["antigen"],
               view["start_year"], view["end_year"], view.get("top", "10")))
        return cur.rowcount > 0


def _delete_saved_view(db, view_id):
    with sqlite3.connect(db) as conn:
        conn.execute(f"DELETE FROM {SAVED_VIEWS_TABLE} WHERE id = ?", (view_id,))


def get_page_html(form_data):
    def _get(key, default=""):
        v = form_data.get(key)
        return (v[0] if v else default).strip()

    lang = _get("lang", "en")
    tr_ = lambda k: tr.get_translation(k, lang)
    lang_param = f'<input type="hidden" name="lang" value="{lang}">' if lang != "en" else ""
    reset_href = f"/binh_page_3{'?lang=' + lang if lang != 'en' else ''}"

    antigen_f    = _get("antigen")
    start_year_f = _get("start_year", "2000")
    end_year_f   = _get("end_year",   "2024")
    top_f        = _get("top",        "10")
    sort_f       = _get("sort",       "increase_desc")
    t3_view_f    = _get("t3_view",    "table")

    # applied_* values only update when user clicks Apply Filters
    applied_antigen_f    = _get("applied_antigen")
    applied_start_year_f = _get("applied_start_year", "2000")
    applied_end_year_f   = _get("applied_end_year",   "2024")
    applied_top_f        = _get("applied_top",        "10")

    try: page = max(1, int(_get("page", "1")))
    except: page = 1

    db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'immunisation.db')

    saved_message = ""
    saved_views = _load_saved_views(db)
    delete_view_f = _get("delete_view")
    if delete_view_f.isdigit():
        _delete_saved_view(db, delete_view_f)
        saved_views = _load_saved_views(db)
        saved_message = '<span class="saved-message">Deleted</span>'

    antigen_opts = pyhtml.get_results_from_query(db,
        "SELECT AntigenID, name FROM Antigen ORDER BY AntigenID")
    year_opts = pyhtml.get_results_from_query(db,
        "SELECT DISTINCT year FROM Vaccination ORDER BY year DESC")
    db_min_year = str(year_opts[-1][0]) if year_opts else "2000"
    db_max_year = str(year_opts[0][0]) if year_opts else "2024"

    try: start_y = int(start_year_f)
    except: start_y = 2000
    try: end_y = int(end_year_f)
    except: end_y = 2024
    # swap if someone manually typed end < start in the URL
    if end_y < start_y:
        start_y, end_y = end_y, start_y

    # each year dropdown only shows values valid relative to the other — prevents impossible ranges
    start_year_opts = [(yr,) for (yr,) in year_opts if int(yr) <= end_y]
    end_year_opts   = [(yr,) for (yr,) in year_opts if int(yr) >= start_y]

    TOP_OPTS = [("5","Top 5"), ("10","Top 10"), ("20","Top 20"), ("50","Top 50"), ("100","Top 100")]
    TOP_MAP  = {v: int(v) for v, _ in TOP_OPTS}
    top_n    = TOP_MAP.get(top_f, 10)

    try: applied_start_y = int(applied_start_year_f)
    except: applied_start_y = 2000
    try: applied_end_y = int(applied_end_year_f)
    except: applied_end_y = 2024
    if applied_end_y < applied_start_y:
        applied_start_y, applied_end_y = applied_end_y, applied_start_y
    applied_top_n = TOP_MAP.get(applied_top_f, 10)

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
        "increase_desc": tr_("sort_increase_hl"),
        "increase_asc":  tr_("sort_increase_lh"),
        "country_asc":   tr_("sort_country_az"),
        "country_desc":  tr_("sort_country_za"),
        "region_asc":    tr_("sort_region_az"),
        "region_desc":   tr_("sort_region_za"),
        "start_desc":    tr_("sort_start_rate_hl"),
        "start_asc":     tr_("sort_start_rate_lh"),
        "end_desc":      tr_("sort_end_rate_hl"),
        "end_asc":       tr_("sort_end_rate_lh"),
    }
    order_expr = SORT_MAP.get(sort_f, "(e.coverage - s.coverage) DESC")

    # table and chart only activate when a specific antigen has been applied
    table_active    = bool(applied_antigen_f)
    antigen_display = applied_antigen_f

    def inactive_msg():
        return f'<div class="chart-msg">{tr_("inactive_msg_vacc3")}</div>'

    a_cond = f"AND antigen = '{_esc(applied_antigen_f)}'" if applied_antigen_f else ""

    # builds a subquery for a single year: rate = doses / population × 100
    # AVG + GROUP BY prevents cross-product duplicates when no antigen filter is set
    # typeof='real' skips rows where doses is stored as '' instead of NULL
    def _sub(yr):
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
        JOIN {_sub(applied_start_y)} s ON c.CountryID = s.country
        JOIN {_sub(applied_end_y)}   e ON c.CountryID = e.country"""

    select_cols = """
        c.name                                      AS country_name,
        r.region                                    AS region_name,
        ROUND(s.coverage, 2)                        AS start_rate,
        ROUND(e.coverage, 2)                        AS end_rate,
        ROUND(e.coverage - s.coverage, 2)           AS increase"""

    if table_active:
        # total count for the results bar — no Top N limit here
        n_total = pyhtml.get_results_from_query(db,
            f"SELECT COUNT(*) {join_sql}")[0][0]
        # sorted and limited to Top N in SQL — no Python post-processing
        top_rows = pyhtml.get_results_from_query(db, f"""
            SELECT {select_cols}
            {join_sql}
            ORDER BY {order_expr}
            LIMIT {applied_top_n}""")
    else:
        n_total  = 0
        top_rows = []

    # paginate within the already-limited top_rows slice
    cnt         = len(top_rows)
    total_pages = max(1, -(-cnt // ROWS_PER_PAGE))
    page        = min(page, total_pages)
    rows        = top_rows[(page-1)*ROWS_PER_PAGE : page*ROWS_PER_PAGE]

    # URL builder — carries all current params forward, overriding with kw
    def url(**kw):
        p = {}
        if antigen_f:        p["antigen"]         = antigen_f
        p["start_year"]  = str(start_y)
        p["end_year"]    = str(end_y)
        if top_f != "10":    p["top"]             = top_f
        if sort_f != "increase_desc": p["sort"]   = sort_f
        if t3_view_f == "chart": p["t3_view"]     = t3_view_f
        if applied_antigen_f:    p["applied_antigen"]    = applied_antigen_f
        p["applied_start_year"] = str(applied_start_y)
        p["applied_end_year"]   = str(applied_end_y)
        if applied_top_f != "10": p["applied_top"] = applied_top_f
        p["page"] = str(page)
        if lang != "en":
            p["lang"] = lang
        p.update(kw)
        qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in p.items() if v)
        return f"/binh_page_3?{qs}#results-section" if qs else "/binh_page_3#results-section"

    # thin wrapper so year dropdown links preserve antigen/top/sort state
    def cascade_year_url(start_year, end_year):
        return url(start_year=str(start_year), end_year=str(end_year), page="1")

    def apply_url(antigen, start_year, end_year, top="10"):
        p = {
            "antigen": antigen, "start_year": start_year, "end_year": end_year, "top": top,
            "applied_antigen": antigen, "applied_start_year": start_year,
            "applied_end_year": end_year, "applied_top": top,
        }
        if lang != "en":
            p["lang"] = lang
        return f"/binh_page_3?{urllib.parse.urlencode(p)}#results-section"

    if _get("save_view") == "1" and table_active:
        view_name = _get("view_name")
        label = view_name if view_name else f"{antigen_display}, {applied_start_y} to {applied_end_y}, Top {applied_top_n}"
        new_view = {
            "label": label,
            "antigen": applied_antigen_f,
            "start_year": str(applied_start_y),
            "end_year": str(applied_end_y),
            "top": applied_top_f,
        }
        if _add_saved_view(db, new_view):
            saved_views = _load_saved_views(db)
            saved_message = f'<span class="saved-message">{tr_("saved_msg")}</span>'
        else:
            saved_message = f'<span class="saved-message">{tr_("already_saved_msg")}</span>'

    if saved_views:
        saved_parts = []
        for v in saved_views:
            if not (v.get("antigen") and v.get("start_year") and v.get("end_year")): continue
            link = apply_url(v["antigen"], v["start_year"], v["end_year"], v.get("top", "10"))
            del_href = f'/binh_page_3?delete_view={v["id"]}{("&lang=" + lang) if lang != "en" else ""}'
            saved_parts.append(
                f'<div class="saved-view-item">'
                f'<a class="saved-pill" href="{link}">{_html(v.get("label", ""))}</a>'
                f'<a class="saved-action" href="{del_href}">{tr_("delete")}</a>'
                f'</div>'
            )
        saved_html = "".join(saved_parts)
    else:
        starter_views = [
            ("BCG, 2000 to 2024, Top 10",  apply_url("BCG",  "2000", "2024", "10")),
            ("DTP3, 2010 to 2024, Top 10", apply_url("DTP3", "2010", "2024", "10")),
            ("MCV1, 2000 to 2024, Top 20", apply_url("MCV1", "2000", "2024", "20")),
        ]
        saved_html = "".join(f'<a class="saved-pill starter" href="{href}">{_html(label)}</a>' for label, href in starter_views)
        saved_html += f'<span class="empty-saved-note">{tr_("starter_note")}</span>'

    filter_tags = ""
    if applied_antigen_f:
        filter_tags += f'<span class="filter-tag">{applied_antigen_f}</span> '
    filter_tags += f'<span class="filter-tag">{applied_start_y} → {applied_end_y}</span> '
    filter_tags += f'<span class="filter-tag">Top {applied_top_n}</span> '

    def sel_antigen():
        label = antigen_f if antigen_f else tr_("select_antigen")
        opts = f'<a href="{url(antigen="", page="1")}" class="{"selected" if not antigen_f else ""}">{tr_("all_antigens")}</a>'
        for aid, _ in antigen_opts:
            sc = "selected" if aid == antigen_f else ""
            opts += f'<a href="{url(antigen=aid, page="1")}" class="{sc}">{aid}</a>'
        return (f'<div class="custom-select css-dropdown">'
                f'<input type="checkbox" id="dd-antigen" class="dd-toggle">'
                f'<label for="dd-antigen" class="dd-backdrop"></label>'
                f'<label for="dd-antigen" class="custom-select-btn">{label}</label>'
                f'<div class="custom-select-options">{opts}</div></div>')

    def sel_start_year():
        opts = ""
        for (yr,) in start_year_opts:
            sc = "selected" if int(yr) == start_y else ""
            opts += f'<a href="{cascade_year_url(yr, end_y)}" class="{sc}">{yr}</a>'
        return (f'<div class="custom-select css-dropdown">'
                f'<input type="checkbox" id="dd-start" class="dd-toggle">'
                f'<label for="dd-start" class="dd-backdrop"></label>'
                f'<label for="dd-start" class="custom-select-btn">{start_y}</label>'
                f'<div class="custom-select-options">{opts}</div>'
                f'</div>')

    def sel_end_year():
        opts = ""
        for (yr,) in end_year_opts:
            sc = "selected" if int(yr) == end_y else ""
            opts += f'<a href="{cascade_year_url(start_y, yr)}" class="{sc}">{yr}</a>'
        return (f'<div class="custom-select css-dropdown">'
                f'<input type="checkbox" id="dd-end" class="dd-toggle">'
                f'<label for="dd-end" class="dd-backdrop"></label>'
                f'<label for="dd-end" class="custom-select-btn">{end_y}</label>'
                f'<div class="custom-select-options">{opts}</div>'
                f'</div>')

    def sel_top():
        cur_label = next((lbl for val, lbl in TOP_OPTS if val == top_f), "Top 10")
        opts = ""
        for val, lbl in TOP_OPTS:
            sc = "selected" if val == top_f else ""
            opts += f'<a href="{url(top=val, page="1")}" class="{sc}">{lbl}</a>'
        return (f'<div class="custom-select css-dropdown">'
                f'<input type="checkbox" id="dd-top" class="dd-toggle">'
                f'<label for="dd-top" class="dd-backdrop"></label>'
                f'<label for="dd-top" class="custom-select-btn">{cur_label}</label>'
                f'<div class="custom-select-options">{opts}</div></div>')

    def sel_sort():
        cur_label = SORT_LABELS.get(sort_f, "Highest Increase")
        opts = ""
        for val, lbl in SORT_LABELS.items():
            sc = "selected" if val == sort_f else ""
            opts += f'<a href="{url(sort=val, page="1")}" class="{sc}">{lbl}</a>'
        return (f'<div class="custom-select css-dropdown">'
                f'<input type="checkbox" id="dd-sort" class="dd-toggle">'
                f'<label for="dd-sort" class="dd-backdrop"></label>'
                f'<label for="dd-sort" class="custom-select-btn">{cur_label}</label>'
                f'<div class="custom-select-options">{opts}</div></div>')

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

    # renders prev/next + numbered page links with ellipsis for large page counts
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

    _SIMG = '<img src="/images/order%20icon.png" class="sort-icon-img" alt="">'

    # sortable column header — toggles asc/desc and links back with the new sort key
    def th(label, asc_key, desc_key):
        is_asc = sort_f == asc_key
        next_k = desc_key if is_asc else asc_key
        cls    = " sort-asc" if is_asc else (" sort-desc" if sort_f == desc_key else "")
        return (f'<th class="sortable{cls}">'
                f'<a href="{url(sort=next_k, page="1")}" class="sort-link">'
                f'{label} {_SIMG}</a></th>')

    # exports all top_rows (not just the current page) as an Excel-compatible data: URI
    def _xls_export():
        def esc(v):
            s = str(v if v is not None else "")
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        headers = ["Rank", "Country", "Region",
                   f"Coverage {applied_start_y} (%)", f"Coverage {applied_end_y} (%)", "Increase (%)"]
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

    # horizontal bar chart — green for improvement, red for decline, scrollable when Top ≥ 20
    def chart3_html():
        title_text = (f"TOP {applied_top_n} COUNTRIES BY VACCINATION RATE INCREASE of {antigen_display} FROM {applied_start_y} TO {applied_end_y}"
                      if table_active else "TOP COUNTRIES BY VACCINATION RATE INCREASE")
        title = f'<div class="table-header-row"><span class="table-title">{title_text}</span></div>'
        if not table_active:
            return title + inactive_msg()
        if len(top_rows) < 2:
            return title + '<div class="chart-msg">Not enough data — need at least 2 countries to display a chart</div>'
        sorted_rows = sorted(top_rows, key=lambda r: r[4] if r[4] is not None else 0, reverse=True)
        max_abs = max(abs(r[4] or 0) for r in sorted_rows) or 1
        out = ""
        for i, (cname, rname, start_r, end_r, delta) in enumerate(sorted_rows):
            d = delta or 0
            w = round(abs(d) / max_abs * 100, 1)
            if d > 0:
                fill_cls, sign = "bar-fill-green", "+"
            elif d < 0:
                fill_cls, sign = "bar-fill-red", ""
            else:
                fill_cls, sign = "bar-fill-gray", ""
            out += (f'<div class="bar-row">'
                    f'<span class="bar-rank">{i+1}</span>'
                    f'<span class="bar-label" title="{cname}">{cname}</span>'
                    f'<div class="bar-track"><div class="{fill_cls}" style="width:{w}%"></div></div>'
                    f'<span class="bar-val">{sign}{d}%</span>'
                    f'</div>')
        inner = f'<div class="bar-chart-h">{out}</div>'
        if applied_top_n >= 20:
            inner = f'<div class="bar-chart-scroll">{inner}</div>'
        return title + inner

    if table_active:
        t3_panel_content = f"""
            <div class="table-header-row">
                <span class="table-title">TOP {applied_top_n} COUNTRIES BY VACCINATION RATE INCREASE of {antigen_display} FROM {applied_start_y} TO {applied_end_y}</span>
                <a href="{export_href}" download="vaccination_improvement.xls" class="export-btn">
                    <img src="/images/export%20icon.png" alt=""> Export Data
                </a>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead><tr>
                        <th>Rank</th>
                        {th("Country",                                  "country_asc",  "country_desc")}
                        {th("Region",                                   "region_asc",   "region_desc")}
                        {th(f"Vaccination Rate In {applied_start_y}",   "start_asc",    "start_desc")}
                        {th(f"Vaccination Rate In {applied_end_y}",     "end_asc",      "end_desc")}
                        {th("Vaccination Rate Increase",                "increase_asc", "increase_desc")}
                    </tr></thead>
                    <tbody>{rows_html()}</tbody>
                </table>
            </div>
            {paginate()}"""
    else:
        t3_panel_content = inactive_msg()

    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
    with open(css_file, 'r', encoding='utf-8') as f:
        css = f.read()

    nav_html    = nav.get_nav_html("/binh_page_3", lang=lang, form_data=form_data)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <title>ImmuniData - {tr_("page_vacc_improvement")}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
</head>
<body>

{nav_html}

<div class="page-header">
    <h1>{tr_("page_vacc_improvement")}</h1>
    <p>{tr_("page_vacc_improvement_sub")}</p>
</div>

<div class="filter-card">
    <div class="filter-row">

        <!-- All dropdowns use instant navigation — selecting any option reloads immediately -->
        <div class="filter-group"><label>{tr_("filter_start_year")}</label>{sel_start_year()}</div>
        <div class="filter-group"><label>{tr_("filter_end_year")}</label>{sel_end_year()}</div>
        <div class="filter-group"><label>{tr_("filter_antigen")}</label>{sel_antigen()}</div>
        <div class="filter-group"><label>{tr_("filter_top")}</label>{sel_top()}</div>
        <div class="filter-group"><label>{tr_("filter_sort")}</label>{sel_sort()}</div>

        <!-- Apply Filters: hidden fields preserve current params when submitted -->
        <form method="GET" action="/binh_page_3" class="form-contents">
            <input type="hidden" name="antigen"             value="{antigen_f}">
            <input type="hidden" name="start_year"          value="{start_y}">
            <input type="hidden" name="end_year"            value="{end_y}">
            <input type="hidden" name="top"                 value="{top_f}">
            <input type="hidden" name="sort"                value="{sort_f}">
            <input type="hidden" name="t3_view"             value="{t3_view_f}">
            <input type="hidden" name="applied_antigen"     value="{antigen_f}">
            <input type="hidden" name="applied_start_year"  value="{start_y}">
            <input type="hidden" name="applied_end_year"    value="{end_y}">
            <input type="hidden" name="applied_top"         value="{top_f}">
            {lang_param}
            <div class="filter-actions">
                <button type="submit" class="btn-apply">
                    <img src="/images/filter%20icon.png" alt=""> {tr_("btn_apply")}
                </button>
                <a href="{reset_href}" class="btn-reset">
                    <img src="/images/reset%20icon.png" alt=""> {tr_("btn_reset")}
                </a>
            </div>
        </form>

    </div>
</div>

<div class="results-bar" id="results-section">
    <img src="/images/showing_result%20icon.png" class="results-icon" alt="">
    <span class="results-label">{tr_("showing_result")}</span>
    {filter_tags}
    <span class="ready-badge">Ready</span>
    <span class="results-count">{n_total} {tr_("countries_both_years")}</span>
    <span class="results-sep">|</span>
    <span class="results-note">{tr_("last_updated")} {db_min_year}&#8211;{db_max_year}</span>
</div>

<div class="saved-card">
    <span class="saved-label">{tr_("saved_views")}</span>
    {saved_html}
    <form method="GET" action="/binh_page_3" class="save-view-form">
        <input type="hidden" name="antigen"              value="{_html(antigen_f)}">
        <input type="hidden" name="start_year"           value="{start_y}">
        <input type="hidden" name="end_year"             value="{end_y}">
        <input type="hidden" name="top"                  value="{_html(top_f)}">
        <input type="hidden" name="sort"                 value="{_html(sort_f)}">
        <input type="hidden" name="t3_view"              value="{_html(t3_view_f)}">
        <input type="hidden" name="applied_antigen"      value="{_html(applied_antigen_f)}">
        <input type="hidden" name="applied_start_year"   value="{applied_start_y}">
        <input type="hidden" name="applied_end_year"     value="{applied_end_y}">
        <input type="hidden" name="applied_top"          value="{_html(applied_top_f)}">
        <input type="hidden" name="save_view"            value="1">
        {lang_param}
        <input type="text"   name="view_name"            class="save-view-input" placeholder="{tr_("save_placeholder")}">
        <button type="submit" class="save-view-btn">{tr_("save_view_btn")}</button>
        {saved_message}
    </form>
</div>

<div class="single-table-wrap">
    <div class="table-card">
        <input type="radio" id="t3-table" name="t3-view" {'checked' if t3_view_f != 'chart' else ''} class="tab-radio">
        <input type="radio" id="t3-chart" name="t3-view" {'checked' if t3_view_f == 'chart' else ''} class="tab-radio">
        <div class="tab-bar">
            <div class="tab-btn-group">
                <a href="{url(t3_view='table')}" class="tab-btn t3-table-label">
                    <img src="/images/table%20icon.png" alt=""> {tr_("tab_table")}
                </a>
                <a href="{url(t3_view='chart')}" class="tab-btn t3-chart-label">
                    <img src="/images/chart%20icon.png" alt=""> {tr_("tab_chart")}
                </a>
            </div>
        </div>

        <div class="t3-table-panel">
            {t3_panel_content}
        </div>

        <div class="t3-chart-panel">
            {chart3_html()}
        </div>
    </div>
</div>

<div class="info-note">
    <img src="/images/iconinfo.png" class="info-icon-img" alt="">
    <span>{tr_("info_note_vacc3_pre")} <strong>{tr_("info_note_vacc3_both")}</strong>
    {applied_start_y} {tr_("inactive_and")} {applied_end_y} {tr_("info_note_vacc3_post")}
    <strong>{tr_("info_note_vacc3_formula")}</strong>.
    {tr_("info_note_vacc3_increase")}</span>
</div>

<div class="how-card">
    <div class="how-copy">
        <img src="/images/iconinfo.png" class="info-icon-img" alt="">
        <div class="how-text">
            <span class="how-title">{tr_("how_works_title")}</span>
            <p>{tr_("how_desc_vacc3")}</p>
        </div>
    </div>
    <div class="how-links">
        <span class="how-hover">
            <a href="#" class="how-link">{tr_("how_view_methodology")} -&gt;</a>
            <span class="how-hover-panel">{tr_("how_popup_vacc3")}</span>
        </span>
        <a href="#" class="how-link">{tr_("how_data_dict")} -&gt;</a>
    </div>
</div>

{nav.get_footer_html(lang)}

</body>
</html>"""
