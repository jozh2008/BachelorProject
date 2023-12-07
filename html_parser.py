from bs4 import BeautifulSoup
import requests
import json
from urllib.parse import urlparse
from pprint import pprint, PrettyPrinter
server = 'https://usegalaxy.eu/'
# api kex of account
api_key = 'mYjQOJmxwALJESXyMerBZpfuIoA4JDI'

class HTMLParser:
    def __init__(self, url):
        self.url = url
        self.load_html()

    def load_html(self):
        # Make an HTTP request to the URL
        response = requests.get(self.url)
        #print(self.url)
        if response.status_code == 200:
            # Parse the HTML content with BeautifulSoup
            self.soup = BeautifulSoup(response.text, 'lxml')
        else:
            raise Exception(f"Failed to retrieve HTML content. Status code: {response.status_code}")

    def get_iframe_src(self):
        # Find the iframe element
        iframe = self.soup.find('iframe')

        # If an iframe is found, return its source URL
        if iframe:
            return iframe.get('src')
        else:
            return None

    def find_development_repository_href(self):
        # Find all div elements with the specified class
        development_repo_divs = self.soup.find_all('div', class_ = "form-row")

        # Iterate through the found divs
        for development_repo_div in development_repo_divs:
            # Check if the div contains the title "Development repository"
            if 'Development repository:' in development_repo_div.text:
                # Extract the href attribute from the anchor tag within the div
                development_repo_link = development_repo_div.find('a')
                if development_repo_link:
                    return development_repo_link.get('href')
                else:
                    print("No anchor tag found within the 'Development repository' div.")
                break

        # Return None if the development repository href is not found
        return None
    
    def get_github_resource(self):
        try:
            response = requests.get(self.url)
            #print(response)
            response.raise_for_status()
            #self.write_to_fil(, "github.txt")
            resource_info = response.json()
            #resource_info = response.text()
            #pprint(resource_info)
           
            return resource_info
        except requests.exceptions.RequestException as e:
            print(f"Error fetching GitHub resource information: {e}")
            return None
    
    def write_to_file(self, data, name):
        with open(name, 'w') as file:
            pp = PrettyPrinter(indent=4, stream=file)
            pp.pprint(data)
        file.close()


