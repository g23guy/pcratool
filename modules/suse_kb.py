# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#-*- coding: utf-8 -*-
'''
Search SUSE KB from commandline
'''
__author__        = 'Raine Curtis <raine.curtis@suse.com>'
__date_modified__ = '2025-08-15'
__version__       = '1.1_dev1'

import requests
import urllib.parse
from bs4 import BeautifulSoup

# Globals
kb_server = "https://www.suse.com"

def search_kb(product, search_str='', num_results=0):
    """ 
    Search KB
    """
    tids  = {}

    URL = "{}/support/kb/?id={}&q={}".format(kb_server, urllib.parse.quote(product), urllib.parse.quote(search_str))
    #print(URL)
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    kbs = soup.find("div", class_="result-table").find_all('a')
    i = 0
    for kb in kbs:
        try:
            i += 1
            kb_tid = kb.find('span').text.strip('(').strip(')')
            kb_title = kb.text
            kb_url = kb_server + kb.get('href')
            tid = { i : {
                "kb_tid": kb_tid,
                "kb_title": kb_title,
                "kb_url": kb_url,
                }
            }
            tids.update(tid)
            if num_results > 0:
                if i >= num_results:
                    break
        except Exception as e:
            print("Error processing KB entry {}: {}".format(i, e))
    return tids


