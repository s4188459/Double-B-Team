import os
import sqlite3
import urllib.parse
import pyhtml
import nav

ROWS_PER_PAGE = 10
SAVED_VIEWS_TABLE = "BaoLevel2SavedViews"


def _esc(s):
    return str(s).replace("'", "''")


def _html(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def _rate_class(v):
    if v is None:
        return "cov-mid"
    if v >= 10:
        return "cov-low"
    if v >= 1:
        return "cov-mid"
    return "cov-high"


def _ensure_saved_views_table(db):
    with sqlite3.connect(db) as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {SAVED_VIEWS_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                inf_type TEXT NOT NULL,
                economy TEXT NOT NULL,
                year TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(inf_type, economy, year)
            )
        """)


def _load_saved_views(db):
    _ensure_saved_views_table(db)
    with sqlite3.connect(db) as conn:
        rows = conn.execute(f"""
            SELECT id, label, inf_type, economy, year
            FROM {SAVED_VIEWS_TABLE}
            ORDER BY id DESC
        """).fetchall()
    return [
        {
            "id": str(view_id),
            "label": label,
            "inf_type": inf_type,
            "economy": economy,
            "year": year,
        }
        for view_id, label, inf_type, economy, year in rows
    ]


def _add_saved_view(db, view):
    _ensure_saved_views_table(db)
    with sqlite3.connect(db) as conn:
        cur = conn.execute(f"""
            INSERT OR IGNORE INTO {SAVED_VIEWS_TABLE} (label, inf_type, economy, year)
            VALUES (?, ?, ?, ?)
        """, (
            view["label"],
            view["inf_type"],
            str(view["economy"]),
            str(view["year"]),
        ))
        return cur.rowcount > 0


def _delete_saved_view(db, view_id):
    _ensure_saved_views_table(db)
    with sqlite3.connect(db) as conn:
        conn.execute(f"DELETE FROM {SAVED_VIEWS_TABLE} WHERE id = ?", (view_id,))


def get_page_html(form_data):
    def _get(key, default=""):
        v = form_data.get(key)
        return (v[0] if v else default).strip()

    db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "immunisation.db")

    inf_opts = pyhtml.get_results_from_query(db, "SELECT id, description FROM Infection_Type ORDER BY description")
    economy_opts = pyhtml.get_results_from_query(db, "SELECT economyID, phase FROM Economy ORDER BY economyID")
    year_opts = pyhtml.get_results_from_query(db, "SELECT DISTINCT year FROM InfectionData ORDER BY year DESC")

    default_inf = inf_opts[0][0] if inf_opts else ""
    default_economy = str(economy_opts[2][0]) if len(economy_opts) >= 3 else (str(economy_opts[0][0]) if economy_opts else "")
    default_year = "2022" if any(str(y[0]) == "2022" for y in year_opts) else (str(year_opts[0][0]) if year_opts else "")

    inf_f = _get("inf_type", default_inf)
    economy_f = _get("economy", default_economy)
    year_f = _get("year", default_year)
    sort_f = _get("sort", "rate_desc")
    sort2_f = _get("sort2", "cases_desc")
    t1_view_f = _get("t1_view", "table")
    t2_view_f = _get("t2_view", "table")

    applied_inf_f = _get("applied_inf_type", inf_f)
    applied_economy_f = _get("applied_economy", economy_f)
    applied_year_f = _get("applied_year", year_f)

    saved_message = ""
    saved_views = _load_saved_views(db)
    delete_view_f = _get("delete_view")
    if delete_view_f.isdigit():
        _delete_saved_view(db, delete_view_f)
        saved_views = _load_saved_views(db)
        saved_message = '<span class="saved-message">Deleted</span>'

    try:
        page1 = max(1, int(_get("page1", "1")))
    except:
        page1 = 1
    try:
        page2 = max(1, int(_get("page2", "1")))
    except:
        page2 = 1

    SORT_LABELS = {
        "rate_desc": "Cases per 100k (High to Low)",
        "rate_asc": "Cases per 100k (Low to High)",
        "cases_desc": "Cases (High to Low)",
        "cases_asc": "Cases (Low to High)",
        "country_asc": "Country (A to Z)",
        "country_desc": "Country (Z to A)",
        "economy_asc": "Economic Status (A to Z)",
        "economy_desc": "Economic Status (Z to A)",
    }
    SORT_MAP = {
        "rate_desc": "rate_per_100k DESC",
        "rate_asc": "rate_per_100k ASC",
        "cases_desc": "i.cases DESC",
        "cases_asc": "i.cases ASC",
        "country_asc": "c.name ASC",
        "country_desc": "c.name DESC",
        "economy_asc": "e.phase ASC",
        "economy_desc": "e.phase DESC",
    }
    SORT2_LABELS = {
        "cases_desc": "Total Cases (High to Low)",
        "cases_asc": "Total Cases (Low to High)",
        "avg_desc": "Average Rate (High to Low)",
        "avg_asc": "Average Rate (Low to High)",
        "economy_asc": "Economic Status (A to Z)",
        "economy_desc": "Economic Status (Z to A)",
    }
    SORT2_MAP = {
        "cases_desc": "total_cases DESC",
        "cases_asc": "total_cases ASC",
        "avg_desc": "avg_rate_per_100k DESC",
        "avg_asc": "avg_rate_per_100k ASC",
        "economy_asc": "e.phase ASC",
        "economy_desc": "e.phase DESC",
    }

    tables_active = bool(applied_inf_f and applied_economy_f and applied_year_f.isdigit())
    summary_active = bool(applied_inf_f and applied_year_f.isdigit())
    order_by = SORT_MAP.get(sort_f, "rate_per_100k DESC")
    order_by2 = SORT2_MAP.get(sort2_f, "total_cases DESC")

    disease_display = next((desc for iid, desc in inf_opts if iid == applied_inf_f), applied_inf_f)
    economy_display = next((phase for eid, phase in economy_opts if str(eid) == str(applied_economy_f)), applied_economy_f)

    where_t1 = ""
    if tables_active:
        where_t1 = (
            f"WHERE i.inf_type = '{_esc(applied_inf_f)}' "
            f"AND c.economy = {int(applied_economy_f)} "
            f"AND i.year = {int(applied_year_f)} "
            "AND typeof(i.cases) = 'real' AND typeof(p.population) = 'real' AND p.population > 0"
        )

    t1_inner = f"""
        SELECT it.description AS disease, c.name AS country_name, e.phase AS economy_phase,
               i.year, ROUND(i.cases, 0) AS cases,
               ROUND(i.cases / p.population * 100000, 2) AS rate_per_100k
        FROM InfectionData i
        JOIN Infection_Type it ON i.inf_type = it.id
        JOIN Country c ON i.country = c.CountryID
        JOIN Economy e ON c.economy = e.economyID
        JOIN CountryPopulation p ON i.country = p.country AND i.year = p.year
        {where_t1}
    """

    if tables_active:
        cnt1 = pyhtml.get_results_from_query(db, f"SELECT COUNT(*) FROM ({t1_inner})")[0][0]
        total_p1 = max(1, -(-cnt1 // ROWS_PER_PAGE))
        page1 = min(page1, total_p1)
        rows1 = pyhtml.get_results_from_query(db, f"""
            {t1_inner}
            ORDER BY {order_by}
            LIMIT {ROWS_PER_PAGE} OFFSET {(page1 - 1) * ROWS_PER_PAGE}
        """)
        chart1_rows = pyhtml.get_results_from_query(db, f"{t1_inner} ORDER BY rate_per_100k DESC LIMIT 20")
    else:
        cnt1 = 0
        total_p1 = 1
        rows1 = []
        chart1_rows = []

    where_t2 = ""
    if summary_active:
        where_t2 = (
            f"WHERE i.inf_type = '{_esc(applied_inf_f)}' "
            f"AND i.year = {int(applied_year_f)} "
            "AND typeof(i.cases) = 'real' AND typeof(p.population) = 'real' AND p.population > 0"
        )

    t2_inner = f"""
        SELECT it.description AS disease, e.phase AS economy_phase, i.year,
               ROUND(SUM(i.cases), 0) AS total_cases,
               COUNT(DISTINCT i.country) AS countries_reporting,
               ROUND(AVG(i.cases / p.population * 100000), 2) AS avg_rate_per_100k
        FROM InfectionData i
        JOIN Infection_Type it ON i.inf_type = it.id
        JOIN Country c ON i.country = c.CountryID
        JOIN Economy e ON c.economy = e.economyID
        JOIN CountryPopulation p ON i.country = p.country AND i.year = p.year
        {where_t2}
        GROUP BY it.description, e.economyID, e.phase, i.year
    """

    if summary_active:
        cnt2 = pyhtml.get_results_from_query(db, f"SELECT COUNT(*) FROM ({t2_inner})")[0][0]
        total_p2 = max(1, -(-cnt2 // ROWS_PER_PAGE))
        page2 = min(page2, total_p2)
        rows2 = pyhtml.get_results_from_query(db, f"""
            {t2_inner}
            ORDER BY {order_by2}
            LIMIT {ROWS_PER_PAGE} OFFSET {(page2 - 1) * ROWS_PER_PAGE}
        """)
        chart2_rows = pyhtml.get_results_from_query(db, f"{t2_inner} ORDER BY total_cases DESC")
    else:
        cnt2 = 0
        total_p2 = 1
        rows2 = []
        chart2_rows = []

    def _xls_export(headers, rows):
        ths = "".join(f"<th>{_html(h)}</th>" for h in headers)
        trs = "".join("<tr>" + "".join(f"<td>{_html(c)}</td>" for c in r) + "</tr>" for r in rows)
        html = f'<html><head><meta charset="UTF-8"></head><body><table><tr>{ths}</tr>{trs}</table></body></html>'
        return "data:application/vnd.ms-excel;charset=utf-8," + urllib.parse.quote(html)

    export1_href = _xls_export(["Preventable disease", "Country", "Economic phase", "Year", "Cases", "Cases per 100,000 people"], rows1)
    export2_href = _xls_export(["Preventable disease", "Economic phase", "Year", "Cases", "Countries reporting", "Average cases per 100,000"], rows2)

    def url(**kw):
        p = {}
        if inf_f:
            p["inf_type"] = inf_f
        if economy_f:
            p["economy"] = economy_f
        if year_f:
            p["year"] = year_f
        if sort_f != "rate_desc":
            p["sort"] = sort_f
        if sort2_f != "cases_desc":
            p["sort2"] = sort2_f
        if t1_view_f == "chart":
            p["t1_view"] = t1_view_f
        if t2_view_f == "chart":
            p["t2_view"] = t2_view_f
        if applied_inf_f:
            p["applied_inf_type"] = applied_inf_f
        if applied_economy_f:
            p["applied_economy"] = applied_economy_f
        if applied_year_f:
            p["applied_year"] = applied_year_f
        p["page1"] = str(page1)
        p["page2"] = str(page2)
        p.update(kw)
        qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in p.items() if v)
        return f"/bao_page_2?{qs}" if qs else "/bao_page_2"

    def apply_url(inf_type, economy, year):
        qs = urllib.parse.urlencode({
            "inf_type": inf_type,
            "economy": economy,
            "year": year,
            "applied_inf_type": inf_type,
            "applied_economy": economy,
            "applied_year": year,
        })
        return f"/bao_page_2?{qs}"

    if _get("save_view") == "1" and applied_inf_f and applied_economy_f and applied_year_f:
        view_name = _get("view_name")
        label = view_name if view_name else f"{disease_display}, {economy_display}, {applied_year_f}"
        new_view = {
            "label": label,
            "inf_type": applied_inf_f,
            "economy": applied_economy_f,
            "year": applied_year_f,
        }
        if _add_saved_view(db, new_view):
            saved_views = _load_saved_views(db)
            saved_message = '<span class="saved-message">Saved</span>'
        else:
            saved_message = '<span class="saved-message">Already saved</span>'

    def sel_inf():
        label = next((desc for iid, desc in inf_opts if iid == inf_f), "Select infection")
        opts = ""
        for iid, desc in inf_opts:
            sc = "selected" if iid == inf_f else ""
            opts += f'<a href="{url(inf_type=iid, page1="1", page2="1")}" class="{sc}">{_html(desc)}</a>'
        return (f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-inf" class="dd-toggle">'
                f'<label for="dd-inf" class="dd-backdrop"></label><label for="dd-inf" class="custom-select-btn">{_html(label)}</label>'
                f'<div class="custom-select-options">{opts}</div></div>')

    def sel_economy():
        label = next((phase for eid, phase in economy_opts if str(eid) == str(economy_f)), "Select economic status")
        opts = ""
        for eid, phase in economy_opts:
            sc = "selected" if str(eid) == str(economy_f) else ""
            opts += f'<a href="{url(economy=str(eid), page1="1", page2="1")}" class="{sc}">{_html(phase)}</a>'
        return (f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-economy" class="dd-toggle">'
                f'<label for="dd-economy" class="dd-backdrop"></label><label for="dd-economy" class="custom-select-btn">{_html(label)}</label>'
                f'<div class="custom-select-options">{opts}</div></div>')

    def sel_year():
        opts = ""
        for (yr,) in year_opts:
            sc = "selected" if str(yr) == str(year_f) else ""
            opts += f'<a href="{url(year=str(yr), page1="1", page2="1")}" class="{sc}">{yr}</a>'
        return (f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-year" class="dd-toggle">'
                f'<label for="dd-year" class="dd-backdrop"></label><label for="dd-year" class="custom-select-btn">{_html(year_f)}</label>'
                f'<div class="custom-select-options">{opts}</div></div>')

    def sel_sort():
        label = SORT_LABELS.get(sort_f, "Cases per 100k (High to Low)")
        opts = ""
        for val, lbl in SORT_LABELS.items():
            sc = "selected" if val == sort_f else ""
            opts += f'<a href="{url(sort=val, page1="1")}" class="{sc}">{_html(lbl)}</a>'
        return (f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-sort" class="dd-toggle">'
                f'<label for="dd-sort" class="dd-backdrop"></label><label for="dd-sort" class="custom-select-btn">{_html(label)}</label>'
                f'<div class="custom-select-options">{opts}</div></div>')

    filter_tags = (
        f'<span class="filter-tag">{_html(disease_display)}</span> '
        f'<span class="filter-tag">{_html(economy_display)}</span> '
        f'<span class="filter-tag">{_html(applied_year_f)}</span> '
    )

    def rows1_html():
        if not rows1:
            return '<tr><td colspan="6" class="no-data">No infection records found for the selected filters</td></tr>'
        out = ""
        for disease, country, phase, yr, cases, rate in rows1:
            badge = f'<span class="cov-badge {_rate_class(rate)}">{rate}</span>'
            out += f"<tr><td>{_html(disease)}</td><td>{_html(country)}</td><td>{_html(phase)}</td><td>{yr}</td><td>{int(cases)}</td><td>{badge}</td></tr>"
        return out

    def rows2_html():
        if not rows2:
            return '<tr><td colspan="6" class="no-data">No economic-status summary found for the selected filters</td></tr>'
        out = ""
        for disease, phase, yr, cases, countries, avg_rate in rows2:
            badge = f'<span class="cov-badge {_rate_class(avg_rate)}">{avg_rate}</span>'
            out += f"<tr><td>{_html(disease)}</td><td>{_html(phase)}</td><td>{yr}</td><td>{int(cases)}</td><td>{countries}</td><td>{badge}</td></tr>"
        return out

    def paginate(cur, total, key, total_cnt):
        shown = {1, total, cur}
        if cur > 1:
            shown.add(cur - 1)
        if cur < total:
            shown.add(cur + 1)

        def purl(p):
            return url(**{key: str(p)})

        prev_btn = f'<a href="{purl(cur - 1)}" class="page-btn">&lsaquo;</a>' if cur > 1 else '<span class="page-btn disabled">&lsaquo;</span>'
        next_btn = f'<a href="{purl(cur + 1)}" class="page-btn">&rsaquo;</a>' if cur < total else '<span class="page-btn disabled">&rsaquo;</span>'
        mid = []
        last = 0
        for p in sorted(shown):
            if p - last > 1:
                mid.append('<span class="page-ellipsis">...</span>')
            mid.append(f'<span class="page-btn active">{p}</span>' if p == cur else f'<a href="{purl(p)}" class="page-btn">{p}</a>')
            last = p
        start = 0 if total_cnt == 0 else (cur - 1) * ROWS_PER_PAGE + 1
        end = min(cur * ROWS_PER_PAGE, total_cnt)
        return f'<div class="pagination"><span class="pagination-info">Showing {start}&#8211;{end} of {total_cnt}</span><div class="pagination-btns">{prev_btn}{"".join(mid)}{next_btn}</div></div>'

    _SIMG = '<img src="/images/order%20icon.png" class="sort-icon-img" alt="">'

    def th1(label, asc_key, desc_key):
        is_asc = sort_f == asc_key
        next_k = desc_key if is_asc else asc_key
        cls = " sort-asc" if is_asc else (" sort-desc" if sort_f == desc_key else "")
        return f'<th class="sortable{cls}"><a href="{url(sort=next_k, page1="1")}" class="sort-link">{label} {_SIMG}</a></th>'

    def th2(label, asc_key, desc_key):
        is_asc = sort2_f == asc_key
        next_k = desc_key if is_asc else asc_key
        cls = " sort-asc" if is_asc else (" sort-desc" if sort2_f == desc_key else "")
        return f'<th class="sortable{cls}"><a href="{url(sort2=next_k, page2="1")}" class="sort-link">{label} {_SIMG}</a></th>'

    def inactive_msg():
        return '<div class="chart-msg">Choose an infection type, economic status, and year, then click <strong>Apply Filters</strong> to view this data.</div>'

    def chart1_html():
        title = f'<div class="table-header-row"><span class="table-title">Top infection rates for {_html(economy_display)} in {_html(applied_year_f)}</span></div>'
        if not tables_active:
            return title + inactive_msg()
        if len(chart1_rows) < 2:
            return title + '<div class="chart-msg">Not enough country data to display a chart.</div>'
        max_val = max((r[5] or 0) for r in chart1_rows) or 1
        out = ""
        for i, (_, country, _, _, _, rate) in enumerate(chart1_rows):
            w = round((rate or 0) / max_val * 100, 1)
            out += f'<div class="bar-row"><span class="bar-rank">{i + 1}</span><span class="bar-label" title="{_html(country)}">{_html(country)}</span><div class="bar-track"><div class="bar-fill-red" style="width:{w}%"></div></div><span class="bar-val">{rate}</span></div>'
        return title + f'<div class="bar-chart-scroll"><div class="bar-chart-h">{out}</div></div>'

    def chart2_html():
        title = f'<div class="table-header-row"><span class="table-title">Total cases by economic status in {_html(applied_year_f)}</span></div>'
        if not summary_active:
            return title + inactive_msg()
        if len(chart2_rows) < 2:
            return title + '<div class="chart-msg">Not enough economic-status data to display a chart.</div>'
        max_val = max((r[3] or 0) for r in chart2_rows) or 1
        colors = ["#2980b9", "#27ae60", "#e67e22", "#9b59b6", "#e74c3c"]
        cols = labels = ""
        for idx, (_, phase, _, cases, _, _) in enumerate(chart2_rows):
            h = max(4, round((cases or 0) / max_val * 180))
            color = colors[idx % len(colors)]
            cols += f'<div class="bar-col"><span class="bar-col-val">{int(cases)}</span><div class="bar-col-fill" style="height:{h}px;background:{color}"></div></div>'
            labels += f'<div class="bar-col-label" title="{_html(phase)}">{_html(phase)}</div>'
        return title + f'<div class="bar-chart-v-wrap"><div class="bar-chart-v">{cols}</div><div class="bar-chart-v-labels">{labels}</div></div>'

    t1_panel_content = inactive_msg() if not tables_active else f"""
        <div class="table-header-row">
            <span class="table-title">Table 1: Infection Rate by Country</span>
            <a href="{export1_href}" download="infection_by_country.xls" class="export-btn"><img src="/images/export%20icon.png" alt=""> Export Data</a>
        </div>
        <div class="table-wrapper">
            <table class="data-table">
                <thead><tr>
                    <th>Preventable disease</th>
                    {th1("Country", "country_asc", "country_desc")}
                    {th1("Economic phase", "economy_asc", "economy_desc")}
                    <th>Year</th>
                    {th1("Cases", "cases_asc", "cases_desc")}
                    {th1("Cases per 100k", "rate_asc", "rate_desc")}
                </tr></thead>
                <tbody>{rows1_html()}</tbody>
            </table>
        </div>
        {paginate(page1, total_p1, "page1", cnt1)}
    """

    t2_panel_content = inactive_msg() if not summary_active else f"""
        <div class="table-header-row">
            <span class="table-title">Table 2: Infection Summary by Economic Status</span>
            <a href="{export2_href}" download="infection_by_economic_status.xls" class="export-btn"><img src="/images/export%20icon.png" alt=""> Export Data</a>
        </div>
        <div class="table-wrapper">
            <table class="data-table">
                <thead><tr>
                    <th>Preventable disease</th>
                    {th2("Economic phase", "economy_asc", "economy_desc")}
                    <th>Year</th>
                    {th2("Cases", "cases_asc", "cases_desc")}
                    <th>Countries</th>
                    {th2("Average per 100k", "avg_asc", "avg_desc")}
                </tr></thead>
                <tbody>{rows2_html()}</tbody>
            </table>
        </div>
        {paginate(page2, total_p2, "page2", cnt2)}
    """

    if saved_views:
        saved_parts = []
        for v in saved_views:
            if not (v.get("inf_type") and v.get("economy") and v.get("year")):
                continue
            saved_parts.append(
                f'<div class="saved-view-item">'
                f'<a class="saved-pill" href="{apply_url(v.get("inf_type", ""), v.get("economy", ""), v.get("year", ""))}">{_html(v.get("label", "Saved view"))}</a>'
                f'<a class="saved-action" href="/bao_page_2?delete_view={_html(v.get("id", ""))}">Delete</a>'
                f'</div>'
            )
        saved_html = "".join(saved_parts)
    else:
        starter_views = [
            ("Measles, Lower Middle, 2022", apply_url("MEA", "3", "2022")),
            ("Rubella, High Income, 2010", apply_url("RUB", "1", "2010")),
            ("Pertussis, Least Developed, 2024", apply_url("PER", "4", "2024")),
        ]
        saved_html = "".join(f'<a class="saved-pill starter" href="{href}">{_html(label)}</a>' for label, href in starter_views)
        saved_html += '<span class="empty-saved-note">Starter examples appear until you save your own view.</span>'

    page_extra_css = """
    .saved-card, .how-card {
        margin: 0 65px 20px;
        background: #fff;
        border: 1.5px solid #e0e4ea;
        border-radius: 10px;
        padding: 14px 18px;
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        box-shadow: 0 1px 5px rgba(0,0,0,0.04);
    }
    .saved-label, .how-title { font-size: 13px; font-weight: 800; color: #111; }
    .saved-pill {
        background: #b3d4f5;
        color: #1a5fa0;
        border-radius: 6px;
        padding: 7px 12px;
        font-size: 12px;
        font-weight: 700;
        text-decoration: none;
    }
    .saved-pill:hover { background: #1a7cd4; color: #fff; }
    .saved-pill.starter { background: #d8eafa; color: #1a5fa0; }
    .saved-view-item {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
        background: #f8faff;
        border: 1px solid #e0e4ea;
        border-radius: 8px;
        padding: 6px;
    }
    .saved-action {
        color: #b91c1c;
        font-size: 12px;
        font-weight: 700;
        padding: 5px 7px;
        border-radius: 6px;
    }
    .saved-action:hover { background: #fee2e2; }
    .save-view-form {
        margin-left: auto;
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
    }
    .save-view-input {
        border: 1.5px solid #d0d4da;
        border-radius: 7px;
        padding: 7px 10px;
        font-size: 12px;
        min-width: 180px;
    }
    .save-view-btn {
        background: #fff;
        color: #1a7cd4;
        border: 1.5px solid #1a7cd4;
        border-radius: 7px;
        padding: 7px 12px;
        font-size: 12px;
        font-weight: 700;
        cursor: pointer;
    }
    .save-view-btn:hover { background: #f0f6ff; }
    .saved-message {
        color: #1a7a4a;
        background: #e6faf0;
        border: 1px solid #6fcf97;
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 12px;
        font-weight: 700;
    }
    .empty-saved-note { color: #888; font-size: 12px; }
    .how-card { justify-content: space-between; margin-top: 0; }
    .how-copy { display: flex; align-items: flex-start; gap: 10px; }
    .how-copy .info-icon-img { margin-top: 2px; }
    .how-text { display: flex; flex-direction: column; gap: 3px; }
    .how-text p { font-size: 12px; color: #555; line-height: 1.45; }
    .how-links { display: flex; flex-direction: column; gap: 7px; align-items: flex-end; }
    .how-link { color: #1a7cd4; font-size: 12px; font-weight: 700; }
    .how-link:hover { text-decoration: underline; }
    .how-hover { position: relative; }
    .how-hover-panel {
        display: none;
        position: absolute;
        right: 0;
        bottom: calc(100% + 8px);
        width: 320px;
        background: #fff;
        border: 1px solid #d8e2ef;
        border-radius: 8px;
        padding: 12px 14px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.14);
        color: #444;
        font-size: 12px;
        line-height: 1.5;
        z-index: 50;
    }
    .how-hover:hover .how-hover-panel { display: block; }
    @media (max-width: 900px) {
        .saved-card, .how-card { margin-left: 24px; margin-right: 24px; }
        .save-view-form { margin-left: 0; width: 100%; }
        .how-card { align-items: flex-start; }
        .how-links { align-items: flex-start; }
    }
    """

    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
    with open(css_file, "r", encoding="utf-8") as f:
        css = f.read()

    nav_html = nav.get_nav_html("/bao_page_2")
    footer_html = nav.get_footer_html()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>ImmuniData - Infection Data by Economic Status Explorer</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}{page_extra_css}</style>
</head>
<body>

{nav_html}

<div class="page-header">
    <h1>Infection Data by Economic Status Explorer</h1>
    <p>Explore infection rates and case totals for a selected infection type across countries within a chosen economic status</p>
</div>

<div class="filter-card">
    <div class="filter-row">
        <div class="filter-group"><label>Infection Type</label>{sel_inf()}</div>
        <div class="filter-group"><label>Economic status</label>{sel_economy()}</div>
        <div class="filter-group"><label>Year</label>{sel_year()}</div>
        <div class="filter-group"><label>Sort by</label>{sel_sort()}</div>

        <form method="GET" action="/bao_page_2" style="display:contents">
            <input type="hidden" name="inf_type" value="{_html(inf_f)}">
            <input type="hidden" name="economy" value="{_html(economy_f)}">
            <input type="hidden" name="year" value="{_html(year_f)}">
            <input type="hidden" name="sort" value="{_html(sort_f)}">
            <input type="hidden" name="sort2" value="{_html(sort2_f)}">
            <input type="hidden" name="applied_inf_type" value="{_html(inf_f)}">
            <input type="hidden" name="applied_economy" value="{_html(economy_f)}">
            <input type="hidden" name="applied_year" value="{_html(year_f)}">
            <input type="hidden" name="t1_view" value="{_html(t1_view_f)}">
            <input type="hidden" name="t2_view" value="{_html(t2_view_f)}">
            <div class="filter-actions">
                <button type="submit" class="btn-apply"><img src="/images/filter%20icon.png" alt=""> Apply Filters</button>
                <a href="/bao_page_2" class="btn-reset"><img src="/images/reset%20icon.png" alt=""> Reset</a>
            </div>
        </form>
    </div>
</div>

<div class="results-bar">
    <img src="/images/showing_result%20icon.png" class="results-icon" alt="">
    <span class="results-label">Showing result for:</span>
    {filter_tags}
    <span class="ready-badge">Ready</span>
    <span class="results-count">{cnt1} countries found</span>
    <span class="results-sep">|</span>
    <span class="results-note">Last updated WHO dataset 2000&#8211;2024</span>
</div>

<div class="saved-card">
    <span class="saved-label">Saved views:</span>
    {saved_html}
    <form method="GET" action="/bao_page_2" class="save-view-form">
        <input type="hidden" name="inf_type" value="{_html(inf_f)}">
        <input type="hidden" name="economy" value="{_html(economy_f)}">
        <input type="hidden" name="year" value="{_html(year_f)}">
        <input type="hidden" name="sort" value="{_html(sort_f)}">
        <input type="hidden" name="sort2" value="{_html(sort2_f)}">
        <input type="hidden" name="applied_inf_type" value="{_html(applied_inf_f)}">
        <input type="hidden" name="applied_economy" value="{_html(applied_economy_f)}">
        <input type="hidden" name="applied_year" value="{_html(applied_year_f)}">
        <input type="hidden" name="t1_view" value="{_html(t1_view_f)}">
        <input type="hidden" name="t2_view" value="{_html(t2_view_f)}">
        <input type="hidden" name="save_view" value="1">
        <input type="text" name="view_name" class="save-view-input" placeholder="Optional view name">
        <button type="submit" class="save-view-btn">Save current view</button>
        {saved_message}
    </form>
</div>

<div class="tables-row">
    <div class="table-card">
        <input type="radio" id="t1-table" name="t1-view" {'checked' if t1_view_f != 'chart' else ''} class="tab-radio">
        <input type="radio" id="t1-chart" name="t1-view" {'checked' if t1_view_f == 'chart' else ''} class="tab-radio">
        <div class="tab-bar">
            <div class="tab-btn-group">
                <a href="{url(t1_view='table')}" class="tab-btn t1-table-label"><img src="/images/table%20icon.png" alt=""> Table</a>
                <a href="{url(t1_view='chart')}" class="tab-btn t1-chart-label"><img src="/images/chart%20icon.png" alt=""> Chart</a>
            </div>
        </div>
        <div class="t1-table-panel">{t1_panel_content}</div>
        <div class="t1-chart-panel">{chart1_html()}</div>
    </div>

    <div class="table-card">
        <input type="radio" id="t2-table" name="t2-view" {'checked' if t2_view_f != 'chart' else ''} class="tab-radio">
        <input type="radio" id="t2-chart" name="t2-view" {'checked' if t2_view_f == 'chart' else ''} class="tab-radio">
        <div class="tab-bar">
            <div class="tab-btn-group">
                <a href="{url(t2_view='table')}" class="tab-btn t2-table-label"><img src="/images/table%20icon.png" alt=""> Table</a>
                <a href="{url(t2_view='chart')}" class="tab-btn t2-chart-label"><img src="/images/chart%20icon.png" alt=""> Chart</a>
            </div>
        </div>
        <div class="t2-table-panel">{t2_panel_content}</div>
        <div class="t2-chart-panel">{chart2_html()}</div>
    </div>
</div>

<div class="info-note">
    <img src="/images/iconinfo.png" class="info-icon-img" alt="">
    <span>Note: Country infection rates are calculated as reported cases divided by population, multiplied by 100,000. Tables update when you click &#8220;Apply Filters&#8221;.</span>
</div>

<div class="how-card">
    <div class="how-copy">
        <img src="/images/iconinfo.png" class="info-icon-img" alt="">
        <div class="how-text">
            <span class="how-title">How This View Works?</span>
            <p>Select an infection type, economic status, and year. Use Table or Chart to switch between detailed records and a visual summary.</p>
        </div>
    </div>
    <div class="how-links">
        <span class="how-hover">
            <a href="#" class="how-link">View methodology -&gt;</a>
            <span class="how-hover-panel">Cases per 100,000 people = infection cases / country population x 100,000. Table 1 filters countries by economic phase. Table 2 compares total cases across all economic phases for the selected infection and year.</span>
        </span>
        <a href="#" class="how-link">Data Dictionary -&gt;</a>
    </div>
</div>

{footer_html}

</body>
</html>"""
