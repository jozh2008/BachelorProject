import requests
import xml.etree.ElementTree as ET
from pprint import PrettyPrinter


class XMLParser:
    def __init__(self, url):
        self.url = url
        self.root = None

    def prepare_fetch_xml_data(self):
        response = requests.get(self.url)

        if response.status_code == 200:
            xml_content = response.json()
            return xml_content
        else:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            print(self.url)

    def fetch_xml_data(self, xml_content):
        xml_string = '\n'.join(xml_content)

        # Parse the XML string
        try:
            self.root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            self.root = None

    def find_protein_database_options(self, database_name):
        list_database = []
        if self.root is not None:
            protein_database_params = self.root.findall(f'.//param[@name="{database_name}"]')

            for param in protein_database_params:
                options_element = param.find('options')
                if options_element is not None:
                    from_data_table_value = options_element.get('from_data_table')
                    list_database.append(from_data_table_value)
                    print(f"The value of 'from_data_table' for {param} is: {from_data_table_value}")
                else:
                    print(f"No 'options' element found for {param}")
        return list_database

    def find_databases_names(self, database_name):
        options_list = []
        if self.root is not None:
            try:
                # XPath expression to find all param elements with a specific from_data_table value
                param_elements = self.root.findall(".//param")

                # Iterate through param elements
                for param_element in param_elements:
                    # Check if the param has the correct from_data_table attribute
                    options_element = param_element.find('options')
                    if options_element is not None:
                        from_data_table_value = options_element.get('from_data_table')
                        if from_data_table_value == database_name:
                            options_list.append((param_element.get("name")))
            except Exception as e:
                print(f"Error: {e}")
        return options_list

    def get_element_text(self, element_path):
        if self.root is not None:
            element = self.root.find(element_path)
            if element is not None:
                return element.text
            else:
                print(f"Element not found: {element_path}")
        else:
            print("XML data not fetched yet. Call fetch_xml_data() first.")

    def write_to_file(self, data, name):
        with open(name, 'w') as file:
            pp = PrettyPrinter(indent=4, stream=file)
            pp.pprint(data)
        file.close()
