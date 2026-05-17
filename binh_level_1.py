import os
import re
import pyhtml
import nav
import translations as tr_mod

# fixed color palette — same vaccine family always gets the same color
DISEASE_PALETTE = [
    "#1a7cd4", "#27ae60", "#8e44ad",
    "#e67e22", "#e74c3c", "#16a085",
    "#2980b9", "#d35400",
]

# extracts the letter prefix of an antigen ID, e.g. "BCG1" → "BCG"
def _antigen_abbr(antigen_id):
    letters = re.sub(r'\d', '', antigen_id)
    return letters[:3].upper()

# extracts the dose number as a readable label, e.g. "BCG1" → "1st dose"
def _antigen_dose(antigen_id):
    m = re.search(r'(\d+)$', antigen_id)
    if not m:
        return ""
    n = int(m.group(1))
    suffix = {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")
    return f"{suffix} dose"

# strips "-containing vaccine" and everything after the first comma from DB names
def _antigen_display_name(full_name):
    name = full_name.split(",")[0]
    name = re.sub(r'-containing vaccine', '', name, flags=re.IGNORECASE).strip()
    return name

# assigns colors by antigen family so related vaccines always share the same color
_color_assigned = {}
def _antigen_color(antigen_id):
    prefix = re.sub(r'\d', '', antigen_id)
    if prefix not in _color_assigned:
        _color_assigned[prefix] = DISEASE_PALETTE[len(_color_assigned) % len(DISEASE_PALETTE)]
    return _color_assigned[prefix]

# home page — fetches headline stats and builds the full HTML
def get_page_html(form_data):
    print("About to return page home page...")

    db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'immunisation.db')

    # four snapshot numbers shown in the top section
    stat1_countries = pyhtml.get_results_from_query(db,
        "SELECT COUNT(DISTINCT country) FROM Vaccination"
    )[0][0]

    stat2_coverage = str(pyhtml.get_results_from_query(db,
        "SELECT ROUND(AVG(coverage), 1) FROM Vaccination WHERE coverage IS NOT NULL"
    )[0][0]) + "%"

    stat3_high_coverage = pyhtml.get_results_from_query(db,
        """SELECT COUNT(*) FROM (
               SELECT country FROM Vaccination
               WHERE year = 2024 AND coverage IS NOT NULL
               GROUP BY country
               HAVING MIN(coverage) >= 90
           )"""
    )[0][0]

    raw_doses = pyhtml.get_results_from_query(db,
        "SELECT SUM(doses) FROM Vaccination WHERE doses IS NOT NULL"
    )[0][0]
    stat4_doses = f"{raw_doses / 1_000_000_000:.1f}B"

    lang     = (form_data.get("lang") or ["en"])[0]
    tr_      = lambda k: tr_mod.get_translation(k, lang)
    _dose_label = {1: tr_("dose_1st"), 2: tr_("dose_2nd"), 3: tr_("dose_3rd")}

    antigens = pyhtml.get_results_from_query(db, "SELECT AntigenID, name FROM Antigen ORDER BY AntigenID")

    # one card per antigen — colors reset each request so the palette stays consistent
    _color_assigned.clear()
    disease_cards_html = ""
    for antigen_id, full_name in antigens:
        abbr         = _antigen_abbr(antigen_id)
        m            = re.search(r'(\d+)$', antigen_id)
        dose         = _dose_label.get(int(m.group(1)), _antigen_dose(antigen_id)) if m else ""
        display_name = _antigen_display_name(full_name)
        color        = _antigen_color(antigen_id)
        disease_cards_html += f"""
            <div class="disease-card">
                <div class="disease-abbr-circle" style="background:{color}">{abbr}</div>
                <span class="disease-name">{display_name}</span>
                <span class="disease-dose">{dose}</span>
            </div>"""

    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
    with open(css_file, 'r', encoding='utf-8') as f:
        css = f.read()

    ls       = f"?lang={lang}" if lang != "en" else ""
    nav_html = nav.get_nav_html("/", lang=lang, form_data=form_data)

    page_html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <title>ImmuniData - Home</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
