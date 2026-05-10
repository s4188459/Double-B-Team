import os
import re
import pyhtml

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'immunisation.db')

_DATA_PAGES = {"/binh_page_2", "/binh_page_3", "/bao_page_2", "/bao_page_3"}

_PAGE_MAP = {
    "Vaccination Data Explorer":                         "/binh_page_2",
    "Vaccination Improvement Explorer":                  "/binh_page_3",
    "Infection Data by Economic Status Explorer":        "/bao_page_2",
    "Infection Improvement by Economic Status Explorer": "/bao_page_3",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def _html_esc(s):
    return s.replace('&', '&amp;').replace('"', '&quot;')

def _antigen_display_name(full_name):
    name = full_name.split(",")[0]
    name = re.sub(r'-containing vaccine', '', name, flags=re.IGNORECASE).strip()
    return name

def _esc_sql(s):
    return s.replace("'", "''")

# ── navigation bar ────────────────────────────────────────────────────────────

def get_nav_html(active_page="/"):
    countries = pyhtml.get_results_from_query(DB, "SELECT CountryID, name FROM Country ORDER BY name")
    regions   = pyhtml.get_results_from_query(DB, "SELECT RegionID, region FROM Region ORDER BY region")
    antigens  = pyhtml.get_results_from_query(DB, "SELECT AntigenID, name FROM Antigen ORDER BY AntigenID")
    inf_types = pyhtml.get_results_from_query(DB, "SELECT id, description FROM Infection_Type ORDER BY description")

    datalist_opts = []
    for _, cname in countries:
        e = _html_esc(cname)
        datalist_opts.append(f'<option value="{e} in Vaccination Data Explorer">')
        datalist_opts.append(f'<option value="{e} in Vaccination Improvement Explorer">')
    for _, rname in regions:
        e = _html_esc(rname)
        datalist_opts.append(f'<option value="{e} in Vaccination Data Explorer">')
        datalist_opts.append(f'<option value="{e} in Vaccination Improvement Explorer">')
    for _, full_name in antigens:
        e = _html_esc(_antigen_display_name(full_name))
        datalist_opts.append(f'<option value="{e} in Vaccination Data Explorer">')
        datalist_opts.append(f'<option value="{e} in Vaccination Improvement Explorer">')
    for _, inf_name in inf_types:
        e = _html_esc(inf_name)
        datalist_opts.append(f'<option value="{e} in Infection Data by Economic Status Explorer">')
        datalist_opts.append(f'<option value="{e} in Infection Improvement by Economic Status Explorer">')
    datalist_html = '\n'.join(datalist_opts)

    home_class = "nav-link active" if active_page == "/" else "nav-link"
    data_class = "nav-dropdown-toggle active" if active_page in _DATA_PAGES else "nav-dropdown-toggle"

    return f"""
    <!-- Top language bar -->
    <div class="top-bar">
        <a href="#">English</a>
        <span class="divider">|</span>
        <a href="#">Vietnamese</a>
    </div>

    <!-- Main header -->
    <header class="main-header">

        <!-- Logo: far left -->
        <a href="/" class="logo">
            <img src="/images/Logo.jpeg" alt="ImmuniData" height="110">
        </a>

        <!-- Nav + Search grouped to the right -->
        <div class="nav-search-group">

            <nav class="main-nav">
                <a href="/" class="{home_class}">Home</a>
                <a href="#" class="nav-link">About</a>

                <!-- Data dropdown -->
                <div class="nav-dropdown-wrapper">
                    <span class="{data_class}">Data &#9660;</span>
                    <div class="dropdown-menu">
                        <a href="/binh_page_2">Vaccination Data Explorer</a>
                        <a href="/binh_page_3">Vaccination Improvement Explorer</a>
                        <a href="/bao_page_2">Infection Data by Economic Status Explorer</a>
                        <a href="/bao_page_3">Infection Improvement by Economic Status Explorer</a>
                    </div>
                </div>

                <a href="#" class="nav-link">Resources</a>
                <a href="#" class="nav-link">Help</a>
            </nav>

            <!-- Search bar -->
            <form class="search-bar" method="GET" action="/search">
                <input type="text" class="search-input" name="q" list="search-suggestions" autocomplete="off" placeholder="Search...">
                <button type="submit" class="search-btn">
                    <img src="/images/search_icon_landing_page.png" alt="Search" height="22" width="22">
                </button>
            </form>
            <datalist id="search-suggestions">
                {datalist_html}
            </datalist>

        </div>

    </header>"""

# ── footer ────────────────────────────────────────────────────────────────────

def get_footer_html():
    return """
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
    </footer>"""

# ── search redirect ───────────────────────────────────────────────────────────

def get_page_html(form_data):
    q = (form_data.get("q") or [""])[0].strip()
    redirect = _resolve(q)
    return f"""<!DOCTYPE html>
<html><head>
<meta http-equiv="refresh" content="0;url={redirect}">
<title>Redirecting...</title>
</head><body></body></html>"""


def _resolve(q):
    for page_name, base_url in _PAGE_MAP.items():
        marker = f" in {page_name}"
        if q.endswith(marker):
            entity = q[:-len(marker)]
            return _find_entity(entity, base_url)
    return "/"


def _find_entity(entity, base_url):
    safe = _esc_sql(entity)

    rows = pyhtml.get_results_from_query(DB,
        f"SELECT CountryID FROM Country WHERE name = '{safe}'")
    if rows:
        return f"{base_url}?country={rows[0][0]}"

    rows = pyhtml.get_results_from_query(DB,
        f"SELECT RegionID FROM Region WHERE region = '{safe}'")
    if rows:
        return f"{base_url}?region={rows[0][0]}"

    rows = pyhtml.get_results_from_query(DB, "SELECT AntigenID, name FROM Antigen")
    for aid, full_name in rows:
        if _antigen_display_name(full_name) == entity:
            return f"{base_url}?antigen={aid}"

    rows = pyhtml.get_results_from_query(DB,
        f"SELECT id FROM Infection_Type WHERE description = '{safe}'")
    if rows:
        return f"{base_url}?infection={rows[0][0]}"

    return base_url
