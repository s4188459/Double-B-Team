#Students don't need to understand the implementation details here, let alone modify this code.
#File version: 2025.03.28
#Author: Gayan Wijesinghe, for questions, contact via Ms Teams.

import sqlite3
import os

import http.server
import socketserver
from urllib.parse import parse_qs, urlparse

need_debugging_help=True

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    pages={}
    def do_GET(self):
        parsed_url = urlparse(self.path)
        debugging_helper(f"A web browser wants to GET the following: {parsed_url.path}")
        if parsed_url.path in MyRequestHandler.pages:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            query = parsed_url.query
            form_data = parse_qs(query)
            debugging_helper(f"\tReceived following data with GET request: {form_data}")
            
            html_content = MyRequestHandler.pages[parsed_url.path].get_page_html(form_data)
            
            self.wfile.write(html_content.encode('utf-8'))            
        else:
            # Let the server handle static files (like images, .html files)
            super().do_GET()
            

def host_site():
    # Set the port
    PORT = 80

    # Create the HTTP server
    with socketserver.TCPServer(("", PORT), MyRequestHandler) as httpd:
        print("Using your favourite browser, go to:\n")
        if (PORT==80):
            print("http://localhost")
        print(f"or\nhttp://localhost:{PORT}\n")
        httpd.serve_forever()
        
        
def get_results_from_query(database,query):
    debugging_helper("\n------------------------")
    debugging_helper("Opening database \""+database+"\"... ")
    connection = sqlite3.connect(database)
    cursor=connection.cursor()
    debugging_helper("done\n")
    debugging_helper("Executing query \""+query+"\"... ")
    cursor.execute(query)
    debugging_helper("done\n")
    debugging_helper("Fetching results...\n")
    results = cursor.fetchall();
    debugging_helper(results)
    debugging_helper("\n------------------------")
    return results

def debugging_helper(message):
    if (need_debugging_help):
        print(message,)
