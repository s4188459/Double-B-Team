import os
import re
import pyhtml

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'immunisation.db')

_DATA_PAGES = {"/binh_page_2", "/binh_page_3", "/bao_page_2", "/bao_page_3"}

def _html_esc(s):
    return s.replace('&', '&amp;').replace('"', '&quot;')

def _antigen_display_name(full_name):
    name = full_name.split(",")[0]
    name = re.sub(r'-containing vaccine', '', name, flags=re.IGNORECASE).strip()
    return name

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
