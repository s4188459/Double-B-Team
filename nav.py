import os
import urllib.parse
import pyhtml
import translations as tr
from faq_widget import FAQChatWidget

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'immunisation.db')

# pages that live under the Data dropdown — used to keep it highlighted when active
_DATA_PAGES = {"/binh_page_2", "/binh_page_3", "/bao_page_2", "/bao_page_3"}

# breadcrumb trail per page; None href means it shows as plain text, not a link
_BREADCRUMBS = {
    "/bao_page_1":  [("Home", "/"),              ("About", None)],
    "/binh_page_2": [("Home", "/"), ("Data", None), ("Vaccination Data Explorer", None)],
    "/binh_page_3": [("Home", "/"), ("Data", None), ("Vaccination Improvement Explorer", None)],
    "/bao_page_2":  [("Home", "/"), ("Data", None), ("Infection Data by Economic Status Explorer", None)],
    "/bao_page_3":  [("Home", "/"), ("Data", None), ("Countries Above Global Infection Rate", None)],
}

# maps English breadcrumb labels to translation keys in translations.TRANSLATIONS
_BREADCRUMB_KEY = {
    "Home":                                                "bc_home",
    "About":                                               "bc_about",
    "Data":                                                "bc_data",
    "Vaccination Data Explorer":                           "page_vacc_explorer",
    "Vaccination Improvement Explorer":                    "page_vacc_improvement",
    "Infection Data by Economic Status Explorer":          "page_inf_explorer",
    "Countries Above Global Infection Rate":               "page_inf_improvement",
}

# renders the "Home > Data > Page Name" trail shown below the header
def _build_breadcrumb(active_page, lang="en", lang_suffix=""):
    crumbs = _BREADCRUMBS.get(active_page)
    if not crumbs:
        return ""
    parts = []
    for i, (label, href) in enumerate(crumbs):
        is_last = (i == len(crumbs) - 1)
        translated = tr.get_translation(_BREADCRUMB_KEY.get(label, label), lang)
        dest = (href + lang_suffix) if href and lang_suffix else href
        if is_last:
            parts.append(f'<span class="breadcrumb-current">{translated}</span>')
        elif dest:
            parts.append(f'<a href="{dest}" class="breadcrumb-link">{translated}</a>')
        else:
            parts.append(f'<span class="breadcrumb-link">{translated}</span>')
        if not is_last:
            parts.append('<span class="breadcrumb-sep">&rsaquo;</span>')
    return f'<nav class="breadcrumb">{"".join(parts)}</nav>'

# builds the full page header: language bar, logo, nav links, search box, and breadcrumb
# lang:      active language code ("en", "vi", "it", "fr", "de")
# form_data: raw parse_qs dict from the current request — used to build language-switch URLs
#            that preserve all current filter state when the user switches language
def get_nav_html(active_page="/", lang="en", form_data=None):
    # URL suffix to append when navigating to other pages so lang persists
    lang_suffix = f"?lang={lang}" if lang and lang != "en" else ""

    # language-switch URL: keeps all current filter params, replaces only lang
    def lang_url(target_lang):
        if form_data:
            params = {k: v[0] for k, v in form_data.items() if v and k != "lang"}
            if target_lang != "en":
                params["lang"] = target_lang
            qs = urllib.parse.urlencode(params)
            return f"{active_page}?{qs}" if qs else active_page
        if target_lang != "en":
            return f"{active_page}?lang={target_lang}"
        return active_page

    # nav-link href: plain path + lang suffix for non-English
    def nh(path):
        return path + lang_suffix if lang_suffix else path

    # which nav item gets the active highlight based on the current page
    home_class  = "nav-link active" if active_page == "/" else "nav-link"
    about_class = "nav-link active" if active_page == "/bao_page_1" else "nav-link"
    data_class  = "nav-dropdown-toggle active" if active_page in _DATA_PAGES else "nav-dropdown-toggle"

    # shorthand for Data dropdown items — adds active class when this is the current page
    def _dd(href, label_key):
        cls = ' class="active"' if active_page == href else ''
        label = tr.get_translation(label_key, lang)
        return f'<a href="{nh(href)}"{cls}>{label}</a>'

    # language bar — active language gets .active-lang class
    lang_items = []
    for code, display in tr.LANGUAGES.items():
        cls = ' class="active-lang"' if code == lang else ''
        lang_items.append(f'<a href="{lang_url(code)}"{cls}>{display}</a>')
    lang_bar = '<span class="divider">|</span>'.join(lang_items)

    # translated labels
    t_home      = tr.get_translation("nav_home",      lang)
    t_about     = tr.get_translation("nav_about",     lang)
    t_data      = tr.get_translation("nav_data",      lang)

    return f"""
    <!-- Top language bar -->
    <div class="top-bar">
        {lang_bar}
    </div>

    <!-- Main header -->
    <header class="main-header">

        <!-- Logo: far left -->
        <a href="{nh("/")}" class="logo">
            <img src="/images/Logo.jpeg" alt="ImmuniData" height="110">
        </a>

        <!-- Nav + Search grouped to the right -->
        <div class="nav-search-group">

            <nav class="main-nav">
                <a href="{nh("/")}" class="{home_class}">{t_home}</a>
                <a href="{nh("/bao_page_1")}" class="{about_class}">{t_about}</a>

                <!-- Data dropdown -->
                <div class="nav-dropdown-wrapper">
                    <span class="{data_class}">{t_data} &#9660;</span>
                    <div class="dropdown-menu">
                        {_dd("/binh_page_2", "page_vacc_explorer")}
                        {_dd("/binh_page_3", "page_vacc_improvement")}
                        {_dd("/bao_page_2",  "page_inf_explorer")}
                        {_dd("/bao_page_3",  "page_inf_improvement")}
                    </div>
                </div>
            </nav>

        </div>

    </header>
    {_build_breadcrumb(active_page, lang, lang_suffix)}

    {FAQChatWidget().render(lang=lang)}
    """

