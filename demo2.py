import os
import socketserver
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pyhtml
import binh_level_1
import binh_level_2
import binh_level_3
import bao_level_1
import bao_level_2
import bao_level_3


PORT = 8000

pyhtml.need_debugging_help = False

pyhtml.MyRequestHandler.pages["/"] = binh_level_1
pyhtml.MyRequestHandler.pages["/binh_page_2"] = binh_level_2
pyhtml.MyRequestHandler.pages["/binh_page_3"] = binh_level_3
pyhtml.MyRequestHandler.pages["/bao_page_1"] = bao_level_1
pyhtml.MyRequestHandler.pages["/bao_page_2"] = bao_level_2
pyhtml.MyRequestHandler.pages["/bao_page_3"] = bao_level_3

socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer(("", PORT), pyhtml.MyRequestHandler) as httpd:
    print(f"Serving on http://localhost:{PORT}")
    httpd.serve_forever()
