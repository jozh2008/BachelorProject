import json


class GalaxyToolRunner:
    def __init__(self, gi, history_id):
        """
        Initialize the GalaxyToolRunner class.

        Args:
            gi: An instance of the Galaxy API object.
            history_id (str): The ID of the Galaxy history.
        """
        self.gi = gi
        self.history_id = history_id
        self.dictionary = {}

    def fetch_dataset_details(self, item):
        """
        Fetch and process details of a dataset in the Galaxy history.

        This method retrieves details of a dataset from the Galaxy history, extracts relevant
        information such as the tool ID and parameters, and stores them in the class dictionary.

        Args:
            item (dict): Details of the dataset.

        Returns:
            tuple: A tuple containing the tool ID and parameters.
        """
        item_type = item['type']

        if item_type == "file":
            item_id = item['id']
            dataset_details = self.gi.histories.show_dataset_provenance(history_id=self.history_id, dataset_id=item_id)

            tool_id = dataset_details["tool_id"]
            if tool_id != '__DATA_FETCH__':
                parameters = dataset_details.get('parameters', {})
                keys_to_remove = []

                for key, value in parameters.items():
                    if "|" in key:
                        keys_to_remove.append(key)
                    if value is not None:
                        try:
                            if isinstance(value, dict) or isinstance(value, list):
                                parsed_dict = value
                            else:
                                parsed_dict = json.loads(value)
                                parameters[key] = parsed_dict
                        except json.JSONDecodeError:
                            print("The original string is not a valid JSON format. Perform alternative actions here.")

                for key_to_remove in keys_to_remove:
                    parameters.pop(key_to_remove, None)
                self.replace_uuid_with_src(parameters)
                self.dictionary[tool_id] = parameters
        return tool_id, parameters

    def replace_uuid_with_src(self, input_dict):
        """
        Recursively replace 'uuid' key with 'src': 'hda' in a dictionary.

        Args:
            input_dict (dict or list): The dictionary or list to process.

        Returns:
            dict or list: The processed dictionary or list.
        """
        if isinstance(input_dict, dict):
            # Check if the dictionary has 'uuid' key and replace it with 'src': 'hda'
            if 'uuid' in input_dict:
                input_dict = {'src': 'hda', 'id': input_dict['id']}
            # Recursively process values
            else:
                for key, value in input_dict.items():
                    input_dict[key] = self.replace_uuid_with_src(value)
        elif isinstance(input_dict, list):
            # Recursively process list elements
            input_dict = [self.replace_uuid_with_src(item) for item in input_dict]
        return input_dict
