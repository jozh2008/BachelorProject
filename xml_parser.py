import xml.etree.ElementTree as ET


class XMLParser:
    def __init__(self):
        """
        Initialize the XMLParser class.
        """
        self.root = None

    def fetch_xml_data(self, xml_content):
        """
        Parse XML content and set the root element.

        Args:
            xml_content (str): The XML content to be parsed.

        Returns:
            None
        """
        xml_string = xml_content

        # Parse the XML string
        try:
            self.root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
            self.root = None

    def find_databases_names(self, database_name):
        """
        Find param elements with a specific 'from_data_table' attribute value.

        Args:
            database_name (str): The value to match in the 'from_data_table' attribute.

        Returns:
            list: A list of param element names matching the specified 'from_data_table' value.
        """
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
                            options_list.append(param_element.get("name"))
            except Exception as e:
                print(f"Error: {e}")
        return options_list
