from bs4 import BeautifulSoup
import subprocess


class HTMLContentExtractor:
    def __init__(self, javascript_file='captureToolSource.js'):
        """
        Initialize the HTMLContentExtractor class.

        Args:
            javascript_file (str): The file containing JavaScript code for capturing HTML content.
        """
        self.javascript_file = javascript_file
        self.html_content = None

    def capture_html_content(self, url):
        """
        Capture HTML content from a specified URL using a JavaScript file.

        Args:
            url (str): The URL from which to capture HTML content.

        Returns:
            None
        """
        try:
            result_from_js = subprocess.check_output(['node', self.javascript_file, url], text=True)
            self.html_content = result_from_js
        except subprocess.CalledProcessError as e:
            print(f'Error running JavaScript code: {e}')

    def extract_and_prettify_xml(self, class_name='language-xml'):
        """
        Extract XML content with a specific class from captured HTML and prettify it.

        Args:
            class_name (str): The class name of the HTML element containing XML content.

        Returns:
            str: Prettified XML content.
        """
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
