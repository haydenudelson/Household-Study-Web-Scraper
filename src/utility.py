from bs4 import BeautifulSoup
import requests

def clean_text(txt):
    res = txt.strip()
    return res

def get_soup(url):
    return BeautifulSoup(requests.get(url).content, features="xml")
