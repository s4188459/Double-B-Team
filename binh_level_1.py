import os

def get_page_html(form_data):
    print("About to return page home page...")

    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
    with open(css_file, 'r', encoding='utf-8') as f:
        css = f.read()

    page_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>ImmuniData - Home</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
</head>
<body>

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
                <a href="/" class="nav-link active">Home</a>
                <a href="#" class="nav-link">About</a>

                <!-- Data dropdown -->
                <div class="nav-dropdown-wrapper">
                    <span class="nav-dropdown-toggle">Data &#9660;</span>
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
            <div class="search-bar">
                <input type="text" class="search-input" placeholder="Search...">
                <button type="button" class="search-btn">
                    <img src="/images/search_icon_landing_page.png" alt="Search" height="22" width="22">
                </button>
            </div>

        </div>

    </header>

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

</body>
</html>"""
    return page_html
