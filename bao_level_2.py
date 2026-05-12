import os
import pyhtml
import nav

def get_page_html(form_data):
    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'style.css')
    with open(css_file, 'r', encoding='utf-8') as f:
        css = f.read()

    nav_html    = nav.get_nav_html("/bao_page_2")
    footer_html = nav.get_footer_html()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>ImmuniData - Infection Data by Economic Status Explorer</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
</head>
<body>

    {nav_html}

    <main style="min-height:60vh; padding:60px 80px;">
        <h1>Infection Data by Economic Status Explorer</h1>
    </main>

    {footer_html}

</body>
</html>"""
