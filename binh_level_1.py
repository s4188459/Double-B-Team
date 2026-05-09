import os

def get_page_html(form_data):
    print("About to return page home page...")

    # TODO: Replace with DB queries from immunisation.db
    stat1_countries = ""
    stat2_coverage = ""
    stat3_high_coverage = ""
    stat4_doses = ""

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

    <!-- Global Immunization Snapshot -->
    <section class="snapshot-section">
        <div class="snapshot-container">

            <div class="snapshot-header">
                <h2 class="snapshot-title">Global Immunization Snapshot (2000 - 2025)</h2>
                <div class="methodology-wrapper">
                    <button class="methodology-btn" onclick="toggleMethodology(this)">
                        View methodology
                        <img src="/images/icon_for_information.png" alt="info" class="btn-icon">
                    </button>
                    <div class="methodology-popup" id="methodologyPopup">
                        <p><strong>Total Countries Monitored:</strong> Represents the total number of distinct nations and territories reporting data within the selected timeframe and regions.</p>
                        <p><strong>Average Coverage:</strong> Calculated as the mean vaccination coverage rate across all antigens currently selected in the dataset.</p>
                        <p><strong>High Coverage Target:</strong> Indicates the count of countries that have successfully achieved a minimum of 90% coverage simultaneously for every selected antigen.</p>
                        <p><strong>Cumulative Doses:</strong> The aggregate sum of all vaccine doses administered and officially recorded for the specified antigens throughout the entire tracked period.</p>
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
                        <a href="#" class="card-link">View details &rarr;</a>
                    </div>
                </div>

                <div class="stat-card">
                    <img src="/images/2nd card.png" alt="Average Coverage" class="card-icon">
                    <div class="card-info">
                        <div class="card-number">{stat2_coverage}</div>
                        <div class="card-label">Average<br>Coverage</div>
                        <a href="#" class="card-link">View details &rarr;</a>
                    </div>
                </div>

                <div class="stat-card">
                    <img src="/images/3rd card.png" alt="High Coverage Countries" class="card-icon">
                    <div class="card-info">
                        <div class="card-number">{stat3_high_coverage}</div>
                        <div class="card-label">Countries</div>
                        <div class="card-desc">Achieved &ge;90% coverage across ALL antigens in 2024</div>
                        <a href="#" class="card-link">View details &rarr;</a>
                    </div>
                </div>

                <div class="stat-card">
                    <img src="/images/4th card.png" alt="Doses" class="card-icon">
                    <div class="card-info">
                        <div class="card-number">{stat4_doses}</div>
                        <div class="card-label">Doses</div>
                        <div class="card-desc">Recorded across 5 antigens over 25 years</div>
                        <a href="#" class="card-link">View details &rarr;</a>
                    </div>
                </div>

            </div>
        </div>
    </section>

    <!-- Disease Covered -->
    <section class="disease-section">
        <h2 class="disease-title">Disease Covered</h2>
        <div class="disease-grid">
            <div class="disease-card">
                <img src="/images/Measles disease icon.png" alt="Measles" class="disease-icon">
                <span class="disease-name">Measles</span>
            </div>
            <div class="disease-card">
                <img src="/images/Polio disease icon.png" alt="Polio" class="disease-icon">
                <span class="disease-name">Polio</span>
            </div>
            <div class="disease-card">
                <img src="/images/Diptheria disease icon.png" alt="Diphtheria" class="disease-icon">
                <span class="disease-name">Diptheria</span>
            </div>
            <div class="disease-card">
                <img src="/images/Pertussis disease icon.png" alt="Pertussis" class="disease-icon">
                <span class="disease-name">Pertussis</span>
            </div>
            <div class="disease-card">
                <img src="/images/Tentanus disease icon.png" alt="Tetanus" class="disease-icon">
                <span class="disease-name">Tetanus</span>
            </div>
            <div class="disease-card">
                <img src="/images/More disease icon.png" alt="More disease" class="disease-icon">
                <span class="disease-name">More disease</span>
            </div>
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

    <script>
    function toggleMethodology(btn) {{
        var popup = document.getElementById('methodologyPopup');
        popup.classList.toggle('active');
    }}
    document.addEventListener('click', function(e) {{
        var wrapper = document.querySelector('.methodology-wrapper');
        if (!wrapper.contains(e.target)) {{
            document.getElementById('methodologyPopup').classList.remove('active');
        }}
    }});
    </script>

</body>
</html>"""
    return page_html