</head>
<body>

    {nav_html}

    <!-- Hero section -->
    <section class="hero">
        <div class="hero-overlay"></div>
        <div class="hero-content">
            <h1 class="hero-title">{tr_("home_hero_title")}</h1>
            <p class="hero-desc">{tr_("home_hero_desc")}</p>
            <div class="hero-buttons">
                <a href="/binh_page_2{ls}" class="btn-primary">{tr_("home_btn_explore")} &rarr;</a>
                <a href="/bao_page_1{ls}" class="btn-outline">{tr_("home_btn_learn")} <img src="/images/iconinfo.png" alt="info" class="btn-icon"></a>
            </div>
        </div>
    </section>

    <!-- Global Immunization Snapshot -->
    <section class="snapshot-section">
        <div class="snapshot-container">

            <div class="snapshot-header">
                <h2 class="snapshot-title">{tr_("home_snapshot_title")}</h2>
                <div class="methodology-wrapper">
                    <input type="checkbox" id="methodology-toggle" class="methodology-checkbox">
                    <label for="methodology-toggle" class="methodology-btn">
                        {tr_("home_view_methodology")}
                        <img src="/images/iconinfo.png" alt="info" class="btn-icon">
                    </label>
                    <div class="methodology-popup">
                        <p><strong>Data Source:</strong> Metrics are aggregated from the WHO Global Immunization Data (2000&ndash;2024).</p>
                        <p><strong>Countries Monitored:</strong> Includes nations and territories categorized into 7 global regions, tracked between 2000 and 2024.</p>
                        <p><strong>Average Coverage:</strong> Calculated as the simple average coverage rate across all tracked antigens globally.</p>
                        <p><strong>&ge;90% Coverage Target:</strong> Represents the number of nations that successfully achieved at least 90% coverage across all assessed antigens specifically in the year 2024.</p>
                        <p><strong>Total Doses:</strong> The cumulative total of vaccine doses administered and recorded for the monitored antigens over the 25-year period.</p>
                    </div>
                </div>
            </div>

            <div class="snapshot-cards">

                <div class="stat-card">
                    <img src="/images/1st card.png" alt="Countries" class="card-icon">
                    <div class="card-info">
                        <div class="card-number">{stat1_countries}</div>
                        <div class="card-label">{tr_("home_stat_countries_label")}</div>
                        <div class="card-desc">{tr_("home_stat_countries_desc")}</div>
                    </div>
                </div>

                <div class="stat-card">
                    <img src="/images/2nd card.png" alt="Average Coverage" class="card-icon">
                    <div class="card-info">
                        <div class="card-number">{stat2_coverage}</div>
                        <div class="card-label">{tr_("home_stat_coverage_label")}</div>
                        <div class="card-desc">{tr_("home_stat_coverage_desc")}</div>
                    </div>
                </div>

                <div class="stat-card">
                    <img src="/images/3rd card.png" alt="High Coverage Countries" class="card-icon">
                    <div class="card-info">
                        <div class="card-number">{stat3_high_coverage}</div>
                        <div class="card-label">{tr_("home_stat_countries_label")}</div>
                        <div class="card-desc">{tr_("home_stat_high_cov_desc")}</div>
                    </div>
                </div>

                <div class="stat-card">
                    <img src="/images/4th card.png" alt="Doses" class="card-icon">
                    <div class="card-info">
                        <div class="card-number">{stat4_doses}</div>
                        <div class="card-label">{tr_("home_stat_doses_label")}</div>
                        <div class="card-desc">{tr_("home_stat_doses_desc")}</div>
                    </div>
                </div>

            </div>
        </div>
    </section>

    <!-- Disease Covered -->
    <section class="disease-section">
        <h2 class="disease-title">{tr_("home_disease_title")}</h2>
        <div class="disease-grid">
            {disease_cards_html}
        </div>
    </section>

    {nav.get_footer_html(lang)}


</body>
</html>"""
    return page_html
