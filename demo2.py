import pyhtml
import binh_level_1
import binh_level_2
import binh_level_3
import bao_level_1
import bao_level_2
import bao_level_3
import search

#In the studio project, the other team members would have their pages imported like this.
# import student_b_level_1
# import student_b_level_2
# import student_b_level_3

# import student_c_level_1
# import student_c_level_2
# import student_c_level_3

pyhtml.need_debugging_help=True

#All pages that you want on the site need to be added as below
pyhtml.MyRequestHandler.pages["/"]=binh_level_1; 
pyhtml.MyRequestHandler.pages["/binh_page_2"]=binh_level_2; 
pyhtml.MyRequestHandler.pages["/binh_page_3"]=binh_level_3; 

pyhtml.MyRequestHandler.pages["/bao_page_1"]=bao_level_1;
pyhtml.MyRequestHandler.pages["/bao_page_2"]=bao_level_2;
pyhtml.MyRequestHandler.pages["/bao_page_3"]=bao_level_3;

pyhtml.MyRequestHandler.pages["/search"]=search;

#Host the site!
pyhtml.host_site()