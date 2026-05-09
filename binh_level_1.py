import os
import re
import pyhtml
import navigation

DISEASE_PALETTE = [
    "#1a7cd4", "#27ae60", "#8e44ad",
    "#e67e22", "#e74c3c", "#16a085",
    "#2980b9", "#d35400",
]

def _antigen_abbr(antigen_id):
    letters = re.sub(r'\d', '', antigen_id)
    return letters[:3].upper()

def _antigen_dose(antigen_id):
    m = re.search(r'(\d+)$', antigen_id)
    if not m:
        return ""
    n = int(m.group(1))
    suffix = {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")
    return f"{suffix} dose"

def _antigen_display_name(full_name):
    name = full_name.split(",")[0]
    name = re.sub(r'-containing vaccine', '', name, flags=re.IGNORECASE).strip()
    return name

_color_assigned = {}
def _antigen_color(antigen_id):
    prefix = re.sub(r'\d', '', antigen_id)
    if prefix not in _color_assigned:
        _color_assigned[prefix] = DISEASE_PALETTE[len(_color_assigned) % len(DISEASE_PALETTE)]
    return _color_assigned[prefix]

def get_page_html(form_data):
    print("About to return page home page...")

    db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'immunisation.db')

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

    antigens = pyhtml.get_results_from_query(db, "SELECT AntigenID, name FROM Antigen ORDER BY AntigenID")

    _color_assigned.clear()
    disease_cards_html = ""
    for antigen_id, full_name in antigens:
        abbr         = _antigen_abbr(antigen_id)
        dose         = _antigen_dose(antigen_id)
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

    nav_html = navigation.get_nav_html("/")

    page_html = f"""<!DOCTYPE html>
<html lang="en">
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
            <h1 class="hero-title">Connecting the world<br>through reliable<br>vaccination data.</h1>
            <p class="hero-desc">Discover insights on immunization coverage, disease<br>incidents and trends across countries, regions and<br>over time. Data from the World Health Organization<br>(2000 - 2025)</p>
            <div class="hero-buttons">
                <a href="/binh_page_2" class="btn-primary">Explore the Data &rarr;</a>
                <a href="/bao_page_1" class="btn-outline">Learn More <img src="/images/icon_for_information.png" alt="info" class="btn-icon"></a>
            </div>
        </div>
    </section>

    <!-- Global Immunization Snapshot -->
    <section class="snapshot-section">
        <div class="snapshot-container">

            <div class="snapshot-header">
                <h2 class="snapshot-title">Global Immunization Snapshot (2000 - 2025)</h2>
                <div class="methodology-wrapper">
                    <input type="checkbox" id="methodology-toggle" class="methodology-checkbox">
                    <label for="methodology-toggle" class="methodology-btn">
                        View methodology
                        <img src="/images/icon_for_information.png" alt="info" class="btn-icon">
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
                        <div class="card-label">Countries</div>
                        <div class="card-desc">Across 7 global regions tracked (2000–2024)</div>
                    </div>
                </div>

                <div class="stat-card">
                    <img src="/images/2nd card.png" alt="Average Coverage" class="card-icon">
                    <div class="card-info">
                        <div class="card-number">{stat2_coverage}</div>
                        <div class="card-label">Average Coverage</div>
                        <div class="card-desc">Across 5 antigens and 217 countries (2000–2024)</div>
                    </div>
                </div>

                <div class="stat-card">
                    <img src="/images/3rd card.png" alt="High Coverage Countries" class="card-icon">
                    <div class="card-info">
                        <div class="card-number">{stat3_high_coverage}</div>
                        <div class="card-label">Countries</div>
                        <div class="card-desc">Achieved &ge;90% coverage across ALL antigens in 2024</div>
                    </div>
                </div>

                <div class="stat-card">
                    <img src="/images/4th card.png" alt="Doses" class="card-icon">
                    <div class="card-info">
                        <div class="card-number">{stat4_doses}</div>
                        <div class="card-label">Doses</div>
                        <div class="card-desc">Recorded across 5 antigens over 25 years</div>
                    </div>
                </div>

            </div>
        </div>
    </section>

    <!-- Disease Covered -->
    <section class="disease-section">
        <h2 class="disease-title">Disease Covered</h2>
        <div class="disease-grid">
            {disease_cards_html}
        </div>
    </section>

    <!-- Footer -->
    <footer class="site-footer">
        <div class="footer-main">

            <!-- Brand column -->
            <div class="footer-brand">
                <div class="footer-brand-title">Preventable Disease<br>Data Explorer</div>
                <p class="footer-brand-desc">Exploring vaccination data to inform decisions and improve health outcomes worldwide</p>
                <div class="footer-contacts">
                    <a href="mailto:ngodinhbinh1504@gmail.com" class="footer-contact-icon" title="Email">
                        <img src="/images/Mail icon.png" alt="Email">
                    </a>
                    <a href="tel:+84967502748" class="footer-contact-icon" title="Phone">
                        <img src="/images/phone icon.png" alt="Phone">
                    </a>
                    <a href="https://www.google.com/maps/search/174+Truong+Sa+Quan+1+TP.HCM" target="_blank" class="footer-contact-icon" title="Location">
                        <img src="/images/location icon.png" alt="Location">
                    </a>
                    <a href="#" class="footer-contact-icon" title="LinkedIn">
                        <img src="/images/LinkedIn icon.png" alt="LinkedIn">
                    </a>
                </div>
            </div>

            <!-- About column -->
            <div class="footer-col">
                <div class="footer-col-title">About</div>
                <a href="/bao_page_1" class="footer-link">Mission Statement</a>
                <a href="#" class="footer-link">Personas</a>
                <a href="#" class="footer-link">Our Team</a>
            </div>

            <!-- Focus view column -->
            <div class="footer-col">
                <div class="footer-col-title">Focus view</div>
                <a href="/binh_page_2" class="footer-link">On Country &amp; Region</a>
                <a href="/bao_page_2" class="footer-link">On Economic statistics</a>
            </div>

            <!-- In-depth analysis column -->
            <div class="footer-col">
                <div class="footer-col-title">In-depth analysis</div>
                <a href="/binh_page_3" class="footer-link">On Country &amp; Region</a>
                <a href="/bao_page_3" class="footer-link">On Economic statistics</a>
            </div>

            <!-- Help column -->
            <div class="footer-col">
                <div class="footer-col-title">Help</div>
                <a href="#" class="footer-link">FAQs</a>
                <a href="#" class="footer-link">Contact Us</a>
                <a href="#" class="footer-link">Feedback</a>
            </div>

        </div>

        <div class="footer-bottom">
            <a href="#" class="footer-legal">Privacy Policy</a>
            <span class="footer-legal-divider">|</span>
            <a href="#" class="footer-legal">Terms of Use</a>
        </div>
    </footer>


</body>
</html>"""
    return page_html
