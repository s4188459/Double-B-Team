import os
import sqlite3
import urllib.parse

import nav
import pyhtml
import translations as tr


ROWS_PER_PAGE = 10
SAVED_VIEWS_TABLE = "BaoLevel3SavedViews"


def _html(value):
    return (
        str(value if value is not None else "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _esc(value):
    return str(value).replace("'", "''")


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
    try:
        with sqlite3.connect(db) as conn:
            rows = conn.execute(f"""
                SELECT id, label, inf_type, start_year
                FROM {SAVED_VIEWS_TABLE}
                ORDER BY id DESC
            """).fetchall()
    except sqlite3.Error:
        return []
    return [
        {
            "id": str(view_id),
            "label": label,
            "inf_type": inf_type,
            "year": str(year),
        }
        for view_id, label, inf_type, year in rows
    ]


def _add_saved_view(db, view):
    try:
        with sqlite3.connect(db) as conn:
            cur = conn.execute(f"""
                INSERT OR IGNORE INTO {SAVED_VIEWS_TABLE}
                    (label, inf_type, economy, start_year, end_year, top)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                view["label"],
                view["inf_type"],
                "",
                str(view["year"]),
                "",
                "",
            ))
            return cur.rowcount > 0
    except sqlite3.Error:
        return False


def _delete_saved_view(db, view_id):
    try:
        with sqlite3.connect(db) as conn:
            conn.execute(f"DELETE FROM {SAVED_VIEWS_TABLE} WHERE id = ?", (view_id,))
    except sqlite3.Error:
        pass


def get_page_html(form_data):
    def _get(key, default=""):
        value = form_data.get(key)
        return (value[0] if value else default).strip()

    db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "immunisation.db")

    inf_opts = pyhtml.get_results_from_query(db, "SELECT id, description FROM Infection_Type ORDER BY description")
    year_opts = pyhtml.get_results_from_query(db, "SELECT DISTINCT year FROM InfectionData ORDER BY year DESC")
    db_min_year = str(year_opts[-1][0]) if year_opts else "2000"
    db_max_year = str(year_opts[0][0]) if year_opts else "2024"

    default_inf = "MEA" if any(iid == "MEA" for iid, _ in inf_opts) else (inf_opts[0][0] if inf_opts else "")
    default_year = "2020" if any(str(y[0]) == "2020" for y in year_opts) else (str(year_opts[0][0]) if year_opts else "")

    lang = _get("lang", "en")
    tr_ = lambda key: tr.get_translation(key, lang)
    db_tr = lambda value, table: tr.get_db_translation(value, lang, table)
    lang_param = f'<input type="hidden" name="lang" value="{_html(lang)}">' if lang != "en" else ""
    reset_href = f"/bao_page_3{'?lang=' + urllib.parse.quote(lang) if lang != 'en' else ''}"

    inf_f = _get("inf_type", default_inf)
    year_f = _get("year", default_year)
    sort_f = _get("sort", "rate_desc")
    t3_view_f = _get("t3_view", "table")

    applied_inf_f = _get("applied_inf_type", inf_f)
    applied_year_f = _get("applied_year", year_f)

    try:
        page = max(1, int(_get("page", "1")))
    except ValueError:
        page = 1

    try:
        year_i = int(year_f)
    except ValueError:
        year_i = int(default_year or 2020)

    try:
        applied_year_i = int(applied_year_f)
    except ValueError:
        applied_year_i = year_i

    SORT_LABELS = {
        "rate_desc": tr_("sort_rate_hl"),
        "rate_asc": tr_("sort_rate_lh"),
        "country_asc": tr_("sort_country_az"),
        "country_desc": tr_("sort_country_za"),
    }
    SORT_MAP = {
        "rate_desc": "rate_per_100k DESC",
        "rate_asc": "rate_per_100k ASC",
        "country_asc": "country_name ASC",
        "country_desc": "country_name DESC",
    }
    order_by = SORT_MAP.get(sort_f, "rate_per_100k DESC")

    table_active = bool(applied_inf_f and str(applied_year_i).isdigit())
    disease_display = next((desc for iid, desc in inf_opts if iid == applied_inf_f), applied_inf_f)

    saved_message = ""
    saved_views = _load_saved_views(db)
    delete_view_f = _get("delete_view")
    if delete_view_f.isdigit():
        _delete_saved_view(db, delete_view_f)
        saved_views = _load_saved_views(db)
        saved_message = f'<span class="saved-message">{tr_("deleted_msg")}</span>'

    global_rate = None
    global_cases = None
    country_rows_all = []
    if table_active:
        global_row = pyhtml.get_results_from_query(db, f"""
            SELECT ROUND(SUM(i.cases) / SUM(p.population) * 100000, 2) AS global_rate,
                   ROUND(SUM(i.cases), 0) AS global_cases
            FROM InfectionData i
            JOIN CountryPopulation p ON i.country = p.country AND i.year = p.year
            WHERE i.inf_type = '{_esc(applied_inf_f)}'
              AND i.year = {applied_year_i}
              AND typeof(i.cases) = 'real'
              AND typeof(p.population) = 'real'
              AND p.population > 0
        """)
        if global_row and global_row[0][0] is not None:
            global_rate = global_row[0][0]
            global_cases = global_row[0][1]
            country_rows_all = pyhtml.get_results_from_query(db, f"""
                SELECT c.name AS country_name,
                       ROUND(i.cases / p.population * 100000, 2) AS rate_per_100k,
                       ROUND(i.cases, 0) AS cases
                FROM InfectionData i
                JOIN Country c ON i.country = c.CountryID
                JOIN CountryPopulation p ON i.country = p.country AND i.year = p.year
                WHERE i.inf_type = '{_esc(applied_inf_f)}'
                  AND i.year = {applied_year_i}
                  AND typeof(i.cases) = 'real'
                  AND typeof(p.population) = 'real'
                  AND p.population > 0
                  AND (i.cases / p.population * 100000) > {float(global_rate)}
                ORDER BY {order_by}
            """)

    cnt = len(country_rows_all)
    total_pages = max(1, -(-cnt // ROWS_PER_PAGE))
    page = min(page, total_pages)
    rows = country_rows_all[(page - 1) * ROWS_PER_PAGE : page * ROWS_PER_PAGE]

    def url(**kw):
        params = {}
        if inf_f:
            params["inf_type"] = inf_f
        params["year"] = str(year_i)
        if sort_f != "rate_desc":
            params["sort"] = sort_f
        if t3_view_f == "chart":
            params["t3_view"] = t3_view_f
        if applied_inf_f:
            params["applied_inf_type"] = applied_inf_f
        params["applied_year"] = str(applied_year_i)
        params["page"] = str(page)
        if lang != "en":
            params["lang"] = lang
        params.update(kw)
        qs = urllib.parse.urlencode({k: str(v) for k, v in params.items() if v != ""})
        return f"/bao_page_3?{qs}#results-section" if qs else "/bao_page_3#results-section"

    def apply_url(inf_type, year):
        params = {
            "inf_type": inf_type,
            "year": year,
            "applied_inf_type": inf_type,
            "applied_year": year,
        }
        if lang != "en":
            params["lang"] = lang
        return f"/bao_page_3?{urllib.parse.urlencode(params)}#results-section"

    def sel_inf():
        raw_label = next((desc for iid, desc in inf_opts if iid == inf_f), None)
        label = db_tr(raw_label, "infection") if raw_label else tr_("select_infection")
        opts = ""
        for iid, desc in inf_opts:
            selected = "selected" if iid == inf_f else ""
            opts += f'<a href="{url(inf_type=iid, page="1")}" class="{selected}">{_html(db_tr(desc, "infection"))}</a>'
        return (
            f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-inf" class="dd-toggle">'
            f'<label for="dd-inf" class="dd-backdrop"></label><label for="dd-inf" class="custom-select-btn">{_html(label)}</label>'
            f'<div class="custom-select-options">{opts}</div></div>'
        )

    def sel_year():
        opts = ""
        for (yr,) in year_opts:
            selected = "selected" if int(yr) == year_i else ""
            opts += f'<a href="{url(year=str(yr), page="1")}" class="{selected}">{yr}</a>'
        return (
            f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-year" class="dd-toggle">'
            f'<label for="dd-year" class="dd-backdrop"></label><label for="dd-year" class="custom-select-btn">{year_i}</label>'
            f'<div class="custom-select-options">{opts}</div></div>'
        )

    def sel_sort():
        label = SORT_LABELS.get(sort_f, tr_("sort_rate_hl"))
        opts = ""
        for value, text in SORT_LABELS.items():
            selected = "selected" if value == sort_f else ""
            opts += f'<a href="{url(sort=value, page="1")}" class="{selected}">{_html(text)}</a>'
        return (
            f'<div class="custom-select css-dropdown"><input type="checkbox" id="dd-sort" class="dd-toggle">'
            f'<label for="dd-sort" class="dd-backdrop"></label><label for="dd-sort" class="custom-select-btn">{_html(label)}</label>'
            f'<div class="custom-select-options">{opts}</div></div>'
        )

    filter_tags = (
        f'<span class="filter-tag">{_html(disease_display)}</span> '
        f'<span class="filter-tag">{applied_year_i}</span> '
        f'<span class="filter-tag">{tr_("filter_above_global")}</span> '
    )

    def inactive_msg():
        return f'<div class="chart-msg">{tr_("inactive_msg_inf3")}</div>'

    def global_rate_cell():
        if global_rate is None:
            return "N/A"
        return f'<span class="cov-badge {_rate_class(global_rate)}">{global_rate}</span>'

    def rows_html():
        if global_rate is None:
            return f'<tr><td colspan="5" class="no-data">{tr_("no_global_data_inf3")}</td></tr>'
        out = (
            f'<tr class="global-row"><td><strong>{tr_("label_global")}</strong></td>'
            f'<td>{_html(disease_display)}</td>'
            f'<td>{global_rate_cell()}</td>'
            f'<td>{applied_year_i}</td>'
            f'<td>{int(global_cases or 0)}</td></tr>'
        )
        if not rows:
            return out + f'<tr><td colspan="5" class="no-data">{tr_("no_countries_above_rate")}</td></tr>'
        for country, rate, cases in rows:
            out += (
                f'<tr><td>{_html(country)}</td>'
                f'<td>{_html(disease_display)}</td>'
                f'<td><span class="cov-badge {_rate_class(rate)}">{rate}</span></td>'
                f'<td>{applied_year_i}</td>'
                f'<td>{int(cases)}</td></tr>'
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

        def purl(page_number):
            return url(page=str(page_number))

        prev_btn = f'<a href="{purl(page - 1)}" class="page-btn">&lsaquo;</a>' if page > 1 else '<span class="page-btn disabled">&lsaquo;</span>'
        next_btn = f'<a href="{purl(page + 1)}" class="page-btn">&rsaquo;</a>' if page < total_pages else '<span class="page-btn disabled">&rsaquo;</span>'
        mid = []
        last = 0
        for page_number in sorted(shown):
            if page_number - last > 1:
                mid.append('<span class="page-ellipsis">...</span>')
            mid.append(
                f'<span class="page-btn active">{page_number}</span>'
                if page_number == page
                else f'<a href="{purl(page_number)}" class="page-btn">{page_number}</a>'
            )
            last = page_number
        start = 0 if cnt == 0 else (page - 1) * ROWS_PER_PAGE + 1
        end = min(page * ROWS_PER_PAGE, cnt)
        return f'<div class="pagination"><span class="pagination-info">Showing {start}&#8211;{end} of {cnt}</span><div class="pagination-btns">{prev_btn}{"".join(mid)}{next_btn}</div></div>'

    _SIMG = '<img src="/images/order%20icon.png" class="sort-icon-img" alt="">'

    def th(label, asc_key, desc_key):
        is_asc = sort_f == asc_key
        next_key = desc_key if is_asc else asc_key
        cls = " sort-asc" if is_asc else (" sort-desc" if sort_f == desc_key else "")
        return f'<th class="sortable{cls}"><a href="{url(sort=next_key, page="1")}" class="sort-link">{_html(label)} {_SIMG}</a></th>'

    def _xls_export():
        headers = [tr_("th_country"), tr_("filter_infection_type"), tr_("th_inf_per_100k"), tr_("th_year"), tr_("th_reported_cases")]
        ths = "".join(f"<th>{_html(header)}</th>" for header in headers)
        trs = ""
        if global_rate is not None:
            trs += (
                f"<tr><td>{tr_('label_global')}</td><td>{_html(disease_display)}</td>"
                f"<td>{global_rate}</td><td>{applied_year_i}</td><td>{int(global_cases or 0)}</td></tr>"
            )
        for country, rate, cases in country_rows_all:
            trs += (
                f"<tr><td>{_html(country)}</td><td>{_html(disease_display)}</td>"
                f"<td>{rate}</td><td>{applied_year_i}</td><td>{int(cases)}</td></tr>"
            )
        html = f'<html><head><meta charset="UTF-8"></head><body><table><tr>{ths}</tr>{trs}</table></body></html>'
        return "data:application/vnd.ms-excel;charset=utf-8," + urllib.parse.quote(html)

    def chart3_html():
        title = f'<div class="table-header-row"><span class="table-title">{tr_("inf3_chart_title").format(_html(disease_display), applied_year_i)}</span></div>'
        if not table_active:
            return title + inactive_msg()
        if global_rate is None:
            return title + f'<div class="chart-msg">{tr_("no_global_data_inf3")}</div>'
        if len(country_rows_all) < 1:
            return title + f'<div class="chart-msg">{tr_("no_countries_above_rate")}</div>'
        chart_rows = country_rows_all[:20]
        max_val = max([global_rate] + [row[1] or 0 for row in chart_rows]) or 1
        out = (
            f'<div class="bar-row"><span class="bar-rank">G</span>'
            f'<span class="bar-label" title="{tr_("label_global")}">{tr_("label_global")}</span>'
            f'<div class="bar-track"><div class="bar-fill-gray" style="width:{round(global_rate / max_val * 100, 1)}%"></div></div>'
            f'<span class="bar-val">{global_rate}</span></div>'
        )
        for index, (country, rate, _) in enumerate(chart_rows, start=1):
            width = round((rate or 0) / max_val * 100, 1)
            out += (
                f'<div class="bar-row"><span class="bar-rank">{index}</span>'
                f'<span class="bar-label" title="{_html(country)}">{_html(country)}</span>'
                f'<div class="bar-track"><div class="bar-fill-red" style="width:{width}%"></div></div>'
                f'<span class="bar-val">{rate}</span></div>'
            )
        return title + f'<div class="bar-chart-scroll"><div class="bar-chart-h">{out}</div></div>'

    export_href = _xls_export()
    if table_active:
        t3_panel_content = f"""
            <div class="table-header-row">
                <span class="table-title">{tr_("inf3_table_title")}</span>
                <a href="{export_href}" download="countries_above_global_infection_rate.xls" class="export-btn"><img src="/images/export%20icon.png" alt=""> {tr_("btn_export_data")}</a>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead><tr>
                        {th(tr_("th_country"), "country_asc", "country_desc")}
                        <th>{tr_("filter_infection_type")}</th>
                        {th(tr_("th_inf_per_100k"), "rate_asc", "rate_desc")}
                        <th>{tr_("th_year")}</th>
                        <th>{tr_("th_reported_cases")}</th>
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
        label = view_name if view_name else f"{disease_display}, {applied_year_i}"
        if _add_saved_view(db, {"label": label, "inf_type": applied_inf_f, "year": applied_year_i}):
            saved_views = _load_saved_views(db)
            saved_message = f'<span class="saved-message">{tr_("saved_msg")}</span>'
        else:
            saved_message = f'<span class="saved-message">{tr_("already_saved_msg")}</span>'

    if saved_views:
        saved_parts = []
        for view in saved_views:
            if not (view.get("inf_type") and view.get("year")):
                continue
            link = apply_url(view["inf_type"], view["year"])
            del_href = f'/bao_page_3?delete_view={view["id"]}{("&lang=" + lang) if lang != "en" else ""}'
            saved_parts.append(
                f'<div class="saved-view-item">'
                f'<a class="saved-pill" href="{link}">{_html(view.get("label", ""))}</a>'
                f'<a class="saved-action" href="{del_href}">{tr_("delete")}</a>'
                f'</div>'
            )
        saved_html = "".join(saved_parts)
    else:
        starter_views = [
            ("Measles, 2020", apply_url("MEA", "2020")),
            ("Rubella, 2020", apply_url("RUB", "2020")),
            ("Pertussis, 2024", apply_url("PER", "2024")),
        ]
        saved_html = "".join(f'<a class="saved-pill starter" href="{href}">{_html(label)}</a>' for label, href in starter_views)
        saved_html += f'<span class="empty-saved-note">{tr_("starter_note")}</span>'

    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
    with open(css_file, "r", encoding="utf-8") as file:
        css = file.read()

    nav_html = nav.get_nav_html("/bao_page_3", lang=lang, form_data=form_data)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <title>ImmuniData - {tr_("page_inf_improvement")}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
</head>
<body>

{nav_html}

<div class="page-header">
    <h1>{tr_("page_inf_improvement")}</h1>
    <p>{tr_("page_inf_improvement_sub")}</p>
</div>

<div class="filter-card">
    <div class="filter-row">
        <div class="filter-group"><label>{tr_("filter_year")}</label>{sel_year()}</div>
        <div class="filter-group"><label>{tr_("filter_infection_type")}</label>{sel_inf()}</div>
        <div class="filter-group"><label>{tr_("filter_sort")}</label>{sel_sort()}</div>

        <form method="GET" action="/bao_page_3" class="form-contents">
            <input type="hidden" name="year" value="{year_i}">
            <input type="hidden" name="inf_type" value="{_html(inf_f)}">
            <input type="hidden" name="sort" value="{_html(sort_f)}">
            <input type="hidden" name="t3_view" value="{_html(t3_view_f)}">
            <input type="hidden" name="applied_year" value="{year_i}">
            <input type="hidden" name="applied_inf_type" value="{_html(inf_f)}">
            {lang_param}
            <div class="filter-actions">
                <button type="submit" class="btn-apply"><img src="/images/filter%20icon.png" alt=""> {tr_("btn_apply")}</button>
                <a href="{reset_href}" class="btn-reset"><img src="/images/reset%20icon.png" alt=""> {tr_("btn_reset")}</a>
            </div>
        </form>
    </div>
</div>

<div class="results-bar" id="results-section">
    <img src="/images/showing_result%20icon.png" class="results-icon" alt="">
    <span class="results-label">{tr_("showing_result")}</span>
    {filter_tags}
    <span class="ready-badge">{tr_("ready_badge")}</span>
    <span class="results-count">{tr_("countries_above_rate_count").format(cnt)}</span>
    <span class="results-sep">|</span>
    <span class="results-note">{tr_("global_rate_label").format(_html(global_rate if global_rate is not None else "N/A"))}</span>
    <span class="results-sep">|</span>
    <span class="results-note">{tr_("last_updated")} {db_min_year}&#8211;{db_max_year}</span>
</div>

<div class="saved-card">
    <span class="saved-label">{tr_("saved_views")}</span>
    {saved_html}
    <form method="GET" action="/bao_page_3" class="save-view-form">
        <input type="hidden" name="year" value="{year_i}">
        <input type="hidden" name="inf_type" value="{_html(inf_f)}">
        <input type="hidden" name="sort" value="{_html(sort_f)}">
        <input type="hidden" name="t3_view" value="{_html(t3_view_f)}">
        <input type="hidden" name="applied_year" value="{applied_year_i}">
        <input type="hidden" name="applied_inf_type" value="{_html(applied_inf_f)}">
        <input type="hidden" name="save_view" value="1">
        {lang_param}
        <input type="text" name="view_name" class="save-view-input" placeholder="{tr_("save_placeholder")}">
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
                <a href="{url(t3_view='table')}" class="tab-btn t3-table-label"><img src="/images/table%20icon.png" alt=""> {tr_("tab_table")}</a>
                <a href="{url(t3_view='chart')}" class="tab-btn t3-chart-label"><img src="/images/chart%20icon.png" alt=""> {tr_("tab_chart")}</a>
            </div>
        </div>
        <div class="t3-table-panel">{t3_panel_content}</div>
        <div class="t3-chart-panel">{chart3_html()}</div>
    </div>
</div>

<div class="info-note">
    <img src="/images/iconinfo.png" class="info-icon-img" alt="">
    <span>{tr_("info_note_inf3")}</span>
</div>

<div class="how-card">
    <div class="how-copy">
        <img src="/images/iconinfo.png" class="info-icon-img" alt="">
        <div class="how-text">
            <span class="how-title">{tr_("how_works_title")}</span>
            <p>{tr_("how_desc_inf3")}</p>
        </div>
    </div>
</div>

{nav.get_footer_html(lang)}

</body>
</html>"""
