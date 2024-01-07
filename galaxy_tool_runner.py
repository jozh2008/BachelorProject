import json
from pprint import pprint

class GalaxyToolRunner:
    def __init__(self, gi, history_id):
        self.gi = gi
        self.history_id = history_id
        self.dictionary = {}

    def fetch_dataset_details(self, item):
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
        return (tool_id, parameters)

    def replace_uuid_with_src(self, input_dict):
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
            input_dict = [self. replace_uuid_with_src(item) for item in input_dict]
        return input_dict

    def run_tools_on_datasets(self):
        for key, value in self.dictionary.items():
            if key != '__DATA_FETCH__':
                try:
                    # Try running the tool with a specific input format ("21.01")
                    result = self.gi.tools.run_tool(history_id=self.history_id, tool_id=key, tool_inputs=value, input_format="21.01")
                    pprint(result)
                except Exception as e:
                    print(f"Exception when running tool '{key}': {e}")
                    # Optionally, log the exception for more detailed analysis
                    # logging.exception(f"Exception when running tool '{key}': {e}")
                    # If you still want to proceed, run the tool without specifying the input format
                    result = self.gi.tools.run_tool(history_id=self.history_id, tool_id=key, tool_inputs=value)
                    pprint(result)


# Example usage:
# gi and history_id should be defined before creating an instance of GalaxyToolRunner
# gt_runner = GalaxyToolRunner(gi, history_id)
# items = gi.histories.show_history(history_id, contents=True, deleted=False, visible=True)
# for item in items:
#     gt_runner.fetch_dataset_details(item)
# gt_runner.run_tools_on_datasets()
