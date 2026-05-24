import os
import sqlite3
import nav
import translations as tr

PERSONA_TABLE = "AboutPersona"
TEAM_TABLE = "AboutTeamMember"


def _html(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


def _ensure_personas(db):
    with sqlite3.connect(db) as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {PERSONA_TABLE} (
                id INTEGER PRIMARY KEY,
                sort_order INTEGER NOT NULL UNIQUE,
                tab_label TEXT NOT NULL,
                image_src TEXT NOT NULL,
                image_alt TEXT NOT NULL,
                display_name TEXT NOT NULL,
                subtitle TEXT NOT NULL,
                tooltip TEXT NOT NULL,
                quote TEXT NOT NULL,
                age TEXT NOT NULL,
                gender TEXT NOT NULL,
                job_title TEXT NOT NULL,
                education TEXT NOT NULL,
                location TEXT NOT NULL,
                experience TEXT NOT NULL,
                current_project TEXT NOT NULL,
                goal_1 TEXT NOT NULL,
                goal_2 TEXT NOT NULL,
                goal_3 TEXT NOT NULL,
                goal_4 TEXT NOT NULL DEFAULT '',
                pain_1 TEXT NOT NULL,
                pain_2 TEXT NOT NULL,
                pain_3 TEXT NOT NULL,
                pain_4 TEXT NOT NULL DEFAULT '',
                need_1 TEXT NOT NULL,
                need_2 TEXT NOT NULL,
                need_3 TEXT NOT NULL,
                need_4 TEXT NOT NULL DEFAULT '',
                motivation TEXT NOT NULL
            )
        """)


def _load_personas(db):
    _ensure_personas(db)
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(f"""
            SELECT *
            FROM {PERSONA_TABLE}
            ORDER BY sort_order
        """).fetchall()
    return [dict(row) for row in rows]


def _ensure_team_members(db):
    with sqlite3.connect(db) as conn:
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {TEAM_TABLE} (
                id INTEGER PRIMARY KEY,
                sort_order INTEGER NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                student_id TEXT NOT NULL
            )
        """)


def _load_team_members(db):
    _ensure_team_members(db)
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(f"""
            SELECT full_name, student_id
            FROM {TEAM_TABLE}
            ORDER BY sort_order
        """).fetchall()
    return [dict(row) for row in rows]


def _persona_items(persona, prefix):
    return [
        persona.get(f"{prefix}_{i}", "")
        for i in range(1, 5)
        if persona.get(f"{prefix}_{i}", "")
    ]


def _render_persona_list(items, extra_class=""):
    class_name = f"persona-list {extra_class}".strip()
    item_html = "".join(f'<li>{_html(item)}</li>' for item in items)
    return f'<ul class="{class_name}">{item_html}</ul>'


def _render_personas(personas, lang="en"):
    t = lambda k: tr.get_translation(k, lang)
    radio_html = ""
    tab_html = ""
    panel_html = ""

    for index, persona in enumerate(personas, start=1):
        checked = " checked" if index == 1 else ""
        radio_html += f'<input type="radio" id="persona-{index}" name="persona-view" class="persona-radio"{checked}>'
        tab_html += (
            f'<label for="persona-{index}" class="persona-tab persona-tab-{index}">'
            f'{_html(persona["tab_label"])}</label>'
        )

        bio_items = [
            f'{t("persona_bio_age")}: {persona["age"]}',
            f'{t("persona_bio_gender")}: {persona["gender"]}',
            f'{t("persona_bio_job")}: {persona["job_title"]}',
            f'{t("persona_bio_edu")}: {persona["education"]}',
            f'{t("persona_bio_loc")}: {persona["location"]}',
            f'{t("persona_bio_exp")}: {persona["experience"]}',
            f'{t("persona_bio_project")}: {persona["current_project"]}',
        ]

        panel_html += f"""
                <div class="persona-panel persona-panel-{index}">
                    <div class="persona-card">
                        <div class="persona-image">
                            <img src="{_html(persona['image_src'])}" alt="{_html(persona['image_alt'])}">
                        </div>
                        <div class="persona-details">
                            <div class="persona-header">
                                <h3>{t("persona_prefix")}: {_html(persona['display_name'])}</h3>
                                <div class="persona-tooltip">
                                    <span class="persona-tooltip-icon">!</span>
                                    <div class="persona-tooltip-text">{_html(persona['tooltip'])}</div>
                                </div>
                            </div>
                            <div class="persona-subtitle">{_html(persona['subtitle'])}</div>
                            <div class="persona-section">
                                <h4>{t("persona_section_quote")}</h4>
                                <p class="persona-quote">"{_html(persona['quote'])}"</p>
                            </div>
                            <div class="persona-section">
                                <h4>{t("persona_section_bio")}</h4>
                                {_render_persona_list(bio_items, "persona-bio-list")}
                            </div>
                            <div class="persona-section">
                                <h4>{t("persona_section_goals")}</h4>
                                {_render_persona_list(_persona_items(persona, "goal"))}
                            </div>
                            <div class="persona-section">
                                <h4>{t("persona_section_pain")}</h4>
                                {_render_persona_list(_persona_items(persona, "pain"))}
                            </div>
                            <div class="persona-section">
                                <h4>{t("persona_section_needs")}</h4>
                                {_render_persona_list(_persona_items(persona, "need"))}
                            </div>
                            <p class="persona-motivation"><strong>{t("persona_motivation_label")}</strong> {_html(persona['motivation'])}</p>
                        </div>
                    </div>
                </div>"""

    return f"""
            <div class="persona-module">
                {radio_html}

                <div class="persona-tab-bar">
                    {tab_html}
                </div>

                {panel_html}
            </div>"""


def _render_team_members(members, lang="en"):
    if not members:
        return ""

    t = lambda k: tr.get_translation(k, lang)
    member_html = ""
    for member in members:
        member_html += (
            '<div class="about-team-member">'
            f'<span class="about-team-name">{_html(member["full_name"])}</span>'
            f'<span class="about-team-id">{t("student_id_label")}: {_html(member["student_id"])}</span>'
            '</div>'
        )

    return f"""
                    <div class="about-team-list">
                        {member_html}
                    </div>"""


# About / Mission Statement page
def get_page_html(form_data):
    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
    with open(css_file, 'r', encoding='utf-8') as f:
        css = f.read()

    lang        = (form_data.get("lang") or ["en"])[0]
    tr_         = lambda k: tr.get_translation(k, lang)
    nav_html    = nav.get_nav_html("/bao_page_1", lang=lang, form_data=form_data)
    footer_html = nav.get_footer_html(lang)
    db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'immunisation.db')
    personas_html = _render_personas(_load_personas(db), lang)
    team_members_html = _render_team_members(_load_team_members(db), lang)

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
            {personas_html}
        </section>

        <section class="about-us-section">
            <div class="about-content">
                <div class="about-image-wrapper" aria-label="Page author image">
                    <img src="/images/PageAuthor.png" alt="Page Author" class="about-image">
                </div>
                <div class="about-us-copy">
                    <h2>{tr_("about_us_title")}</h2>
                    <p>{tr_("about_us_p1")}</p>
                    <p>{tr_("about_us_p2")}</p>
                    {team_members_html}
                </div>
            </div>
        </section>
    </main>

    {footer_html}

</body>
</html>"""
