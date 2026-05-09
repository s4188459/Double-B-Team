import os
import re
import pyhtml

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'immunisation.db')

PAGE_MAP = {
    "Vaccination Data Explorer":                         "/binh_page_2",
    "Vaccination Improvement Explorer":                  "/binh_page_3",
    "Infection Data by Economic Status Explorer":        "/bao_page_2",
    "Infection Improvement by Economic Status Explorer": "/bao_page_3",
}

def get_page_html(form_data):
    q = (form_data.get("q") or [""])[0].strip()
    redirect = _resolve(q)
    return f"""<!DOCTYPE html>
<html><head>
<meta http-equiv="refresh" content="0;url={redirect}">
<title>Redirecting...</title>
</head><body></body></html>"""


def _esc(s):
    return s.replace("'", "''")


def _resolve(q):
    for page_name, base_url in PAGE_MAP.items():
        marker = f" in {page_name}"
        if q.endswith(marker):
            entity = q[:-len(marker)]
            return _find_entity(entity, base_url)
    return "/"


def _find_entity(entity, base_url):
    safe = _esc(entity)

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
        display = re.sub(r'-containing vaccine', '',
                         full_name.split(",")[0], flags=re.IGNORECASE).strip()
        if display == entity:
            return f"{base_url}?antigen={aid}"

    rows = pyhtml.get_results_from_query(DB,
        f"SELECT id FROM Infection_Type WHERE description = '{safe}'")
    if rows:
        return f"{base_url}?infection={rows[0][0]}"

    return base_url
