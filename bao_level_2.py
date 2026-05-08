import pyhtml
def get_page_html(form_data):
    print("About to return page 2")
    
    page_html=f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Bao Page 2</title>
    </head>
    <body>
        <h1>Welcome to Bao Page 2</h1>
    </body>
    </html>
    """
    return page_html