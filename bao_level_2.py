import os
import pyhtml
import nav

ROWS_PER_PAGE = 10
SAVED_VIEWS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bao_level_2_saved_views.json")


def _html(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _esc(value):
    return str(value).replace("'", "''")


def _rate_class(rate):
    try:
        rate = float(rate)
    except (TypeError, ValueError):
        return "medium"
    if rate >= 100:
        return "low"
    if rate >= 10:
        return "medium"
    return "high"


def _load_saved_views():
    if not os.path.exists(SAVED_VIEWS_FILE):
        return []
    try:
        with open(SAVED_VIEWS_FILE, "r", encoding="utf-8") as f:
            views = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    return views if isinstance(views, list) else []


def _write_saved_views(views):
    with open(SAVED_VIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(views, f, indent=2)


def _view_code(view):
    payload = {
        "label": str(view.get("label", "Saved view")),
        "inf_type": str(view.get("inf_type", "")),
        "economy": str(view.get("economy", "")),
        "year": str(view.get("year", "")),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _view_from_code(code):
    if not code:
        return None
    try:
        padded = code + "=" * (-len(code) % 4)
        view = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(view, dict):
        return None
    required = ("inf_type", "economy", "year")
    if not all(view.get(k) for k in required):
        return None
    return {
        "label": str(view.get("label") or "Imported view"),
        "inf_type": str(view["inf_type"]),
        "economy": str(view["economy"]),
        "year": str(view["year"]),
    }


def get_page_html(form_data):
    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
    with open(css_file, 'r', encoding='utf-8') as f:
        css = f.read()

    nav_html    = nav.get_nav_html("/bao_page_2")
    footer_html = nav.get_footer_html()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>ImmuniData - Infection Data by Economic Status Explorer</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
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

<form method="GET" action="/bao_page_2" class="import-view-form">
    <span class="import-view-label">Paste view code:</span>
    <input type="text" name="import_view_code" class="import-code-input" placeholder="Paste a shared saved-view code">
    <button type="submit" class="import-code-btn">Save from code</button>
</form>

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

    <main style="min-height:60vh; padding:60px 80px;">
        <h1>Infection Data by Economic Status Explorer</h1>
    </main>

    {footer_html}

</body>
</html>"""
