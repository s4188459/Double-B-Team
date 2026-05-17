import os
import pyhtml
import nav

# About / Mission Statement page
def get_page_html(form_data):
    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
    with open(css_file, 'r', encoding='utf-8') as f:
        css = f.read()

    nav_html    = nav.get_nav_html("/bao_page_1")
    footer_html = nav.get_footer_html()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>ImmuniData - About</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
</head>
<body>

    {nav_html}

    <main class="mission-page">
        <section class="mission-section">
            <div class="mission-copy">
                <h1>Our Vision</h1>
                <p>ImmuniData exists to make preventable disease and immunisation data easier to understand, compare and act on. We want public health evidence to be accessible to students, analysts, policy teams and communities without requiring specialised tools.</p>
                <p>Our mission is to turn large vaccination and infection datasets into clear views that support better decisions, stronger awareness and more equitable health outcomes.</p>
            </div>
            <div class="mission-image-placeholder" aria-label="Image placeholder for mission statement">
                <div class="placeholder-art"></div>
            </div>
        </section>

        <section class="mission-section approach-section">
            <div class="mission-image-placeholder" aria-label="Image placeholder for user-friendly approach">
                <div class="placeholder-art"></div>
            </div>
            <div class="mission-copy">
                <h2>User-Friendly Approach</h2>
                <p>We focus on clean navigation, useful filters and readable summaries so users can move from a broad global picture to a specific country, region, disease or economic context.</p>
                <p>Every page is designed to reduce confusion: clear labels, consistent tables and practical comparisons help users find patterns without losing sight of the people behind the data.</p>
            </div>
        </section>

        <section class="personas-section">
            <div class="section-divider"></div>
            <h2>Who Are We Helping?</h2>
            <div class="persona-module">
                <input type="radio" id="persona-1" name="persona-view" class="persona-radio" checked>
                <input type="radio" id="persona-2" name="persona-view" class="persona-radio">

                <div class="persona-tab-bar">
                    <label for="persona-1" class="persona-tab persona-tab-1">Persona 1</label>
                    <label for="persona-2" class="persona-tab persona-tab-2">Persona 2</label>
                </div>

                <div class="persona-panel persona-panel-1">
                    <h3>Public Health Learners and Researchers</h3>
                    <div class="persona-copy">
                        <p>Students, educators and early-stage researchers need a reliable way to explore how vaccination coverage, disease incidence and economic indicators relate across places and years.</p>
                        <ul class="persona-list">
                            <li>Compare vaccination and infection trends without manually cleaning raw datasets.</li>
                            <li>Identify countries or regions that meet coverage targets or show signs of improvement.</li>
                            <li>Use simple, transparent views for assignments, reports and evidence-based discussion.</li>
                        </ul>
                    </div>
                </div>

                <div class="persona-panel persona-panel-2">
                    <h3>Policy Planners and Community Advocates</h3>
                    <div class="persona-copy">
                        <p>Health program planners and community advocates need clear evidence to explain where preventable disease risks remain high and where immunisation progress needs support.</p>
                        <ul class="persona-list">
                            <li>Review trends by region, country and economic context to support practical recommendations.</li>
                            <li>Spot underserved areas where vaccination coverage may not be keeping pace with public health targets.</li>
                            <li>Use accessible summaries when preparing briefings, outreach materials or stakeholder discussions.</li>
                        </ul>
                    </div>
                </div>
            </div>
        </section>

        <section class="about-us-section">
            <h2>About Us</h2>
            <div class="about-content">
                <div class="about-image-placeholder" aria-label="Image placeholder for about us">
                    <div class="placeholder-art"></div>
                </div>
                <div class="about-us-copy">
                    <p>We are a student project team building ImmuniData as a practical data explorer for preventable disease information. Our work brings together public datasets, simple interaction design and focused analysis pages.</p>
                    <p>The goal is to help users ask better questions about immunisation progress, disease burden and the social conditions that shape health outcomes.</p>
                </div>
            </div>
        </section>
    </main>

    {footer_html}

</body>
</html>"""
