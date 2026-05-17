import os
import sqlite3
import urllib.parse

import nav
import pyhtml


ROWS_PER_PAGE = 10
SAVED_VIEWS_TABLE = "BaoLevel3SavedViews"


def _html(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _esc(value):
    return str(value).replace("'", "''")


def _delta_class(value):
    if value is None:
        return "delta-zero"
    if value > 0:
        return "delta-pos"
    if value < 0:
        return "delta-neg"
    return "delta-zero"


def _rate_class(rate):
    try:
        rate = float(rate)
    except (TypeError, ValueError):
        return "cov-mid"
    if rate >= 100:
        return "cov-low"
    if rate >= 10:
        return "cov-mid"
    return "cov-high"


def _load_saved_views(db):
    with sqlite3.connect(db) as conn:
        rows = conn.execute(f"""
            SELECT id, label, inf_type, economy, start_year, end_year, top
            FROM {SAVED_VIEWS_TABLE}
            ORDER BY id DESC
        """).fetchall()
    return [
        {"id": str(r[0]), "label": r[1], "inf_type": r[2],
         "economy": r[3], "start_year": r[4], "end_year": r[5], "top": r[6]}
        for r in rows
    ]


def _add_saved_view(db, view):
    with sqlite3.connect(db) as conn:
        cur = conn.execute(f"""
            INSERT OR IGNORE INTO {SAVED_VIEWS_TABLE} (label, inf_type, economy, start_year, end_year, top)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (view["label"], view["inf_type"], view["economy"],
               view["start_year"], view["end_year"], view.get("top", "10")))
        return cur.rowcount > 0


def _delete_saved_view(db, view_id):
    with sqlite3.connect(db) as conn:
        conn.execute(f"DELETE FROM {SAVED_VIEWS_TABLE} WHERE id = ?", (view_id,))


def get_page_html(form_data):
    def _get(key, default=""):
        v = form_data.get(key)
        return (v[0] if v else default).strip()

    db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "immunisation.db")

    saved_message = ""
    saved_views = _load_saved_views(db)
    delete_view_f = _get("delete_view")
    if delete_view_f.isdigit():
        _delete_saved_view(db, delete_view_f)
        saved_views = _load_saved_views(db)
        saved_message = '<span class="saved-message">Deleted</span>'

    inf_opts = pyhtml.get_results_from_query(db, "SELECT id, description FROM Infection_Type ORDER BY description")
    economy_opts = pyhtml.get_results_from_query(db, "SELECT economyID, phase FROM Economy ORDER BY economyID")
    year_opts = pyhtml.get_results_from_query(db, "SELECT DISTINCT year FROM InfectionData ORDER BY year DESC")
    db_min_year = str(year_opts[-1][0]) if year_opts else "2000"
    db_max_year = str(year_opts[0][0]) if year_opts else "2024"

    default_inf = inf_opts[0][0] if inf_opts else ""
    default_economy = str(economy_opts[2][0]) if len(economy_opts) >= 3 else (str(economy_opts[0][0]) if economy_opts else "")
    default_start_year = "2000" if any(str(y[0]) == "2000" for y in year_opts) else (str(year_opts[-1][0]) if year_opts else "")
    default_end_year = "2024" if any(str(y[0]) == "2024" for y in year_opts) else (str(year_opts[0][0]) if year_opts else "")

    inf_f = _get("inf_type", default_inf)
    economy_f = _get("economy", default_economy)
    start_year_f = _get("start_year", default_start_year)
    end_year_f = _get("end_year", default_end_year)
    top_f = _get("top", "10")
    sort_f = _get("sort", "improvement_desc")
    t3_view_f = _get("t3_view", "table")

    applied_inf_f = _get("applied_inf_type", inf_f)
    applied_economy_f = _get("applied_economy", economy_f)
    applied_start_year_f = _get("applied_start_year", start_year_f)
    applied_end_year_f = _get("applied_end_year", end_year_f)
    applied_top_f = _get("applied_top", top_f)

    try:
        page = max(1, int(_get("page", "1")))
    except ValueError:
        page = 1

    try:
        start_y = int(start_year_f)
    except ValueError:
        start_y = int(default_start_year or 2000)
    try:
        end_y = int(end_year_f)
    except ValueError:
        end_y = int(default_end_year or 2024)
    if end_y < start_y:
        start_y, end_y = end_y, start_y

    try:
        applied_start_y = int(applied_start_year_f)
    except ValueError:
        applied_start_y = start_y
    try:
        applied_end_y = int(applied_end_year_f)
    except ValueError:
        applied_end_y = end_y
    if applied_end_y < applied_start_y:
        applied_start_y, applied_end_y = applied_end_y, applied_start_y

    start_year_opts = [(yr,) for (yr,) in year_opts if int(yr) <= end_y]
    end_year_opts = [(yr,) for (yr,) in year_opts if int(yr) >= start_y]

    TOP_OPTS = [("5", "Top 5"), ("10", "Top 10"), ("20", "Top 20"), ("50", "Top 50"), ("100", "Top 100")]
    TOP_MAP = {v: int(v) for v, _ in TOP_OPTS}
    applied_top_n = TOP_MAP.get(applied_top_f, 10)

    SORT_LABELS = {
        "improvement_desc": "Biggest Improvement",
        "improvement_asc": "Smallest Improvement",
        "country_asc": "Country (A to Z)",
        "country_desc": "Country (Z to A)",
        "start_rate_desc": "Start Rate (High to Low)",
        "start_rate_asc": "Start Rate (Low to High)",
        "end_rate_desc": "End Rate (High to Low)",
        "end_rate_asc": "End Rate (Low to High)",
        "start_cases_desc": "Start Cases (High to Low)",
        "start_cases_asc": "Start Cases (Low to High)",
        "end_cases_desc": "End Cases (High to Low)",
        "end_cases_asc": "End Cases (Low to High)",
    }
    SORT_MAP = {
        "improvement_desc": "improvement DESC",
        "improvement_asc": "improvement ASC",
        "country_asc": "country_name ASC",
        "country_desc": "country_name DESC",
        "start_rate_desc": "start_rate DESC",
        "start_rate_asc": "start_rate ASC",
        "end_rate_desc": "end_rate DESC",
        "end_rate_asc": "end_rate ASC",
        "start_cases_desc": "start_cases DESC",
        "start_cases_asc": "start_cases ASC",
        "end_cases_desc": "end_cases DESC",
        "end_cases_asc": "end_cases ASC",
    }
    order_by = SORT_MAP.get(sort_f, "improvement DESC")

    table_active = bool(
        applied_inf_f
        and applied_economy_f.isdigit()
        and str(applied_start_y).isdigit()
        and str(applied_end_y).isdigit()
    )

    disease_display = next((desc for iid, desc in inf_opts if iid == applied_inf_f), applied_inf_f)
    economy_display = next((phase for eid, phase in economy_opts if str(eid) == str(applied_economy_f)), applied_economy_f)

    def _year_sub(year):
        return f"""(
            SELECT i.country,
                   ROUND(i.cases, 0) AS cases,
                   ROUND(i.cases / p.population * 100000, 2) AS rate_per_100k
            FROM InfectionData i
            JOIN CountryPopulation p ON i.country = p.country AND i.year = p.year
            WHERE i.inf_type = '{_esc(applied_inf_f)}'
              AND i.year = {int(year)}
              AND typeof(i.cases) = 'real'
              AND typeof(p.population) = 'real'
              AND p.population > 0
        )"""

    rows_all = []
    n_total = 0
    if table_active:
        inner = f"""
            SELECT c.name AS country_name,
                   e.phase AS economy_phase,
                   s.cases AS start_cases,
                   t.cases AS end_cases,
                   s.rate_per_100k AS start_rate,
                   t.rate_per_100k AS end_rate,
                   ROUND(s.rate_per_100k - t.rate_per_100k, 2) AS improvement,
                   ROUND(s.cases - t.cases, 0) AS case_reduction
            FROM Country c
            JOIN Economy e ON c.economy = e.economyID
            JOIN {_year_sub(applied_start_y)} s ON c.CountryID = s.country
            JOIN {_year_sub(applied_end_y)} t ON c.CountryID = t.country
            WHERE c.economy = {int(applied_economy_f)}
        """
        n_total = pyhtml.get_results_from_query(db, f"SELECT COUNT(*) FROM ({inner})")[0][0]
        rows_all = pyhtml.get_results_from_query(db, f"""
            SELECT *
            FROM ({inner})
            ORDER BY {order_by}
            LIMIT {applied_top_n}
        """)

    cnt = len(rows_all)
    total_pages = max(1, -(-cnt // ROWS_PER_PAGE))
    page = min(page, total_pages)
    rows = rows_all[(page - 1) * ROWS_PER_PAGE : page * ROWS_PER_PAGE]

    def url(**kw):
        p = {}
        if inf_f:
            p["inf_type"] = inf_f
        if economy_f:
            p["economy"] = economy_f
        p["start_year"] = str(start_y)
        p["end_year"] = str(end_y)
        if top_f != "10":
            p["top"] = top_f
        if sort_f != "improvement_desc":
            p["sort"] = sort_f
        if t3_view_f == "chart":
            p["t3_view"] = t3_view_f
        if applied_inf_f:
            p["applied_inf_type"] = applied_inf_f
        if applied_economy_f:
            p["applied_economy"] = applied_economy_f
        p["applied_start_year"] = str(applied_start_y)
        p["applied_end_year"] = str(applied_end_y)
        if applied_top_f != "10":
            p["applied_top"] = applied_top_f
        p["page"] = str(page)
        p.update(kw)
        qs = urllib.parse.urlencode({k: str(v) for k, v in p.items() if v != ""})
        return f"/bao_page_3?{qs}#results-section" if qs else "/bao_page_3#results-section"

    def apply_url(inf_type, economy, start_year, end_year, top):
        qs = urllib.parse.urlencode({
            "inf_type": inf_type,
            "economy": economy,
            "start_year": start_year,
            "end_year": end_year,
            "top": top,
            "applied_inf_type": inf_type,
            "applied_economy": economy,
            "applied_start_year": start_year,
            "applied_end_year": end_year,
            "applied_top": top,
        })
        return f"/bao_page_3?{qs}#results-section"

    def cascade_year_url(start_year, end_year):
        return url(start_year=str(start_year), end_year=str(end_year), page="1")

    def sel_inf():
        label = next((desc for iid, desc in inf_opts if iid == inf_f), "Select infection")
        opts = ""
        for iid, desc in inf_opts:
            sc = "selected" if iid == inf_f else ""
            opts += f'<a href="{url(inf_type=iid, page="1")}" class="{sc}">{_html(desc)}</a>'
        return (
            f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-inf" class="dd-toggle">'
            f'<label for="dd-inf" class="dd-backdrop"></label><label for="dd-inf" class="custom-select-btn">{_html(label)}</label>'
            f'<div class="custom-select-options">{opts}</div></div>'
        )

    def sel_economy():
        label = next((phase for eid, phase in economy_opts if str(eid) == str(economy_f)), "Select economic status")
        opts = ""
        for eid, phase in economy_opts:
            sc = "selected" if str(eid) == str(economy_f) else ""
            opts += f'<a href="{url(economy=str(eid), page="1")}" class="{sc}">{_html(phase)}</a>'
        return (
            f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-economy" class="dd-toggle">'
            f'<label for="dd-economy" class="dd-backdrop"></label><label for="dd-economy" class="custom-select-btn">{_html(label)}</label>'
            f'<div class="custom-select-options">{opts}</div></div>'
        )

    def sel_start_year():
        opts = ""
        for (yr,) in start_year_opts:
            sc = "selected" if int(yr) == start_y else ""
            opts += f'<a href="{cascade_year_url(yr, end_y)}" class="{sc}">{yr}</a>'
        return (
            f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-start" class="dd-toggle">'
            f'<label for="dd-start" class="dd-backdrop"></label><label for="dd-start" class="custom-select-btn">{start_y}</label>'
            f'<div class="custom-select-options">{opts}</div></div>'
        )

    def sel_end_year():
        opts = ""
        for (yr,) in end_year_opts:
            sc = "selected" if int(yr) == end_y else ""
            opts += f'<a href="{cascade_year_url(start_y, yr)}" class="{sc}">{yr}</a>'
        return (
            f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-end" class="dd-toggle">'
            f'<label for="dd-end" class="dd-backdrop"></label><label for="dd-end" class="custom-select-btn">{end_y}</label>'
            f'<div class="custom-select-options">{opts}</div></div>'
        )

    def sel_top():
        label = next((lbl for val, lbl in TOP_OPTS if val == top_f), "Top 10")
        opts = ""
        for val, lbl in TOP_OPTS:
            sc = "selected" if val == top_f else ""
            opts += f'<a href="{url(top=val, page="1")}" class="{sc}">{_html(lbl)}</a>'
        return (
            f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-top" class="dd-toggle">'
            f'<label for="dd-top" class="dd-backdrop"></label><label for="dd-top" class="custom-select-btn">{_html(label)}</label>'
            f'<div class="custom-select-options">{opts}</div></div>'
        )

    def sel_sort():
        label = SORT_LABELS.get(sort_f, "Biggest Improvement")
        opts = ""
        for val, lbl in SORT_LABELS.items():
            sc = "selected" if val == sort_f else ""
            opts += f'<a href="{url(sort=val, page="1")}" class="{sc}">{_html(lbl)}</a>'
        return (
            f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-sort" class="dd-toggle">'
            f'<label for="dd-sort" class="dd-backdrop"></label><label for="dd-sort" class="custom-select-btn">{_html(label)}</label>'
            f'<div class="custom-select-options">{opts}</div></div>'
        )

    filter_tags = (
        f'<span class="filter-tag">{_html(disease_display)}</span> '
        f'<span class="filter-tag">{_html(economy_display)}</span> '
        f'<span class="filter-tag">{applied_start_y} to {applied_end_y}</span> '
        f'<span class="filter-tag">Top {applied_top_n}</span> '
    )

    def inactive_msg():
        return '<div class="chart-msg">Choose an infection type, economic status, and year range, then click <strong>Apply Filters</strong> to view this data.</div>'

    def rows_html():
        if not rows:
            return '<tr><td colspan="8" class="no-data">No infection records found for countries with data in both selected years</td></tr>'
        out = ""
        for i, (country, phase, start_cases, end_cases, start_rate, end_rate, improvement, case_reduction) in enumerate(rows):
            rank = (page - 1) * ROWS_PER_PAGE + i + 1
            sign = "+" if improvement and improvement > 0 else ""
            case_sign = "+" if case_reduction and case_reduction > 0 else ""
            delta = f'<span class="delta-badge {_delta_class(improvement)}">{sign}{improvement}</span>'
            start_badge = f'<span class="cov-badge {_rate_class(start_rate)}">{start_rate}</span>'
            end_badge = f'<span class="cov-badge {_rate_class(end_rate)}">{end_rate}</span>'
            out += (
                f"<tr><td><strong>{rank}</strong></td>"
                f"<td>{_html(country)}</td>"
                f"<td>{_html(phase)}</td>"
                f"<td>{int(start_cases)}</td>"
                f"<td>{int(end_cases)}</td>"
                f"<td>{start_badge}</td>"
                f"<td>{end_badge}</td>"
                f"<td>{delta} <span class=\"case-delta\">({case_sign}{int(case_reduction)} cases)</span></td></tr>"
            )
        return out

    def paginate():
        if total_pages <= 1:
            return ""
        shown = {1, total_pages, page}
        if page > 1:
            shown.add(page - 1)
        if page < total_pages:
            shown.add(page + 1)

        def purl(p_):
            return url(page=str(p_))

        prev_btn = f'<a href="{purl(page - 1)}" class="page-btn">&lsaquo;</a>' if page > 1 else '<span class="page-btn disabled">&lsaquo;</span>'
        next_btn = f'<a href="{purl(page + 1)}" class="page-btn">&rsaquo;</a>' if page < total_pages else '<span class="page-btn disabled">&rsaquo;</span>'
        mid = []
        last = 0
        for p_ in sorted(shown):
            if p_ - last > 1:
                mid.append('<span class="page-ellipsis">...</span>')
            mid.append(f'<span class="page-btn active">{p_}</span>' if p_ == page else f'<a href="{purl(p_)}" class="page-btn">{p_}</a>')
            last = p_
        start = 0 if cnt == 0 else (page - 1) * ROWS_PER_PAGE + 1
        end = min(page * ROWS_PER_PAGE, cnt)
        return f'<div class="pagination"><span class="pagination-info">Showing {start}&#8211;{end} of {cnt}</span><div class="pagination-btns">{prev_btn}{"".join(mid)}{next_btn}</div></div>'

    _SIMG = '<img src="/images/order%20icon.png" class="sort-icon-img" alt="">'

    def th(label, asc_key, desc_key):
        is_asc = sort_f == asc_key
        next_k = desc_key if is_asc else asc_key
        cls = " sort-asc" if is_asc else (" sort-desc" if sort_f == desc_key else "")
        return f'<th class="sortable{cls}"><a href="{url(sort=next_k, page="1")}" class="sort-link">{_html(label)} {_SIMG}</a></th>'

    def _xls_export():
        headers = [
            "Rank",
            "Country",
            "Economic phase",
            f"Cases {applied_start_y}",
            f"Cases {applied_end_y}",
            f"Rate {applied_start_y} per 100k",
            f"Rate {applied_end_y} per 100k",
            "Improvement per 100k",
            "Case reduction",
        ]
        ths = "".join(f"<th>{_html(h)}</th>" for h in headers)
        trs = ""
        for i, (country, phase, start_cases, end_cases, start_rate, end_rate, improvement, case_reduction) in enumerate(rows_all):
            trs += (
                f"<tr><td>{i + 1}</td><td>{_html(country)}</td><td>{_html(phase)}</td>"
                f"<td>{start_cases}</td><td>{end_cases}</td><td>{start_rate}</td><td>{end_rate}</td>"
                f"<td>{improvement}</td><td>{case_reduction}</td></tr>"
            )
        html = f'<html><head><meta charset="UTF-8"></head><body><table><tr>{ths}</tr>{trs}</table></body></html>'
        return "data:application/vnd.ms-excel;charset=utf-8," + urllib.parse.quote(html)

    export_href = _xls_export()

    def chart3_html():
        title_text = f"Top {applied_top_n} infection-rate improvements for {_html(disease_display)} in {_html(economy_display)}"
        title = f'<div class="table-header-row"><span class="table-title">{title_text}</span></div>'
        if not table_active:
            return title + inactive_msg()
        if len(rows_all) < 2:
            return title + '<div class="chart-msg">Not enough country data to display a chart.</div>'
        sorted_rows = sorted(rows_all, key=lambda r: r[6] if r[6] is not None else 0, reverse=True)
        max_abs = max(abs(r[6] or 0) for r in sorted_rows) or 1
        out = ""
        for i, (country, _, _, _, _, _, improvement, _) in enumerate(sorted_rows):
            value = improvement or 0
            width = round(abs(value) / max_abs * 100, 1)
            if value > 0:
                fill_cls = "bar-fill-green"
                sign = "+"
            elif value < 0:
                fill_cls = "bar-fill-red"
                sign = ""
            else:
                fill_cls = "bar-fill-gray"
                sign = ""
            out += (
                f'<div class="bar-row"><span class="bar-rank">{i + 1}</span>'
                f'<span class="bar-label" title="{_html(country)}">{_html(country)}</span>'
                f'<div class="bar-track"><div class="{fill_cls}" style="width:{width}%"></div></div>'
                f'<span class="bar-val">{sign}{value}</span></div>'
            )
        inner = f'<div class="bar-chart-h">{out}</div>'
        if applied_top_n >= 20:
            inner = f'<div class="bar-chart-scroll">{inner}</div>'
        return title + inner

    if table_active:
        t3_panel_content = f"""
            <div class="table-header-row">
                <span class="table-title">Table: Infection Improvement by Country</span>
                <a href="{export_href}" download="infection_improvement_by_country.xls" class="export-btn"><img src="/images/export%20icon.png" alt=""> Export Data</a>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead><tr>
                        <th>Rank</th>
                        {th("Country", "country_asc", "country_desc")}
                        <th>Economic phase</th>
                        {th(f"Cases {applied_start_y}", "start_cases_asc", "start_cases_desc")}
                        {th(f"Cases {applied_end_y}", "end_cases_asc", "end_cases_desc")}
                        {th(f"Rate {applied_start_y}", "start_rate_asc", "start_rate_desc")}
                        {th(f"Rate {applied_end_y}", "end_rate_asc", "end_rate_desc")}
                        {th("Improvement", "improvement_asc", "improvement_desc")}
                    </tr></thead>
                    <tbody>{rows_html()}</tbody>
                </table>
            </div>
            {paginate()}
        """
    else:
        t3_panel_content = inactive_msg()

    if _get("save_view") == "1" and table_active:
        view_name = _get("view_name")
        label = view_name if view_name else f"{disease_display}, {economy_display}, {applied_start_y} to {applied_end_y}, Top {applied_top_n}"
        new_view = {
            "label": label,
            "inf_type": applied_inf_f,
            "economy": applied_economy_f,
            "start_year": str(applied_start_y),
            "end_year": str(applied_end_y),
            "top": applied_top_f,
        }
        if _add_saved_view(db, new_view):
            saved_views = _load_saved_views(db)
            saved_message = '<span class="saved-message">Saved</span>'
        else:
            saved_message = '<span class="saved-message">Already saved</span>'

    if saved_views:
        saved_parts = []
        for v in saved_views:
            if not (v.get("inf_type") and v.get("economy") and v.get("start_year") and v.get("end_year")): continue
            link = apply_url(v["inf_type"], v["economy"], v["start_year"], v["end_year"], v.get("top", "10"))
            saved_parts.append(
                f'<div class="saved-view-item">'
                f'<a class="saved-pill" href="{link}">{_html(v.get("label", ""))}</a>'
                f'<a class="saved-action" href="/bao_page_3?delete_view={v["id"]}">Delete</a>'
                f'</div>'
            )
        saved_html = "".join(saved_parts)
    else:
        starter_views = [
            ("Measles, Lower Middle, 2000 to 2024", apply_url("MEA", "3", "2000", "2024", "10")),
            ("Rubella, High Income, 2000 to 2024", apply_url("RUB", "1", "2000", "2024", "10")),
            ("Pertussis, Low Income, 2010 to 2024", apply_url("PER", "4", "2010", "2024", "10")),
        ]
        saved_html = "".join(f'<a class="saved-pill starter" href="{href}">{_html(label)}</a>' for label, href in starter_views)
        saved_html += '<span class="empty-saved-note">Starter examples appear until you save your own view.</span>'

    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
    with open(css_file, "r", encoding="utf-8") as f:
        css = f.read()

    nav_html = nav.get_nav_html("/bao_page_3")
    footer_html = nav.get_footer_html()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>ImmuniData - Infection Improvement by Economic Status Explorer</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
</head>
<body>

{nav_html}

<div class="page-header">
    <h1>Infection Improvement by Economic Status Explorer</h1>
    <p>Compare infection rates between two years and identify countries where reported infections improved the most within an economic status</p>
</div>

<div class="filter-card">
    <div class="filter-row">
        <div class="filter-group"><label>Infection Type</label>{sel_inf()}</div>
        <div class="filter-group"><label>Economic status</label>{sel_economy()}</div>
        <div class="filter-group"><label>Start Year</label>{sel_start_year()}</div>
        <div class="filter-group"><label>End Year</label>{sel_end_year()}</div>
        <div class="filter-group"><label>Top</label>{sel_top()}</div>
        <div class="filter-group"><label>Sort by</label>{sel_sort()}</div>

        <form method="GET" action="/bao_page_3" class="form-contents">
            <input type="hidden" name="inf_type" value="{_html(inf_f)}">
            <input type="hidden" name="economy" value="{_html(economy_f)}">
            <input type="hidden" name="start_year" value="{start_y}">
            <input type="hidden" name="end_year" value="{end_y}">
            <input type="hidden" name="top" value="{_html(top_f)}">
            <input type="hidden" name="sort" value="{_html(sort_f)}">
            <input type="hidden" name="t3_view" value="{_html(t3_view_f)}">
            <input type="hidden" name="applied_inf_type" value="{_html(inf_f)}">
            <input type="hidden" name="applied_economy" value="{_html(economy_f)}">
            <input type="hidden" name="applied_start_year" value="{start_y}">
            <input type="hidden" name="applied_end_year" value="{end_y}">
            <input type="hidden" name="applied_top" value="{_html(top_f)}">
            <div class="filter-actions">
                <button type="submit" class="btn-apply"><img src="/images/filter%20icon.png" alt=""> Apply Filters</button>
                <a href="/bao_page_3" class="btn-reset"><img src="/images/reset%20icon.png" alt=""> Reset</a>
            </div>
        </form>
    </div>
</div>

<div class="results-bar" id="results-section">
    <img src="/images/showing_result%20icon.png" class="results-icon" alt="">
    <span class="results-label">Showing result for:</span>
    {filter_tags}
    <span class="ready-badge">Ready</span>
    <span class="results-count">{n_total} countries with data in both years</span>
    <span class="results-sep">|</span>
    <span class="results-note">Last updated WHO dataset {db_min_year}&#8211;{db_max_year}</span>
</div>

<div class="saved-card">
    <span class="saved-label">Saved views:</span>
    {saved_html}
    <form method="GET" action="/bao_page_3" class="save-view-form">
        <input type="hidden" name="inf_type"          value="{_html(inf_f)}">
        <input type="hidden" name="economy"           value="{_html(economy_f)}">
        <input type="hidden" name="start_year"        value="{start_y}">
        <input type="hidden" name="end_year"          value="{end_y}">
        <input type="hidden" name="top"               value="{_html(top_f)}">
        <input type="hidden" name="sort"              value="{_html(sort_f)}">
        <input type="hidden" name="t3_view"           value="{_html(t3_view_f)}">
        <input type="hidden" name="applied_inf_type"  value="{_html(applied_inf_f)}">
        <input type="hidden" name="applied_economy"   value="{_html(applied_economy_f)}">
        <input type="hidden" name="applied_start_year" value="{applied_start_y}">
        <input type="hidden" name="applied_end_year"  value="{applied_end_y}">
        <input type="hidden" name="applied_top"       value="{_html(applied_top_f)}">
        <input type="hidden" name="save_view"         value="1">
        <input type="text"   name="view_name"         class="save-view-input" placeholder="Optional view name">
        <button type="submit" class="save-view-btn">Save current view</button>
        {saved_message}
    </form>
</div>

<div class="single-table-wrap">
    <div class="table-card">
        <input type="radio" id="t3-table" name="t3-view" {'checked' if t3_view_f != 'chart' else ''} class="tab-radio">
        <input type="radio" id="t3-chart" name="t3-view" {'checked' if t3_view_f == 'chart' else ''} class="tab-radio">
        <div class="tab-bar">
            <div class="tab-btn-group">
                <a href="{url(t3_view='table')}" class="tab-btn t3-table-label"><img src="/images/table%20icon.png" alt=""> Table</a>
                <a href="{url(t3_view='chart')}" class="tab-btn t3-chart-label"><img src="/images/chart%20icon.png" alt=""> Chart</a>
            </div>
        </div>
        <div class="t3-table-panel">{t3_panel_content}</div>
        <div class="t3-chart-panel">{chart3_html()}</div>
    </div>
</div>

<div class="info-note">
    <img src="/images/iconinfo.png" class="info-icon-img" alt="">
    <span>Note: Improvement is calculated as start-year infection rate minus end-year infection rate per 100,000 people. Positive values mean reported infection rates decreased.</span>
</div>

<div class="how-card">
    <div class="how-copy">
        <img src="/images/iconinfo.png" class="info-icon-img" alt="">
        <div class="how-text">
            <span class="how-title">How This View Works?</span>
            <p>Select an infection type, economic status, start year, and end year. Use Table or Chart to compare countries by infection-rate improvement.</p>
        </div>
    </div>
    <div class="how-links">
        <span class="how-hover">
            <a href="#" class="how-link">View methodology -&gt;</a>
            <span class="how-hover-panel">Infection rate = reported cases / country population x 100,000. Improvement = start-year rate - end-year rate, so a higher positive number represents a larger reduction in reported infections.</span>
        </span>
        <a href="#" class="how-link">Data Dictionary -&gt;</a>
    </div>
</div>

{footer_html}

</body>
</html>"""