# static footer with brand info, quick links, and legal text
def get_footer_html(lang="en"):
    t = lambda k: tr.get_translation(k, lang)
    ls = f"?lang={lang}" if lang != "en" else ""

    return f"""
    <!-- Footer -->
    <footer class="site-footer">
        <div class="footer-main">

            <!-- Brand column -->
            <div class="footer-brand">
                <div class="footer-brand-title">{t("footer_brand_title")}</div>
                <p class="footer-brand-desc">{t("footer_brand_desc")}</p>
                <div class="footer-contacts">
                    <a href="mailto:ngodinhbinh1504@gmail.com" class="footer-contact-icon" title="Email">
                        <img src="/images/Mail icon.png" alt="Email">
                    </a>
                    <a href="tel:+84967502748" class="footer-contact-icon" title="Phone">
                        <img src="/images/phone icon.png" alt="Phone">
                    </a>
                    <a href="https://www.google.com/maps/search/RMIT+University+Vietnam+702+Nguyen+Van+Linh+Ho+Chi+Minh" target="_blank" class="footer-contact-icon" title="Location">
                        <img src="/images/location icon.png" alt="Location">
                    </a>
                    <a href="https://www.linkedin.com/in/ngo-dinn-binh-9469243b3/" target="_blank" class="footer-contact-icon" title="LinkedIn">
                        <img src="/images/LinkedIn icon.png" alt="LinkedIn">
                    </a>
                </div>
            </div>

            <!-- About column -->
            <div class="footer-col">
                <div class="footer-col-title">{t("footer_col_about")}</div>
                <a href="/bao_page_1{ls}" class="footer-link">{t("footer_mission")}</a>
                <a href="#" class="footer-link">{t("footer_personas")}</a>
                <a href="#" class="footer-link">{t("footer_team")}</a>
            </div>

            <!-- Focus view column -->
            <div class="footer-col">
                <div class="footer-col-title">{t("footer_col_focus")}</div>
                <a href="/binh_page_2{ls}" class="footer-link">{t("footer_country_region")}</a>
                <a href="/bao_page_2{ls}" class="footer-link">{t("footer_economic")}</a>
            </div>

            <!-- In-depth analysis column -->
            <div class="footer-col">
                <div class="footer-col-title">{t("footer_col_analysis")}</div>
                <a href="/binh_page_3{ls}" class="footer-link">{t("footer_country_region")}</a>
                <a href="/bao_page_3{ls}" class="footer-link">{t("footer_economic")}</a>
            </div>


        </div>
    </footer>"""

