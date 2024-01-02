import subprocess
from bs4 import BeautifulSoup
class HTMLContentExtractor:
    def __init__(self, javascript_file='captureToolSource.js'):
        self.javascript_file = javascript_file
        self.html_content = None

    def capture_html_content(self, url):
        try:
            result_from_js = subprocess.check_output(['node', self.javascript_file, url], text=True)
            self.html_content = result_from_js
        except subprocess.CalledProcessError as e:
            print(f'Error running JavaScript code: {e}')

    def extract_and_prettify_xml(self, class_name='language-xml'):
        if self.html_content:
            soup = BeautifulSoup(self.html_content, 'html.parser')
            pre_element = soup.find('pre', class_=class_name)

            if pre_element:
                xml_code = pre_element.text.strip()
                formatted_xml = BeautifulSoup(xml_code, 'xml').prettify()
                return formatted_xml
            else:
                print(f'No element with class "{class_name}" found.')
        else:
            print('HTML content not captured. Run capture_html_content() first.')

# Example usage
"""
custom_url = 'https://usegalaxy.eu/root?tool_id=toolshed.g2.bx.psu.edu%2Frepos%2Frnateam%2Fsortmerna%2Fbg_sortmerna%2F2.1b.6'           
html_extractor = HTMLContentExtractor()
html_extractor.capture_html_content(custom_url)

formatted_xml = html_extractor.extract_and_prettify_xml()

if formatted_xml:
    print('Formatted XML:')
    print(formatted_xml)
"""
