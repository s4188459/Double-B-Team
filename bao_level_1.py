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
    mission_css = """
    .mission-page {
        background: #fff;
        color: #111;
    }

    .mission-section {
        display: grid;
        grid-template-columns: 1fr 1fr;
        min-height: 360px;
    }

    .mission-copy {
        padding: 54px 65px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .mission-copy h1,
    .mission-copy h2,
    .personas-section h2,
    .about-us-section h2 {
        font-size: 24px;
        line-height: 1.2;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    .mission-copy p,
    .persona-copy p,
    .about-us-copy p {
        font-size: 16px;
        line-height: 1.7;
        color: #444;
        margin-bottom: 14px;
    }

    .mission-image-placeholder,
    .about-image-placeholder {
        background: #d8d8d8;
        min-height: 360px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }

    .placeholder-art {
        position: relative;
        width: 160px;
        height: 180px;
    }

    .placeholder-art::before {
        content: "";
        position: absolute;
        width: 54px;
        height: 54px;
        border-radius: 50%;
        background: #b8b8b8;
        left: 18px;
        top: 10px;
    }

    .placeholder-art::after {
        content: "";
        position: absolute;
        width: 0;
        height: 0;
        border-left: 48px solid transparent;
        border-right: 48px solid transparent;
        border-bottom: 155px solid #b8b8b8;
        right: 0;
        bottom: 0;
    }

    .personas-section {
        padding: 40px 65px 28px;
    }

    .section-divider {
        border-top: 2px solid #9f9f9f;
        margin-bottom: 22px;
    }

    .personas-section h2,
    .about-us-section h2 {
        text-align: center;
        font-size: 20px;
    }

    .persona-module {
        display: grid;
        grid-template-columns: 132px 1fr;
        gap: 18px;
        align-items: start;
        background: #fff;
    }

    .persona-radio {
        display: none;
    }

    .persona-tab-bar {
        display: flex;
        flex-direction: column;
        gap: 12px;
        background: transparent;
        padding-top: 0;
        position: relative;
        z-index: 2;
    }

    .persona-tab {
        position: relative;
        padding: 9px 12px;
        border: 2px solid #777;
        background: #fff;
        color: #333;
        cursor: pointer;
        font-size: 14px;
        font-weight: 800;
        text-align: left;
        user-select: none;
    }

    .persona-tab:last-child {
        border-right: 2px solid #777;
    }

    .persona-tab:hover {
        background: #f0f6ff;
        color: #1a7cd4;
    }

    .persona-panel {
        display: none;
        border: 2px solid #aaa;
        background: #fff;
        padding: 24px 28px;
        min-height: 280px;
        position: relative;
        z-index: 1;
    }

    #persona-1:checked ~ .persona-tab-bar .persona-tab-1,
    #persona-2:checked ~ .persona-tab-bar .persona-tab-2 {
        background: #fff;
        color: #1a7cd4;
        border-color: #aaa;
        border-right-color: #fff;
        width: calc(100% + 20px);
        margin-right: -20px;
        padding-right: 30px;
    }

    #persona-1:checked ~ .persona-tab-bar .persona-tab-1::after,
    #persona-2:checked ~ .persona-tab-bar .persona-tab-2::after {
        content: "";
        position: absolute;
        top: 2px;
        right: -18px;
        width: 4px;
        height: calc(100% - 4px);
        background: #fff;
    }

    #persona-1:checked ~ .persona-tab-bar .persona-tab-1::before,
    #persona-2:checked ~ .persona-tab-bar .persona-tab-2::before {
        display: none;
    }

    #persona-1:checked ~ .persona-panel-1,
    #persona-2:checked ~ .persona-panel-2 {
        display: block;
    }

    .persona-panel h3 {
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 12px;
    }

    .persona-list {
        margin-top: 12px;
        display: grid;
        gap: 10px;
    }

    .persona-list li {
        font-size: 15px;
        line-height: 1.6;
        color: #444;
        margin-left: 18px;
    }

    .about-us-section {
        padding: 10px 65px 44px;
    }

    .about-content {
        display: grid;
        grid-template-columns: 190px minmax(0, 520px);
        gap: 56px;
        justify-content: center;
        align-items: center;
        margin-top: 12px;
    }

    .about-image-placeholder {
        min-height: 110px;
    }

    .about-image-placeholder .placeholder-art {
        width: 82px;
        height: 74px;
        transform: scale(0.62);
    }

    @media (max-width: 900px) {
        .mission-section {
            grid-template-columns: 1fr;
        }

        .approach-section .mission-image-placeholder {
            order: 2;
        }

        .mission-copy,
        .personas-section,
        .about-us-section {
            padding-left: 24px;
            padding-right: 24px;
        }

        .about-content {
            grid-template-columns: 1fr;
        }

        .persona-tab {
            font-size: 14px;
            padding: 12px 10px;
            text-align: center;
        }

        .persona-tab-bar {
            flex-direction: row;
            gap: 10px;
            margin-bottom: -2px;
        }

        #persona-1:checked ~ .persona-tab-bar .persona-tab-1,
        #persona-2:checked ~ .persona-tab-bar .persona-tab-2 {
            border-right-color: #aaa;
            border-bottom-color: #fff;
            width: auto;
            margin-right: 0;
            margin-bottom: -12px;
            padding-right: 10px;
            padding-bottom: 22px;
        }

        #persona-1:checked ~ .persona-tab-bar .persona-tab-1::after,
        #persona-2:checked ~ .persona-tab-bar .persona-tab-2::after {
            top: auto;
            right: 2px;
            bottom: -10px;
            width: calc(100% - 4px);
            height: 10px;
            border: none;
        }

        #persona-1:checked ~ .persona-tab-bar .persona-tab-1::before,
        #persona-2:checked ~ .persona-tab-bar .persona-tab-2::before {
            top: auto;
            right: -2px;
            bottom: -12px;
            width: calc(100% + 4px);
            height: 12px;
            border-top: none;
            border-bottom: none;
            border-right: 2px solid #aaa;
            border-left: 2px solid #aaa;
        }

        .about-content {
            gap: 22px;
        }
    }
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>ImmuniData - About</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
    <style>{mission_css}</style>
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
