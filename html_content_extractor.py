from bs4 import BeautifulSoup
import requests


class HTMLContentExtractor:
    def __init__(self):
        """
        Initialize the HTMLContentExtractor class.

        """
        self.html_content = None

    def capture_html_content(self, url):
        """
        Capture HTML content from the specified URL.

        Parameters:
        - url (str): The URL from which to capture HTML content.

        Raises:
        - requests.exceptions.RequestException: If there is an error while making the request.
        """

        try:
            # Make a GET request to the specified URL
            response = requests.get(url=url)

            # Check if the request was successful (status code 200)
            response.raise_for_status()

            # Assign the HTML content to the instance variable
            self.html_content = response.text
        except requests.exceptions.RequestException as e:
            # Handle any request-related exceptions
            print(f'Error making request: {e}')

    def extract_and_prettify_xml(self, class_name='language-xml'):
        """
        Extract XML content with a specific class from captured HTML and prettify it.

        Args:
            class_name (str): The class name of the HTML element containing XML content.

        Returns:
            str: Prettified XML content.
        """
        if self.html_content:
            soup = BeautifulSoup(self.html_content, 'xml')
            if soup:
                xml_code = soup.prettify()

                return xml_code
            else:
                print(f'No element with class "{class_name}" found.')
        else:
            print('HTML content not captured. Run capture_html_content() first.')
