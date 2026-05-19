import os
import sqlite3
import urllib.parse
import pyhtml
import nav
import translations as tr

ROWS_PER_PAGE = 10
SAVED_VIEWS_TABLE = "BinhLevel2SavedViews"


def _html(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


# basic SQL escaping to prevent injection in filter queries
def _esc(s):
    return str(s).replace("'", "''")




# returns CSS class for coverage badge coloring: green ≥90%, yellow ≥70%, red below
def _cov_class(v):
    if v is None: return "cov-mid"
    return "cov-high" if v >= 90 else ("cov-mid" if v >= 70 else "cov-low")


def _load_saved_views(db):
    with sqlite3.connect(db) as conn:
        try:
            conn.execute(f"ALTER TABLE {SAVED_VIEWS_TABLE} ADD COLUMN threshold TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass
        rows = conn.execute(f"""
            SELECT id, label, antigen, year, region, country, threshold
            FROM {SAVED_VIEWS_TABLE}
            ORDER BY id DESC
        """).fetchall()
    return [
        {"id": str(r[0]), "label": r[1], "antigen": r[2],
         "year": r[3], "region": r[4], "country": r[5], "threshold": r[6]}
        for r in rows
    ]


def _add_saved_view(db, view):
    with sqlite3.connect(db) as conn:
        try:
            conn.execute(f"ALTER TABLE {SAVED_VIEWS_TABLE} ADD COLUMN threshold TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass
        cur = conn.execute(f"""
            INSERT OR IGNORE INTO {SAVED_VIEWS_TABLE} (label, antigen, year, region, country, threshold)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (view["label"], view["antigen"], view["year"],
               view.get("region", ""), view.get("country", ""), view.get("threshold", "")))
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
    db_tr = lambda v, t: tr.get_db_translation(v, lang, t)
    lang_param = f'<input type="hidden" name="lang" value="{lang}">' if lang != "en" else ""
    reset_href = f"/binh_page_2{'?lang=' + lang if lang != 'en' else ''}"

    # region/country only control the dropdown UI and cascade — tables ignore them until Apply is clicked
    region_f  = _get("region")
    country_f = _get("country")

    # these are what the tables actually filter on — only update when user hits Apply Filters
    applied_region_f  = _get("applied_region")
    applied_country_f = _get("applied_country")
    applied_antigen_f = _get("applied_antigen")
    applied_year_f    = _get("applied_year")
    applied_threshold_f = _get("applied_threshold", "")
    try:    applied_threshold = max(0, min(99, int(applied_threshold_f))) if applied_threshold_f else None
    except: applied_threshold = None

    antigen_f = _get("antigen")
    year_f    = _get("year")
    sort_f    = _get("sort",  "coverage_desc")
    sort2_f   = _get("sort2", "countries_desc")
    t1_view_f = _get("t1_view", "table")
    t2_view_f = _get("t2_view", "table")

    try: page1 = max(1, int(_get("page1", "1")))
    except: page1 = 1
    try: page2 = max(1, int(_get("page2", "1")))
    except: page2 = 1

    db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'immunisation.db')

    saved_message = ""
    saved_views = _load_saved_views(db)
    delete_view_f = _get("delete_view")
    if delete_view_f.isdigit():
        _delete_saved_view(db, delete_view_f)
        saved_views = _load_saved_views(db)
        saved_message = '<span class="saved-message">Deleted</span>'

    antigen_opts = pyhtml.get_results_from_query(db, "SELECT AntigenID, name FROM Antigen ORDER BY AntigenID")
    year_opts    = pyhtml.get_results_from_query(db, "SELECT DISTINCT year FROM Vaccination ORDER BY year DESC")
    db_min_year  = str(year_opts[-1][0]) if year_opts else "2000"
    db_max_year  = str(year_opts[0][0]) if year_opts else "2024"
    region_opts  = pyhtml.get_results_from_query(db, "SELECT RegionID, region FROM Region ORDER BY region")

    # if a country is selected, look up its region so the region dropdown stays in sync
    if country_f:
        _r = pyhtml.get_results_from_query(db,
            f"SELECT region FROM Country WHERE CountryID = '{_esc(country_f)}'")
        if _r:
            region_f = str(_r[0][0])

    # narrow the country list to whichever region is selected
    if region_f:
        country_opts = pyhtml.get_results_from_query(db,
            f"SELECT CountryID, name FROM Country WHERE region = '{_esc(region_f)}' ORDER BY name")
    else:
        country_opts = pyhtml.get_results_from_query(db,
            "SELECT CountryID, name FROM Country ORDER BY name")

    # WHERE clause builder for Table 1 — always use applied_* not region_f/country_f
    def base_conds():
        # typeof='real' skips rows where missing coverage is stored as empty string rather than NULL
        c = ["TYPEOF(v.coverage) = 'real'"]
        if applied_antigen_f:                          c.append(f"v.antigen = '{_esc(applied_antigen_f)}'")
        if applied_year_f and applied_year_f.isdigit():c.append(f"v.year = {int(applied_year_f)}")
        if applied_region_f:                           c.append(f"c.region  = '{_esc(applied_region_f)}'")
        if applied_country_f:                          c.append(f"v.country = '{_esc(applied_country_f)}'")
        return " AND ".join(c)

    where_base = "WHERE " + base_conds()
    having_thr = f"HAVING AVG(v.coverage) >= {applied_threshold}" if applied_threshold is not None else ""

    def base_conds_t2():
        c = ["TYPEOF(v.coverage) = 'real'"]
        if applied_antigen_f:                          c.append(f"v.antigen = '{_esc(applied_antigen_f)}'")
        if applied_year_f and applied_year_f.isdigit():c.append(f"v.year = {int(applied_year_f)}")
        return " AND ".join(c)

    where_base_t2 = "WHERE " + base_conds_t2()

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
        "coverage_desc": tr_("sort_target_hl"),
        "coverage_asc":  tr_("sort_target_lh"),
        "country_asc":   tr_("sort_country_az"),
        "country_desc":  tr_("sort_country_za"),
        "region_asc":    tr_("sort_region_az"),
        "region_desc":   tr_("sort_region_za"),
    }
    order_by = SORT_MAP.get(sort_f, "ROUND(AVG(v.coverage),1) DESC")

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

    # tables and charts only activate when the user has applied both a specific antigen and year
    tables_active = bool(applied_antigen_f and applied_year_f and applied_year_f.isdigit())
    antigen_display = next((name for aid, name in antigen_opts if aid == applied_antigen_f), applied_antigen_f)

    country_display = ""
    if applied_country_f:
        _cr = pyhtml.get_results_from_query(db,
            f"SELECT name FROM Country WHERE CountryID = '{_esc(applied_country_f)}'")
        if _cr:
            country_display = str(_cr[0][0])

    def _t1_title_base():
        return "Country Meets Herd Immunity"

    def _t2_title():
        return "Region Summary"

    def t1_country_miss_msg():
        name = country_display or applied_country_f
        thr  = f"&ge;{applied_threshold}%" if applied_threshold is not None else ""
        msg  = f"does not meet the {thr} minimum rate" if thr else "has no coverage data"
        return f'<div class="chart-msg">{name} {msg} for {antigen_display} in {applied_year_f}</div>'

    def inactive_msg():
        missing = []
        if not applied_antigen_f: missing.append(f"<strong>{tr_('inactive_an_antigen')}</strong>")
        if not (applied_year_f and applied_year_f.isdigit()): missing.append(f"<strong>{tr_('inactive_a_year')}</strong>")
        parts = f" {tr_('inactive_and')} ".join(missing)
        suffix = tr_("inactive_apply_suffix").format(f"<strong>{tr_('btn_apply')}</strong>")
        return f'<div class="chart-msg">{tr_("inactive_select")} {parts} {suffix}</div>'

    # Table 1: countries meeting minimum coverage rate — GROUP BY + AVG handles duplicate rows
    t1_inner = f"""
        SELECT a.name AS antigen_name, v.year, c.name AS country_name,
               r.region   AS region_name,
               ROUND(AVG(v.coverage), 1) AS pct
        {JOINS}
        {where_base}
        GROUP BY a.AntigenID, v.year, v.country
        {having_thr}"""

    if tables_active:
        cnt1  = pyhtml.get_results_from_query(db, f"SELECT COUNT(*) FROM ({t1_inner})")[0][0]
        n_ctr = cnt1
        total_p1 = max(1, -(-cnt1 // ROWS_PER_PAGE))
        page1    = min(page1, total_p1)
        rows1    = pyhtml.get_results_from_query(db, f"""
            {t1_inner}
            ORDER BY {order_by}
            LIMIT {ROWS_PER_PAGE} OFFSET {(page1-1)*ROWS_PER_PAGE}""")
    else:
        cnt1 = n_ctr = 0
        total_p1 = 1
        rows1 = []

    # Table 2: per region — counts how many countries met the minimum rate for the selected filters
    t2_inner = f"""
        SELECT a.name AS antigen_name, sub.year, r.region AS region_name,
               COUNT(*) AS countries_met
        FROM (
            SELECT v.antigen, v.year, v.country, c.region AS reg_id
            FROM Vaccination v
            JOIN Country c ON v.country = c.CountryID
            {where_base_t2}
            GROUP BY v.antigen, v.year, v.country
            {having_thr}
        ) sub
        JOIN Region  r ON sub.reg_id  = r.RegionID
        JOIN Antigen a ON sub.antigen = a.AntigenID
        GROUP BY a.AntigenID, sub.year, r.RegionID"""

    if tables_active:
        cnt2     = pyhtml.get_results_from_query(db, f"SELECT COUNT(*) FROM ({t2_inner})")[0][0]
        total_p2 = max(1, -(-cnt2 // ROWS_PER_PAGE))
        page2    = min(page2, total_p2)
        rows2    = pyhtml.get_results_from_query(db, f"""
            {t2_inner}
            ORDER BY {order_by2}
            LIMIT {ROWS_PER_PAGE} OFFSET {(page2-1)*ROWS_PER_PAGE}""")
    else:
        cnt2 = 0
        total_p2 = 1
        rows2 = []

    # pull all filtered rows (no pagination limit) for the Excel export
    if tables_active:
        _exp1 = pyhtml.get_results_from_query(db, f"{t1_inner} ORDER BY {order_by}")
        _exp2 = pyhtml.get_results_from_query(db, f"{t2_inner} ORDER BY {order_by2}")
    else:
        _exp1 = _exp2 = []

    # wraps rows in an Excel-compatible HTML table encoded as a data: URI
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
    thr_hdr = f">={applied_threshold}%" if applied_threshold is not None else "All"
    export2_href = _xls_export(["Antigen", "Year", "Region", f"Countries Met {thr_hdr}"], _exp2)

    # chart data only makes sense when both antigen and year are applied
    if tables_active:
        # all countries for Chart 1 (no pagination limit)
        chart1_rows = pyhtml.get_results_from_query(db, f"""
            {t1_inner}
            ORDER BY {order_by}""")
        # distinct countries per region for Chart 2
        chart2_rows = pyhtml.get_results_from_query(db, f"""
            SELECT r.region, COUNT(DISTINCT sub.country) AS countries_met
            FROM (
                SELECT v.antigen, v.year, v.country, c.region AS reg_id
                FROM Vaccination v
                JOIN Country c ON v.country = c.CountryID
                {where_base_t2}
                GROUP BY v.antigen, v.year, v.country
                {having_thr}
            ) sub
            JOIN Region r ON sub.reg_id = r.RegionID
            GROUP BY r.RegionID
            ORDER BY countries_met DESC""")
    else:
        chart1_rows = []
        chart2_rows = []

    # URL for region/country dropdown links — each option is a real <a> that reloads the page (no JS needed)
    def cascade_url(region="", country=""):
        p = {}
        if antigen_f:         p["antigen"]          = antigen_f
        if year_f:            p["year"]              = year_f
        if region:            p["region"]            = region
        if country:           p["country"]           = country
        if applied_antigen_f: p["applied_antigen"]   = applied_antigen_f
        if applied_year_f:    p["applied_year"]      = applied_year_f
        if applied_region_f:  p["applied_region"]    = applied_region_f
        if applied_country_f: p["applied_country"]   = applied_country_f
        if applied_threshold is not None: p["applied_threshold"] = str(applied_threshold)
        if sort_f  and sort_f  != "coverage_desc":  p["sort"]  = sort_f
        if sort2_f and sort2_f != "countries_desc": p["sort2"] = sort2_f
        if t1_view_f == "chart": p["t1_view"] = t1_view_f
        if t2_view_f == "chart": p["t2_view"] = t2_view_f
        p["page1"] = "1"
        p["page2"] = "1"
        qs = "&".join(f"{k}={v}" for k, v in p.items() if v)
        return f"/binh_page_2?{qs}" if qs else "/binh_page_2"

    # general URL builder — carries all current filter params forward, overriding with kw
    def url(**kw):
        p = {}
        if antigen_f:         p["antigen"]          = antigen_f
        if year_f:            p["year"]              = year_f
        if region_f:          p["region"]            = region_f
        if country_f:         p["country"]           = country_f
        if applied_antigen_f: p["applied_antigen"]   = applied_antigen_f
        if applied_year_f:    p["applied_year"]      = applied_year_f
        if applied_region_f:  p["applied_region"]    = applied_region_f
        if applied_country_f: p["applied_country"]   = applied_country_f
        if applied_threshold is not None: p["applied_threshold"] = str(applied_threshold)
        if sort_f  and sort_f  != "coverage_desc":  p["sort"]  = sort_f
        if sort2_f and sort2_f != "countries_desc": p["sort2"] = sort2_f
        if t1_view_f == "chart": p["t1_view"] = t1_view_f
        if t2_view_f == "chart": p["t2_view"] = t2_view_f
        p["page1"] = str(page1)
        p["page2"] = str(page2)
        if lang != "en":
            p["lang"] = lang
        p.update(kw)
        qs = "&".join(f"{k}={v}" for k, v in p.items() if v)
        return f"/binh_page_2?{qs}" if qs else "/binh_page_2"

    def apply_url(antigen, year, region="", country="", threshold=""):
        p = {"antigen": antigen, "year": year,
             "applied_antigen": antigen, "applied_year": year}
        if region:    p["region"] = region;   p["applied_region"] = region
        if country:   p["country"] = country; p["applied_country"] = country
        if threshold: p["applied_threshold"] = threshold
        if lang != "en": p["lang"] = lang
        return f"/binh_page_2?{urllib.parse.urlencode(p)}"

    if _get("save_view") == "1" and applied_antigen_f and applied_year_f:
        view_name = _get("view_name")
        if not view_name:
            parts = [applied_antigen_f, applied_year_f]
            if applied_threshold is not None:
                parts.append(f"min {applied_threshold}%")
            if applied_region_f:
                rn = next((rn for rid, rn in region_opts if str(rid) == str(applied_region_f)), applied_region_f)
                parts.append(rn)
            if applied_country_f:
                _cn = pyhtml.get_results_from_query(db,
                    f"SELECT name FROM Country WHERE CountryID = '{_esc(applied_country_f)}'")
                parts.append(_cn[0][0] if _cn else applied_country_f)
            view_name = ", ".join(parts)
        new_view = {
            "label": view_name, "antigen": applied_antigen_f,
            "year": applied_year_f, "region": applied_region_f or "",
            "country": applied_country_f or "",
            "threshold": str(applied_threshold) if applied_threshold is not None else "",
        }
        if _add_saved_view(db, new_view):
            saved_views = _load_saved_views(db)
            saved_message = f'<span class="saved-message">{tr_("saved_msg")}</span>'
        else:
            saved_message = f'<span class="saved-message">{tr_("already_saved_msg")}</span>'

    if saved_views:
        saved_parts = []
        for v in saved_views:
            if not (v.get("antigen") and v.get("year")): continue
            link = apply_url(v["antigen"], v["year"], v.get("region", ""), v.get("country", ""), v.get("threshold", ""))
            del_href = f'/binh_page_2?delete_view={v["id"]}{("&lang=" + lang) if lang != "en" else ""}'
            saved_parts.append(
                f'<div class="saved-view-item">'
                f'<a class="saved-pill" href="{link}">{_html(v.get("label", ""))}</a>'
                f'<a class="saved-action" href="{del_href}">{tr_("delete")}</a>'
                f'</div>'
            )
        saved_html = "".join(saved_parts)
    else:
        starter_views = [
            ("DTPCV1, 2022", apply_url("DTPCV1", "2022")),
            ("MCV1, 2020",   apply_url("MCV1",   "2020")),
            ("RCV1, 2018",   apply_url("RCV1",   "2018")),
        ]
        saved_html = "".join(f'<a class="saved-pill starter" href="{href}">{_html(label)}</a>' for label, href in starter_views)
        saved_html += f'<span class="empty-saved-note">{tr_("starter_note")}</span>'

    # filter tags shown in the results bar — reflect applied_* not the dropdown UI state
    filter_tags = ""
    if applied_antigen_f:
        filter_tags += f'<span class="filter-tag">{antigen_display}</span> '
    if applied_year_f:
        filter_tags += f'<span class="filter-tag">{applied_year_f}</span> '
    if applied_region_f:
        rn = next((rn for rid, rn in region_opts if str(rid) == str(applied_region_f)), applied_region_f)
        filter_tags += f'<span class="filter-tag">{rn}</span> '
    if applied_country_f:
        _cn_row = pyhtml.get_results_from_query(db,
            f"SELECT name FROM Country WHERE CountryID = '{_esc(applied_country_f)}'")
        cn = _cn_row[0][0] if _cn_row else applied_country_f
        filter_tags += f'<span class="filter-tag">{cn}</span> '
    if applied_threshold is not None and tables_active:
        filter_tags += f'<span class="filter-tag">&ge;{applied_threshold}%</span> '
    if not filter_tags:
        filter_tags = '<span class="filter-all-label">All data</span> '

    def sel_antigen():
        label = next((name for aid, name in antigen_opts if aid == antigen_f), antigen_f) if antigen_f else tr_("select_antigen")
        opts = f'<a href="{url(antigen="", page1="1", page2="1")}" class="{"selected" if not antigen_f else ""}">{tr_("all_antigens")}</a>'
        for aid, aname in antigen_opts:
            sc = "selected" if aid == antigen_f else ""
            opts += f'<a href="{url(antigen=aid, page1="1", page2="1")}" class="{sc}">{aname}</a>'
        return (f'<div class="custom-select css-dropdown">'
                f'<input type="checkbox" id="dd-antigen" class="dd-toggle">'
                f'<label for="dd-antigen" class="dd-backdrop"></label>'
                f'<label for="dd-antigen" class="custom-select-btn">{label}</label>'
                f'<div class="custom-select-options">{opts}</div></div>')

    def sel_year():
        label = year_f if year_f else tr_("select_year")
        opts = f'<a href="{url(year="", page1="1", page2="1")}" class="{"selected" if not year_f else ""}">{tr_("all_years")}</a>'
        for (yr,) in year_opts:
            sc = "selected" if str(yr) == year_f else ""
            opts += f'<a href="{url(year=str(yr), page1="1", page2="1")}" class="{sc}">{yr}</a>'
        return (f'<div class="custom-select css-dropdown">'
                f'<input type="checkbox" id="dd-year" class="dd-toggle">'
                f'<label for="dd-year" class="dd-backdrop"></label>'
                f'<label for="dd-year" class="custom-select-btn">{label}</label>'
                f'<div class="custom-select-options">{opts}</div></div>')

    def sel_region():
        # region is locked to read-only when a country is already chosen
        if country_f:
            rn = next((rn for rid, rn in region_opts if str(rid) == str(region_f)), "All Regions")
            return f'<div class="custom-select-locked">{db_tr(rn, "region")}</div>'
        raw_label = next((rn for rid, rn in region_opts if str(rid) == str(region_f)), None)
        label = db_tr(raw_label, "region") if raw_label else tr_("all_regions")
        opts = f'<a href="{cascade_url()}" class="{"selected" if not region_f else ""}">{tr_("all_regions")}</a>'
        for rid, rn in region_opts:
            sc = "selected" if str(rid) == str(region_f) else ""
            opts += f'<a href="{cascade_url(region=str(rid))}" class="{sc}">{db_tr(rn, "region").replace("&","&amp;")}</a>'
        return (f'<div class="custom-select css-dropdown">'
                f'<input type="checkbox" id="dd-region" class="dd-toggle">'
                f'<label for="dd-region" class="dd-backdrop"></label>'
                f'<label for="dd-region" class="custom-select-btn">{label}</label>'
                f'<div class="custom-select-options">{opts}</div>'
                f'</div>')

    def sel_country():
        label = next((cn for cid, cn in country_opts if cid == country_f), "All Countries")
        # "All Countries" clears the country but keeps the region so the list doesn't reset
        opts = f'<a href="{cascade_url(region=region_f)}" class="{"selected" if not country_f else ""}">All Countries</a>'
        for cid, cn in country_opts:
            sc = "selected" if cid == country_f else ""
            opts += f'<a href="{cascade_url(country=cid)}" class="{sc}">{cn}</a>'
        return (f'<div class="custom-select css-dropdown">'
                f'<input type="checkbox" id="dd-country" class="dd-toggle">'
                f'<label for="dd-country" class="dd-backdrop"></label>'
                f'<label for="dd-country" class="custom-select-btn">{label}</label>'
                f'<div class="custom-select-options">{opts}</div>'
                f'</div>')

    def sel_threshold():
        OPTS = [("—", "")] + [(f"{rate}%", str(rate)) for rate in range(0, 100)]
        label = f"{applied_threshold}%" if applied_threshold is not None else "—"
        cur   = str(applied_threshold) if applied_threshold is not None else ""
        opts  = ""
        for lbl, val in OPTS:
            sc    = "selected" if val == cur else ""
            opts += f'<a href="{url(applied_threshold=val, page1="1", page2="1")}" class="{sc}">{lbl}</a>'
        return (f'<div class="custom-select css-dropdown">'
                f'<input type="checkbox" id="dd-threshold" class="dd-toggle">'
                f'<label for="dd-threshold" class="dd-backdrop"></label>'
                f'<label for="dd-threshold" class="custom-select-btn">{label}</label>'
                f'<div class="custom-select-options">{opts}</div></div>')

    def sel_sort():
        label = SORT_LABELS.get(sort_f, "% of Target (High→Low)")
        opts = ""
        for val, lbl in SORT_LABELS.items():
            sc = "selected" if val == sort_f else ""
            opts += f'<a href="{url(sort=val, page1="1", page2="1")}" class="{sc}">{lbl}</a>'
        return (f'<div class="custom-select css-dropdown">'
                f'<input type="checkbox" id="dd-sort" class="dd-toggle">'
                f'<label for="dd-sort" class="dd-backdrop"></label>'
                f'<label for="dd-sort" class="custom-select-btn">{label}</label>'
                f'<div class="custom-select-options">{opts}</div></div>')

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

    # renders prev/next + numbered page links, with ellipsis for long ranges
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

    _SIMG = '<img src="/images/order%20icon.png" class="sort-icon-img" alt="">'

    # Table 1 sortable header — toggles between asc/desc and links back with the new sort key
    def th1(label, asc_key, desc_key):
        is_asc = sort_f == asc_key
        next_k = desc_key if is_asc else asc_key
        cls    = " sort-asc" if is_asc else (" sort-desc" if sort_f == desc_key else "")
        return (f'<th class="sortable{cls}">'
                f'<a href="{url(sort=next_k, page1="1")}" class="sort-link">'
                f'{label} {_SIMG}</a></th>')

    # same as th1 but links against sort2 for Table 2
    def th2(label, asc_key, desc_key):
        is_asc = sort2_f == asc_key
        next_k = desc_key if is_asc else asc_key
        cls    = " sort-asc" if is_asc else (" sort-desc" if sort2_f == desc_key else "")
        return (f'<th class="sortable{cls}">'
                f'<a href="{url(sort2=next_k, page2="1")}" class="sort-link">'
                f'{label} {_SIMG}</a></th>')

    # one color per region for Chart 2 bars
    _REGION_COLORS = ["#2980b9", "#27ae60", "#e67e22", "#9b59b6",
                      "#e74c3c", "#1abc9c", "#f39c12", "#16a085"]

    # horizontal bar chart — shows all countries meeting minimum rate, scrollable if more than 15
    def chart1_html():
        title = f'<div class="table-header-row"><span class="table-title">Table 1: {_t1_title_base()}</span></div>'
        if not tables_active:
            return title + inactive_msg()
        if applied_country_f and cnt1 == 0:
            return title + t1_country_miss_msg()
        if len(chart1_rows) < 2:
            return title + '<div class="chart-msg">Not enough data — need at least 2 countries to display a chart</div>'
        max_val = max((pct or 0) for _, _, _, _, pct in chart1_rows) or 1
        out = ""
        for i, (_, _, cname, _, pct) in enumerate(chart1_rows):
            w = round((pct or 0) / max_val * 100, 1)
            out += (f'<div class="bar-row">'
                    f'<span class="bar-rank">{i+1}</span>'
                    f'<span class="bar-label" title="{cname}">{cname}</span>'
                    f'<div class="bar-track"><div class="bar-fill-blue" style="width:{w}%"></div></div>'
                    f'<span class="bar-val">{pct}%</span>'
                    f'</div>')
        inner = f'<div class="bar-chart-h">{out}</div>'
        if len(chart1_rows) > 15:
            inner = f'<div class="bar-chart-scroll">{inner}</div>'
        return title + inner

    # vertical bar chart — one bar per region, height = number of countries that met the target
    def chart2_html():
        title_text = f"Table 2: {_t2_title()}"
        title = f'<div class="table-header-row"><span class="table-title">{title_text}</span></div>'
        if not tables_active:
            return title + inactive_msg()
        if len(chart2_rows) < 2:
            return title + '<div class="chart-msg">Not enough data — need at least 2 regions to display a chart</div>'
        max_val = max(cnt for _, cnt in chart2_rows) or 1
        MAX_H   = 180
        cols = labels = ""
        for idx, (rname, cnt) in enumerate(chart2_rows):
            color = _REGION_COLORS[idx % len(_REGION_COLORS)]
            h     = max(4, round(cnt / max_val * MAX_H))
            cols   += (f'<div class="bar-col">'
                       f'<span class="bar-col-val">{cnt}</span>'
                       f'<div class="bar-col-fill" style="height:{h}px;background:{color}"></div>'
                       f'</div>')
            labels += f'<div class="bar-col-label" title="{rname}">{rname}</div>'
        return (title +
                f'<div class="bar-chart-v-wrap">'
                f'<div class="bar-chart-v">{cols}</div>'
                f'<div class="bar-chart-v-labels">{labels}</div>'
                f'</div>')

    if tables_active:
        if applied_country_f and cnt1 == 0:
            t1_panel_content = f"""
            <div class="table-header-row">
                <span class="table-title">Table 1: {_t1_title_base()}</span>
            </div>
            {t1_country_miss_msg()}"""
        else:
            t1_panel_content = f"""
            <div class="table-header-row">
                <span class="table-title">Table 1: {_t1_title_base()}</span>
                <a href="{export1_href}" download="vaccination_table1.xls" class="export-btn">
                    <img src="/images/export%20icon.png" alt=""> Export Data
                </a>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead><tr>
                        {th1("Antigen",      "antigen_asc",  "antigen_desc")}
                        {th1("Year",         "year_asc",     "year_desc")}
                        {th1("Country",      "country_asc",  "country_desc")}
                        {th1("Region",       "region_asc",   "region_desc")}
                        {th1("% of Target",  "coverage_asc", "coverage_desc")}
                    </tr></thead>
                    <tbody>{rows1_html()}</tbody>
                </table>
            </div>
            {paginate(page1, total_p1, "page1", cnt1)}"""
        t2_panel_content = f"""
            <div class="table-header-row">
                <span class="table-title">Table 2: {_t2_title()}</span>
                <a href="{export2_href}" download="vaccination_table2.xls" class="export-btn">
                    <img src="/images/export%20icon.png" alt=""> Export Data
                </a>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead><tr>
                        {th2("Antigen",            "antigen2_asc",  "antigen2_desc")}
                        {th2("Year",               "year2_asc",     "year2_desc")}
                        {th2(f"Countries met {f'≥{applied_threshold}%' if applied_threshold is not None else '(all)'}", "countries_asc", "countries_desc")}
                        {th2("Region",             "region2_asc",   "region2_desc")}
                    </tr></thead>
                    <tbody>{rows2_html()}</tbody>
                </table>
            </div>
            {paginate(page2, total_p2, "page2", cnt2)}"""
    else:
        t1_panel_content = (
            f'<div class="table-header-row"><span class="table-title">Table 1: {_t1_title_base()}</span></div>'
            + inactive_msg()
        )
        t2_panel_content = (
            f'<div class="table-header-row"><span class="table-title">Table 2: {_t2_title()}</span></div>'
            + inactive_msg()
        )

    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
    with open(css_file, 'r', encoding='utf-8') as f:
        css = f.read()

    nav_html    = nav.get_nav_html("/binh_page_2", lang=lang, form_data=form_data)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <title>ImmuniData - {tr_("page_vacc_explorer")}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
</head>
<body>

{nav_html}

<div class="page-header">
    <h1>{tr_("page_vacc_explorer")}</h1>
    <p>{tr_("page_vacc_explorer_sub")}</p>
</div>

<div class="filter-card">
    <div class="filter-row">

        <!-- All dropdowns use instant navigation — selecting any option reloads immediately -->
        <div class="filter-group"><label>{tr_("filter_region")}</label>{sel_region()}</div>
        <div class="filter-group"><label>{tr_("filter_country")}</label>{sel_country()}</div>
        <div class="filter-group"><label>{tr_("filter_antigen")}</label>{sel_antigen()}</div>
        <div class="filter-group"><label>{tr_("filter_year")}</label>{sel_year()}</div>
        <div class="filter-group"><label>Min. Rate (%)</label>{sel_threshold()}</div>
        <div class="filter-group"><label>{tr_("filter_sort")}</label>{sel_sort()}</div>

        <!-- Apply Filters: applies region/country to tables; hidden fields preserve current params -->
        <form method="GET" action="/binh_page_2" class="form-contents">
            <input type="hidden" name="antigen"          value="{antigen_f}">
            <input type="hidden" name="year"             value="{year_f}">
            <input type="hidden" name="sort"             value="{sort_f}">
            <input type="hidden" name="sort2"            value="{sort2_f}">
            <input type="hidden" name="region"           value="{region_f}">
            <input type="hidden" name="country"          value="{country_f}">
            <input type="hidden" name="applied_antigen"  value="{antigen_f}">
            <input type="hidden" name="applied_year"     value="{year_f}">
            <input type="hidden" name="applied_region"   value="{region_f}">
            <input type="hidden" name="applied_country"  value="{country_f}">
            <input type="hidden" name="t1_view"          value="{t1_view_f}">
            <input type="hidden" name="t2_view"          value="{t2_view_f}">
            <input type="hidden" name="applied_threshold" value="{_html(str(applied_threshold) if applied_threshold is not None else '')}">
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

<div class="results-bar">
    <img src="/images/showing_result%20icon.png" class="results-icon" alt="">
    <span class="results-label">{tr_("showing_result")}</span>
    {filter_tags}
    <span class="ready-badge">Ready</span>
    <span class="results-count">{n_ctr} {tr_("countries_found")}</span>
    <span class="results-sep">|</span>
    <span class="results-note">{tr_("last_updated")} {db_min_year}&#8211;{db_max_year}</span>
</div>

<div class="saved-card">
    <span class="saved-label">{tr_("saved_views")}</span>
    {saved_html}
    <form method="GET" action="/binh_page_2" class="save-view-form">
        <input type="hidden" name="antigen"          value="{_html(antigen_f)}">
        <input type="hidden" name="year"             value="{_html(year_f)}">
        <input type="hidden" name="region"           value="{_html(region_f)}">
        <input type="hidden" name="country"          value="{_html(country_f)}">
        <input type="hidden" name="sort"             value="{_html(sort_f)}">
        <input type="hidden" name="sort2"            value="{_html(sort2_f)}">
        <input type="hidden" name="applied_antigen"  value="{_html(applied_antigen_f)}">
        <input type="hidden" name="applied_year"     value="{_html(applied_year_f)}">
        <input type="hidden" name="applied_region"   value="{_html(applied_region_f)}">
        <input type="hidden" name="applied_country"  value="{_html(applied_country_f)}">
        <input type="hidden" name="t1_view"          value="{_html(t1_view_f)}">
        <input type="hidden" name="t2_view"          value="{_html(t2_view_f)}">
        <input type="hidden" name="applied_threshold" value="{_html(str(applied_threshold) if applied_threshold is not None else '')}">
        <input type="hidden" name="save_view"        value="1">
        {lang_param}
        <input type="text"   name="view_name"        class="save-view-input" placeholder="{tr_("save_placeholder")}">
        <button type="submit" class="save-view-btn">{tr_("save_view_btn")}</button>
        {saved_message}
    </form>
</div>

<div class="tables-row">

    <!-- Table 1: Countries meeting minimum rate -->
    <div class="table-card">
        <input type="radio" id="t1-table" name="t1-view" {'checked' if t1_view_f != 'chart' else ''} class="tab-radio">
        <input type="radio" id="t1-chart" name="t1-view" {'checked' if t1_view_f == 'chart' else ''} class="tab-radio">
        <div class="tab-bar">
            <div class="tab-btn-group">
                <a href="{url(t1_view='table')}" class="tab-btn t1-table-label"><img src="/images/table%20icon.png" alt=""> {tr_("tab_table")}</a>
                <a href="{url(t1_view='chart')}" class="tab-btn t1-chart-label"><img src="/images/chart%20icon.png" alt=""> {tr_("tab_chart")}</a>
            </div>
        </div>
        <div class="t1-table-panel">
            {t1_panel_content}
        </div>
        <div class="t1-chart-panel">
            {chart1_html()}
        </div>
    </div>

    <!-- Table 2: Countries meeting minimum rate per region -->
    <div class="table-card">
        <input type="radio" id="t2-table" name="t2-view" {'checked' if t2_view_f != 'chart' else ''} class="tab-radio">
        <input type="radio" id="t2-chart" name="t2-view" {'checked' if t2_view_f == 'chart' else ''} class="tab-radio">
        <div class="tab-bar">
            <div class="tab-btn-group">
                <a href="{url(t2_view='table')}" class="tab-btn t2-table-label"><img src="/images/table%20icon.png" alt=""> {tr_("tab_table")}</a>
                <a href="{url(t2_view='chart')}" class="tab-btn t2-chart-label"><img src="/images/chart%20icon.png" alt=""> {tr_("tab_chart")}</a>
            </div>
        </div>
        <div class="t2-table-panel">
            {t2_panel_content}
        </div>
        <div class="t2-chart-panel">
            {chart2_html()}
        </div>
    </div>

</div>

<div class="info-note">
    <img src="/images/iconinfo.png" class="info-icon-img" alt="">
    <span>{tr_("info_note_vacc2")}</span>
</div>

<div class="how-card">
    <div class="how-copy">
        <img src="/images/iconinfo.png" class="info-icon-img" alt="">
        <div class="how-text">
            <span class="how-title">{tr_("how_works_title")}</span>
            <p>{tr_("how_desc_vacc2")}</p>
        </div>
    </div>
</div>

{nav.get_footer_html(lang)}

</body>
</html>"""
