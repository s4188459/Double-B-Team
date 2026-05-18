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
            <img src="/images/Ourvision.png" alt="Our Vision" class="mission-image">
        </section>

        <section class="mission-section approach-section">
            <img src="/images/friendly.png" alt="User-Friendly Approach" class="mission-image">
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
                    <div class="persona-card">
                        <div class="persona-image">
                            <img src="/images/persona1.png" alt="Dr. Sarah Thompson">
                        </div>
                        <div class="persona-details">
                            <div class="persona-header">
                                <h3>Persona: Dr. Sarah Thompson</h3>
                                <div class="persona-tooltip">
                                    <span class="persona-tooltip-icon">!</span>
                                    <div class="persona-tooltip-text">Students, educators and early-stage researchers need a reliable way to explore how vaccination coverage, disease incidence and economic indicators relate across places and years.</div>
                                </div>
                            </div>
                            <div class="persona-subtitle">Public Health Learners and Researchers</div>
                            <div class="persona-section">
                                <h4>Quote</h4>
                                <p class="persona-quote">"Vaccination is one of the most powerful tools we have to prevent diseases and save lives. The more precise our data, the more effective our policies will be in improving health outcomes for everyone."</p>
                            </div>
                            <div class="persona-section">
                                <h4>Bio</h4>
                                <ul class="persona-list persona-bio-list">
                                    <li>Age: 38</li>
                                    <li>Gender: Female</li>
                                    <li>Job Title: Senior Public Health Researcher</li>
                                    <li>Education: Ph.D. in Epidemiology (Specializing in Vaccine Effectiveness and Public Health Interventions)</li>
                                    <li>Location: Global Health Research Institute (A leading research organization focused on global health challenges)</li>
                                    <li>Experience: 10 years in public health research, specializing in vaccine effectiveness and disease prevention</li>
                                    <li>Current Project: Evaluating the Impact of Vaccination Campaigns on Preventable Diseases in Low- and Middle-Income Countries (LMICs)</li>
                                </ul>
                            </div>
                            <div class="persona-section">
                                <h4>Goals</h4>
                                <ul class="persona-list">
                                    <li>Access up-to-date vaccination data across countries and regions to compare trends and evaluate vaccination campaign effectiveness.</li>
                                    <li>Generate evidence-based insights to support public health policies and immunisation strategies.</li>
                                    <li>Track long-term impacts of vaccination programs on disease prevalence and health outcomes.</li>
                                </ul>
                            </div>
                            <div class="persona-section">
                                <h4>Pain Points</h4>
                                <ul class="persona-list">
                                    <li>Vaccination data is difficult to access, filter, and compare across multiple sources.</li>
                                    <li>Data quality can be inconsistent, outdated, incomplete, or fragmented.</li>
                                    <li>Complex datasets are hard to visualise and explain clearly to policymakers.</li>
                                    <li>Different data formats make integration and analysis more difficult.</li>
                                </ul>
                            </div>
                            <div class="persona-section">
                                <h4>Needs</h4>
                                <ul class="persona-list">
                                    <li>Reliable and structured data that can be filtered by country, region, year, antigen, and disease type.</li>
                                    <li>Analytical tools and visualisations to compare vaccination rates, disease trends, and health outcomes.</li>
                                    <li>A user-friendly dashboard with clear filters, sorting, and key insights.</li>
                                    <li>Export or sharing features for collaboration with research teams and stakeholders.</li>
                                </ul>
                            </div>
                            <p class="persona-motivation"><strong>Motivation:</strong> She is motivated by improving global health outcomes, reducing health disparities, and supporting evidence-based vaccination strategies for underserved populations.</p>
                        </div>
                    </div>
                </div>

                <div class="persona-panel persona-panel-2">
                    <div class="persona-card">
                        <div class="persona-image">
                            <img src="/images/persona%202.png" alt="{tr_("persona_2_tab")}">
                        </div>
                        <div class="persona-details">
                            <div class="persona-header">
                                <h3>{tr_("persona_2_title")}</h3>
                                <div class="persona-tooltip">
                                    <span class="persona-tooltip-icon">!</span>
                                    <div class="persona-tooltip-text">{tr_("persona_2_tooltip")}</div>
                                </div>
                            </div>
                            <div class="persona-subtitle">{tr_("persona_2_group")}</div>
                            <p class="persona-quote">"{tr_("persona_2_quote")}"</p>
                            <div class="persona-meta">
                                <span>{tr_("persona_2_role")}</span>
                                <span>{tr_("persona_2_education")}</span>
                                <span>{tr_("persona_2_location")}</span>
                                <span>{tr_("persona_2_experience")}</span>
                            </div>
                            <p>{tr_("persona_2_summary")}</p>
                            <div class="persona-section">
                                <h4>{tr_("persona_2_goals_title")}</h4>
                                <ul class="persona-list">
                                    <li>{tr_("persona_2_goal_1")}</li>
                                    <li>{tr_("persona_2_goal_2")}</li>
                                    <li>{tr_("persona_2_goal_3")}</li>
                                </ul>
                            </div>
                            <div class="persona-section">
                                <h4>{tr_("persona_2_pain_title")}</h4>
                                <ul class="persona-list">
                                    <li>{tr_("persona_2_pain_1")}</li>
                                    <li>{tr_("persona_2_pain_2")}</li>
                                    <li>{tr_("persona_2_pain_3")}</li>
                                </ul>
                            </div>
                            <div class="persona-section">
                                <h4>{tr_("persona_2_needs_title")}</h4>
                                <ul class="persona-list">
                                    <li>{tr_("persona_2_need_1")}</li>
                                    <li>{tr_("persona_2_need_2")}</li>
                                    <li>{tr_("persona_2_need_3")}</li>
                                </ul>
                            </div>
                            <p class="persona-motivation"><strong>{tr_("persona_2_motivation_title")}</strong> {tr_("persona_2_motivation")}</p>
                        </div>
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
