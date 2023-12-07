from galaxytools import *
from pprint import pprint
from bs4 import BeautifulSoup
import requests
import pyperclip
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from urllib.request import urlopen



from selenium import webdriver

driver = webdriver.Chrome()

# Open a webpage


from selenium.webdriver.common.by import By
url = "https://usegalaxy.eu/?tool_id=toolshed.g2.bx.psu.edu%2Frepos%2Fiuc%2Fhumann%2Fhumann%2F3.8%2Bgalaxy0&version=latest"
#url ="https://toolshed.g2.bx.psu.edu/view/iuc/humann/fc6c328c292f"
#url ="https://toolshed.g2.bx.psu.edu/repository/view_repository?id=56429c40581f1d7b&amp;changeset_revision=fc6c328c292f&amp;message=&amp;status=done"
# Set up the WebDriver (in this case, using Chrome)
driver = webdriver.Chrome()

# Navigate to a webpage
driver.get(url)
driver.implicitly_wait(10)

# Get the updated HTML content after dynamic loading
updated_html = driver.page_source

# Close the browser
driver.quit()

print(updated_html)
with open("webpage_content3.html", "w", encoding="utf-8") as file:
        file.write(updated_html)
