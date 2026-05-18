import os
import pyhtml
import nav
import translations as tr

# About / Mission Statement page
def get_page_html(form_data):
    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
    with open(css_file, 'r', encoding='utf-8') as f:
        css = f.read()

    lang        = (form_data.get("lang") or ["en"])[0]
    tr_         = lambda k: tr.get_translation(k, lang)
    nav_html    = nav.get_nav_html("/bao_page_1", lang=lang, form_data=form_data)
    footer_html = nav.get_footer_html(lang)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
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
                <h1>{tr_("about_vision_title")}</h1>
                <p>{tr_("about_vision_p1")}</p>
                <p>{tr_("about_vision_p2")}</p>
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
                <h2>{tr_("about_approach_title")}</h2>
                <p>{tr_("about_approach_p1")}</p>
                <p>{tr_("about_approach_p2")}</p>
            </div>
        </section>

        <section class="personas-section">
            <div class="section-divider"></div>
            <h2>{tr_("about_who_title")}</h2>
            <div class="persona-module">
                <input type="radio" id="persona-1" name="persona-view" class="persona-radio" checked>
                <input type="radio" id="persona-2" name="persona-view" class="persona-radio">

                <div class="persona-tab-bar">
                    <label for="persona-1" class="persona-tab persona-tab-1">{tr_("persona_1_tab")}</label>
                    <label for="persona-2" class="persona-tab persona-tab-2">{tr_("persona_2_tab")}</label>
                </div>

                <div class="persona-panel persona-panel-1">
                    <h3>{tr_("persona_1_title")}</h3>
                    <div class="persona-copy">
                        <p>{tr_("persona_1_p")}</p>
                        <ul class="persona-list">
                            <li>{tr_("persona_1_li1")}</li>
                            <li>{tr_("persona_1_li2")}</li>
                            <li>{tr_("persona_1_li3")}</li>
                        </ul>
                    </div>
                </div>

                <div class="persona-panel persona-panel-2">
                    <h3>{tr_("persona_2_title")}</h3>
                    <div class="persona-copy">
                        <p>{tr_("persona_2_p")}</p>
                        <ul class="persona-list">
                            <li>{tr_("persona_2_li1")}</li>
                            <li>{tr_("persona_2_li2")}</li>
                            <li>{tr_("persona_2_li3")}</li>
                        </ul>
                    </div>
                </div>
            </div>
        </section>

        <section class="about-us-section">
            <h2>{tr_("about_us_title")}</h2>
            <div class="about-content">
                <div class="about-image-placeholder" aria-label="Image placeholder for about us">
                    <div class="placeholder-art"></div>
                </div>
                <div class="about-us-copy">
                    <p>{tr_("about_us_p1")}</p>
                    <p>{tr_("about_us_p2")}</p>
                </div>
            </div>
        </section>
    </main>

    {footer_html}

</body>
</html>"""
