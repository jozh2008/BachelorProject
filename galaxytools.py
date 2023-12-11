from bioblend import galaxy
from bioblend import ConnectionError
from pprint import pprint, PrettyPrinter
import re
import time
import json
import copy
from itertools import product
from html_parser import HTMLParser
from xml_parser import XMLParser
from datetime import datetime
from typing import (
    List,
    Dict,
    Optional,
    Any
)


class Tool:
    def __init__(self, server: str, api_key: str) -> None:
        self.gi = galaxy.GalaxyInstance(url=server, key=api_key)
        self.history_id = ""
        self.tool_id = ""
        self.input_files = []
        self.json_input = []
        self.my_dict = {}
        self.my_dict2 = {}
        self.file_path = "tool_data.json"
        self.datatabels_name = []
        self.url_name = ""
        self.job_id = []

    def connect_to_galaxy_with_retry(self):
        while True:
            try:
                self.gi.config.get_version()
                print("is alive")
                return self.gi
            except ConnectionError as e:
                print(f"Failed to connect to Galaxy: {e}")
                print("Retrying in 2 seconds...")
                time.sleep(2)  # Wait for 2 seconds before retrying

    def upload_file(self, file_name: str, new_name: str | None = None):
        job = self.gi.tools.upload_file(path=file_name, history_id=self.history_id, file_name=new_name)
        job_id = job["jobs"][0]["id"]
        self.gi.jobs.wait_for_job(job_id=job_id)

    # for a given tool, give back the latest version and the id of this tool
    def get_newest_tool_version_and_id(self, tool_name: str):
        # Get a list of tools with the specified name
        tools = self.gi.tools.get_tools(name=tool_name)
        # Create a dictionary to store tool versions and associated galaxy versions
        tool_versions = {}
        # Iterate through the list of tools
        for tool in tools:
            # Extract numeric components from the version string
            version_parts = re.findall(r'\d+', tool["version"])
            # If version_parts is not empty, the last component is the galaxy version
            galaxy_version = version_parts[-1] if version_parts else ""
            # Store the tool version and associated galaxy version in the dictionary
            tool_versions[tool["version"]] = galaxy_version

        # Find the newest version based on the version numbers
        newest_version = max(tool_versions, key=self.version_key)
        # Retrieve the tool ID of the newest version
        tool_id = next(tool["id"] for tool in tools if tool["version"] == newest_version)
        # Return the newest version and tool ID
        return newest_version, tool_id

    def get_all_tool_version_and_id(self, tool_name: str):
        tools = self.gi.tools.get_tools(name=tool_name)
        tool_versions = {}
        for tool in tools:
            tool_versions[tool["version"]] = tool["id"]
        return tool_versions

    # calculates the history_id for a given history name
    def get_history_id(self, history_name: str):
        # check if connected to galaxy server
        # self.connect_to_galaxy_with_retry()
        history = self.gi.histories.get_histories(name=history_name)
        history_id = history[0]["id"]
        self.history_id = history_id

    def create_history(self, history_name: str):
        # check if connected to galaxy server
        # self.connect_to_galaxy_with_retry()
        histories = self.gi.histories.get_histories()
        # delete if history already exists
        if histories[0]["name"] == history_name:
            self.gi.histories.delete_history(histories[0]["id"])
        history = self.gi.histories.create_history(history_name)
        self.history_id = history["id"]

    # return just the tool_id of latest version
    def get_tool_id(self, tool_version: Optional[str]):
        return tool_version[1]

    # wait until job is done, cause tools are dependent of each other
    def wait_for_job(self, job_id: str):
        try:
            self.gi.jobs.wait_for_job(job_id=job_id, interval=30)
        except ConnectionError:
            self.connect_to_galaxy_with_retry()

    # Define a custom key function to extract and compare version numbers
    def version_key(self, version: SyntaxError):
        # Split the version string into components and convert them to integers
        parts = [int(part) for part in re.findall(r'\d+', version)]
        return tuple(parts)

    def get_dataset_names(self):
        pass

    def get_inputs(self):
        pass

    def run_tool_with_input_files(self, tool_name: str, datasets_name: List[str]):
        self.datatabels_name = self.get_names_from_data(self.load_data_from_file(self.file_path))
        _, self.tool_id = self.get_newest_tool_version_and_id(tool_name)
        self.my_dict = self.build_input_states(tool_id=self.tool_id, history_id=self.history_id)
        input_data_ids = self.get_input_data_ids(datasets_name)
        self.input_files = self.get_input_files(input_data_ids)

    def get_input_data_ids(self, dataset_names: List[str]):
        # get the dataset_ids in a list given the names of the datasets
        dataset_ids = []
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False)
        # check for every dataset_name in datasets if this name is valid, if so
        # add it to dataset_id list
        for dataset_name in dataset_names:
            for dataset in datasets:
                if dataset_name in dataset["name"]:
                    dataset_ids.append(dataset["id"])
                    print(f"Found dataset '{dataset_name}' with ID: {dataset['id']}")

        return dataset_ids

    def get_input_files(self, input_data_ids: List[str]):
        """
        return list with input_file format of the datasets
        which has no errors
        input_files = [
            {
                'src': 'hda',
                'id': input_data_id_1  # Replace with the actual input data ID
            }
        ]
        """
        valid_inputs = []
        for data_id in input_data_ids:
            dataset_info = self.gi.datasets.show_dataset(data_id)
            if dataset_info.get('state') != 'error':
                valid_inputs.append({'src': 'hda', 'id': data_id})
        return valid_inputs

    def run_tool(self, inputs: Dict, combination_test: bool = False):
        job = self.gi.tools.run_tool(
            history_id=self.history_id,
            tool_id=self.tool_id,
            tool_inputs=inputs,
            input_format="21.01"
        )

        job_id = job["jobs"][0]["id"]

        if combination_test:
            self.job_id.append([job_id, inputs])
        else:
            self.wait_for_job(job_id)
            print(f"Tool '{self.tool_id}' has finished processing with job ID: {job_id}")

    def update_dataset_names(self, update_names, old_names):
        """
        Update the odd dataset names with the new names
        """
        input_data_ids = self.get_input_data_ids(old_names)
        for data_id, new_name in zip(input_data_ids, update_names):
            self.gi.histories.update_dataset(history_id=self.history_id, dataset_id=data_id, name=new_name)

    def get_tool_input_options(self, tool_name):
        """
        Get detailed input options for a specified tool.

        Parameters:
        - tool_name: The name of the tool.

        Returns:
        - input_options: Detailed input options for the tool.
        """
        # Get the newest version and ID of the tool
        _, tool_id = self.get_newest_tool_version_and_id(tool_name)
        # Show the tool with detailed input and output options
        tool_details = self.gi.tools.show_tool(tool_id, io_details=True)
        # Extract detailed input options
        input_options = tool_details.get('inputs', {})
        return input_options

    def get_tool_input_options_all(self, tool_name):
        """
        Retrieve input options for a given tool.

        Args:
            tool_name (str): The name of the tool.

        Returns:
            dict: A dictionary containing input options for the specified tool.
        """
        # Get the newest tool version and its ID
        _, tool_id = self.get_newest_tool_version_and_id(tool_name=tool_name)

        # Retrieve tool details using the Galaxy API
        tool_details = self.gi.tools.show_tool(tool_id, io_details=True, link_details=True)

        # Extract input options from the tool details
        input_options = tool_details.get('tool_shed_repository', {})

        # Return the input options as a dictionary
        return input_options

    def write_to_file(self, data, name):
        with open(name, 'w') as file:
            pp = PrettyPrinter(indent=4, stream=file)
            pp.pprint(data)
        file.close()

    def get_databases(self, inputs):
        """
        json_extract returns for every database a list with name, database_name, selected
        return every database_name in a list
        """
        return [inputs[i] for i in range(1, len(inputs), 3)]

    def remove_duplicate(self, orginal_list):
        unique_list = []
        for item in orginal_list:
            if item not in unique_list:
                unique_list.append(item)
        return unique_list

    def get_flattened_list(self, original_list):
        """
        Flatten a list of lists.

         Parameters:
            - original_list: The original list of lists.

        Returns:
            - flattened_list: The flattened list.
        """
        flattened_list = [element for sublist in original_list[0] for element in sublist]
        return flattened_list

    def extract_values_from_nested_json(self, json_object, target_key):
        """
        Recursively fetch values from nested JSON based on a specified key.

        Args:
            json_object (dict or list): The JSON object to search.
            target_key (str): The key to search for in the JSON object.

        Returns:
            list: A list of values corresponding to the specified key in the JSON object.
        """
        result_values = []
        result_muliple = []

        def recursive_search(obj, result_values, key):
            """
            Recursively searches for values of key in JSON tree.

            Args:
                obj (dict or list): The current JSON object or list.
                result_values (list): The list to store found values.
                key (str): The target key to search for.

            Returns:
                list: A list of values corresponding to the specified key.
            """
            if isinstance(obj, dict):
                for _, v in obj.items():
                    if isinstance(v, (dict, list)):
                        recursive_search(v, result_values, key)
                    if v == key and obj.get("model_class") == 'SelectToolParameter':
                        options = obj.get("options", {})
                        result_values.append(options)
                        if obj.get('multiple') is True:
                            result_muliple.append(key)
            elif isinstance(obj, list):
                for item in obj:
                    recursive_search(item, result_values, key)
            return result_values

        found_values = recursive_search(json_object, result_values, target_key)
        return found_values, result_muliple

    def extract_keys(self, data, keys=[]):
        if isinstance(data, dict):
            for key, value in data.items():
                keys.append(key)
                self.extract_keys(value, keys)
        elif isinstance(data, list):
            for item in data:
                self.extract_keys(item, keys)
        return keys

    def extract_keys_with_path(self, data, path=[], keys=[]):
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = path + [f"|{key}" if path != [] else f"{key}"]
                keys.append("".join(current_path))
                self.extract_keys_with_path(value, current_path, keys)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = path + [f"_{i}"]
                self.extract_keys_with_path(item, current_path, keys)
        return keys

    def get_databases_name(self, database_names):
        base_url = self.get_link(self.tool_name)
        development_repo_href = HTMLParser(self.process_iframe_url(base_url)).find_development_repository_href()
        databases_list = []
        # for db_name in self.fetch_database_names(development_repo_href):
        db_url = (
            f"{development_repo_href}/{self.url_name}.xml"
            if development_repo_href[-1] != "/"
            else f"{development_repo_href}{self.url_name}.xml"
        )

        xml_parser = XMLParser(url=db_url)
        db_data = self.find_values_in_nested_json(xml_parser.prepare_fetch_xml_data(), "rawLines", is_object=False)
        flattened_data = self.flatten(db_data)

        if flattened_data:
            xml_parser.fetch_xml_data(flattened_data)
            databases_list.append(xml_parser.find_databases_names(database_names))

        unique_databases = self.remove_duplicate(self.flatten(databases_list))

        return unique_databases

    def fetch_database_names(self, development_repo_href):
        url_parser = HTMLParser(url=development_repo_href)
        data = url_parser.get_github_resource()
        xml_files = self.find_values_in_nested_json(data, ".xml", is_object=False)

        for xml_file in xml_files:
            yield xml_file

    def update_keys(self, original, updated):
        for key, value in updated.items():
            original = (self.update_values(original, key=key, new_values=value))
        return original

    def build_input_states(self, tool_id: str, history_id: str, inputs: Dict[str, Any] | None = None):

        try:
            tools = self.gi.tools.build(tool_id=tool_id, inputs=inputs, history_id=history_id)
            input_states = (tools["state_inputs"])
            return input_states
        except ConnectionError as e:
            if "500" in str(e) and "Uncaught exception in exposed API method" in str(e):
                # Handle the specific ConnectionError with HTTP status code 500 and the specified error message
                print("Caught the specific ConnectionError:")
                print(f"Exception: {str(e)}")
            else:
                # Handle other ConnectionError scenarios
                print("Caught a ConnectionError, but not the specific case:")
                print(f"Exception: {str(e)}")

    def get_link(self, tool_name):
        """
        Construct a URL based on the tool name and its input options.

        Args:
            tool_name (str): The name of the tool.

        Returns:
            tuple: A tuple containing the full URL and the base URL.
        """
        tool_options = self.get_tool_input_options_all(tool_name)

        tool_shed = tool_options["tool_shed"]
        owner = tool_options["owner"]
        name = tool_options["name"]
        changeset_revision = tool_options["changeset_revision"]

        base_url = f"https://{tool_shed}"
        full_url = f"{base_url}/view/{owner}/{name}/{changeset_revision}"

        self.url_name = name

        return full_url, base_url

    def process_iframe_url(self, url_tuple):
        """
        Process the URL to extract and handle the iframe source URL.

        Args:
            url_tuple (tuple): A tuple containing base_url and url_1.

        Returns:
            str or None: The iframe source URL if found, otherwise None.
        """
        base_url, url_1 = url_tuple
        html_parser = HTMLParser(base_url)
        iframe_src = html_parser.get_iframe_src()

        if iframe_src:
            iframe_url = f"{url_1}{iframe_src}"
            return iframe_url
        else:
            print("No iframe found in the HTML content.")
            return None

    def process_data(self, keys, inputs_options):
        result_dict = {}
        multiple_values = []
        for key in keys:
            # Extract values based on the key
            extracted_values, multiple_values = self.extract_values_from_nested_json(inputs_options, key)
            # Check if the extracted values are not empty
            if extracted_values:
                flattened_values = self.get_flattened_list(extracted_values)
                if key == "selector":
                    self.json_input = (self.flatten(extracted_values))
                databases = self.get_databases(flattened_values)

                # Store databases in the result_dict
                result_dict[key] = databases

        return result_dict, multiple_values

    def update_values(self, dic, key, new_values, paired: bool = False):
        """
        Recursively updates values in a nested dictionary based on a specified key.

        Args:
            dic (dict): The original dictionary.
            key (str): The key to update in the dictionary.
            new_values: The new values to assign to the matching key.

        Returns:
            dict: The updated dictionary.
        """
        # Make a deep copy to preserve the original dictionary
        dictionary = copy.deepcopy(dic)

        def recursion(d, k, new_val):
            if isinstance(d, dict):
                for k_inner, v_inner in d.items():
                    if isinstance(v_inner, (dict, list)):
                        recursion(v_inner, k, new_val)
                    if k_inner == k:
                        if isinstance(new_val, (list, tuple)) and paired:
                            d[k_inner] = [new_val.pop(0)] if new_val else None
                        else:
                            d[k_inner] = new_val
            elif isinstance(d, list):
                for item in d:
                    recursion(item, k, new_val)

        recursion(dictionary, key, new_values)

        return dictionary

    def find_values_in_nested_json(self, json_object, target_key, is_object: str = True):
        """
        Recursively searches for values of a specified key in a nested JSON object.

        Args:
            json_object (dict or list): The JSON object to search.
            target_key (str): The key to search for in the JSON object.

        Returns:
            list: A list of values corresponding to the specified key in the JSON object.
        """
        result_values = []

        def recursive_search(obj, result_values, key):
            """
            Recursively searches for values of key in JSON tree.

            Args:
                obj (dict or list): The current JSON object or list.
                result_values (list): The list to store found values.
                key (str): The target key to search for.

            Returns:
                list: A list of values corresponding to the specified key.
            """
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, (dict, list)):
                        recursive_search(v, result_values, key)
                    if (is_object is True):
                        if v == key:
                            result_values.append(obj)
                    else:
                        if isinstance(v, str):
                            if key in v and k == "name":
                                result_values.append(v)
                        else:
                            if k == key:
                                result_values.append(v)
            elif isinstance(obj, list):
                for item in obj:
                    recursive_search(item, result_values, key)
            return result_values

        found_values = recursive_search(json_object, result_values, target_key)
        return found_values

    def flatten(self, lst):
        flat_list = []
        for item in lst:
            if isinstance(item, list):
                flat_list.extend(self.flatten(item))
            else:
                flat_list.append(item)
        return flat_list

    def generate_input_combinations(
        self,
        input_files: List[str],
        filter_keyword,
        value: str,
        key,
        updated_dict: Dict,
        paired=True
    ):
        """
        Generate input combinations based on keyword filtering and tool options.

        Args:
            input_files (List[str]): List of input files.
            filter_keyword (str): Keyword to filter input combinations.
            value (str): Description of the value parameter.
            key (type): Description of the key parameter.

        Returns:
            List[dict]: List of dictionaries representing input combinations.
        """
        inputs = input_files.copy()

        # Extract keys with path from my_dict
        keys_with_path = self.extract_keys_with_path(self.my_dict)

        # Create a dictionary to store filtered keys based on the first keyword
        filtered_keys = {i: key for i in keys_with_path if filter_keyword in i.split("|")}

        # Build the original dictionary using the filtered keys
        original_state_dict = self.try_building_original_states(filtered_keys)
        # If the original dictionary is None, return an empty list
        if original_state_dict is None:
            return []
        # Store the original dictionary in my_dict2
        self.my_dict2 = original_state_dict
        # Update the original dictionary with input_files using the update_values method
        updated_state_dict = self.update_values(original_state_dict, value, inputs, paired)
        dict_updated = (self.update_keys(updated_state_dict.copy(), updated_dict))

        return dict_updated

    def try_building_original_states(self, filtered_keys):
        """
        Attempt to build the original dictionary using the filtered keys with a retry mechanism.

        Args:
            filtered_keys (dict): Filtered keys for building the original dictionary.

        Returns:
            dict or None: Original dictionary or None if it cannot be built.
        """
        current_partial_state = {}
        for key, value in filtered_keys.items():
            current_partial_state[key] = value
            original_state = self.build_input_states(
                tool_id=self.tool_id,
                history_id=self.history_id,
                inputs=current_partial_state
            )
            if original_state is not None:
                return original_state
            current_partial_state = {}
        return None

    def load_data_from_file(self, file_path):
        with open(file_path, 'r') as file:
            loaded_data = json.load(file)

        return loaded_data

    def get_names_from_data(self, data):
        return [entry['name'] for entry in data]

    def find_databases(self):
        lst_db = []
        lst2 = ["humann_nucleotide_database", "humann_protein_database", "rRNA_databases"]
        # for database in self.datatabels_name:
        for database in lst2:
            print(database)
            lst_db.append(self.get_databases_name(database_names=database))
        return lst_db

    def get_all_input_combinations(self, key_word):
        """
        Retrieves input combinations based on a keyword and tool options.

        Args:
            input_files (List[str]): List of input files.
            key_word (str): Keyword to filter input combinations.

        Returns:
            List[dict]: List of dictionaries representing input combinations.
        """
        d1 = {}
        d2 = {}
        l1 = []
        l2 = []
        # Get tool input options and process data
        inputs_options = self.get_tool_input_options(self.tool_name)
        input_options_dictionary = self.find_values_in_nested_json(inputs_options, key_word)

        lst = self.remove_duplicate(self.flatten(self.find_databases()))
        d1, l1 = self.process_data(lst, inputs_options=input_options_dictionary)
        d2, l2 = self.process_data(lst, inputs_options=inputs_options)
        # combine the dictionarys
        dictionary = {**d1, **d2}
        pprint(dictionary)
        multiple_list = [*l1, *l2]
        multiple_list = self.remove_duplicate(multiple_list)
        all_combinations = self.generate_combinations(dictionary=dictionary, exclude_keys=multiple_list)

        return all_combinations

    def generate_combinations(self, dictionary: Dict, exclude_keys: List):
        # Prepare an empty dictionary to store the excluded key-value pairs
        excluded_dict = {}

        # Create a copy of the original dictionary for manipulation
        remaining_dict = dictionary.copy()

        # Move the excluded keys and their values to the excluded_dict
        for key in exclude_keys:
            excluded_dict[key] = remaining_dict.pop(key)

        # Generate combinations of the remaining values
        remaining_combinations = [dict(zip(remaining_dict.keys(), values)) for values in product(*remaining_dict.values())]

        # Merge the excluded_dict with each remaining combination
        all_combinations = [combination | excluded_dict for combination in remaining_combinations]

        # Return the final list of combinations
        return all_combinations

    def get_combination_test_inputs(
        self,
        input_files: List[str],
        filter_keyword,
        value: str,
        key,
        updated_dict: Dict,
        paired=True
    ):

        # Update the original dictionary with input_files using the update_values method
        updated_dict = self.generate_input_combinations(
            input_files=input_files,
            filter_keyword=filter_keyword,
            value=value,
            key=key,
            updated_dict=updated_dict,
            paired=paired
        )

        # Get all input combinations
        all_combinations = self.get_all_input_combinations(key_word=key)

        # Generate input_list with updated dictionaries for each combination
        input_list = [self.update_keys(updated_dict.copy(), combination) for combination in all_combinations]

        return input_list

    def is_entry_present(self, data, entry):
        # Check if the entry is present (ignoring timestamp)
        for i in data:
            if i.get("input") == entry:
                return True
        return False

    def add_entry_to_json(self, entry, file_path, error_message):
        # Load existing JSON data
        try:
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            # If the file doesn't exist, initialize an empty list
            data = []

        # Check if the entry is already present (ignoring timestamp)
        if not self.is_entry_present(data, entry):
            # Add the entry to the data
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_entry = {
                "timestamp": timestamp,
                "error_message": error_message,
                "input": entry
            }
            if isinstance(data, list):
                data.append(data_entry)
            else:
                data = [data_entry]

            # Write the updated data back to the JSON file
            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=2)

    def handle_error_entry(self, entry, error_message):
        file_path = f'{self.tool_name}_incorrect_combination.json'
        self.add_entry_to_json(entry=entry, file_path=file_path, error_message=error_message)

    def wait_for_job_completion(self, job_id):
        while True:
            try:
                job_info = self.gi.jobs.show_job(job_id)
                if job_info['state'] != 'queued' and job_info['state'] != "running":
                    return job_info['state']
                time.sleep(5)
            except ConnectionError as e:
                print(f"Failed to connect to Galaxy: {e}")
                print("Retrying in 2 seconds...")
                time.sleep(2)


class FastQCTool(Tool):

    def __init__(self, server, api_key, history_id):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "FastQC"

    def get_inputs(self, input_files: List[str]):
        """
        Return a dictionary with the correct inputs
        """
        input_file_1, input_file_2 = input_files
        inputs_1 = {
            'input_file': {
                'values': input_file_1
            }
        }
        inputs_2 = {
            'input_file': {
                'values': input_file_2
            },
        }
        return inputs_1, inputs_2

    def get_dataset_names(self):
        """
        names of datsets
        """
        return "T1A_forward", "T1A_reverse"

    def run_tool_with_input_files(self, tool_name: str, combination_test: bool = False):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names())
        inputs_1, inputs_2 = self.get_inputs(self.input_files)
        super().run_tool(inputs=inputs_1)
        super().run_tool(inputs=inputs_2)


class MultiQCTool(Tool):
    SOFTWARE = "fastqc"
    KEY_WORD = "software"
    VALUES = "values"

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "MultiQC"
        self.input_dict = {}

    def get_inputs(self, input_files: List[str]):
        inputs = {
            'results_0|software_cond|software': self.SOFTWARE,
            'results_0|software_cond|output_0|input': {
                'values': input_files
            }
        }
        return inputs

    def get_dataset_names(self):
        return "FastQC on data 1: RawData", "FastQC on data 2: RawData"

    def run_tool_with_input_files(self, tool_name: str, combination_test: bool = False):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names())
        if combination_test:
            inputs = super().get_combination_test_inputs(
                input_files=self.input_files,
                filter_keyword=self.KEY_WORD,
                value=self.VALUES,
                key=self.SOFTWARE,
                updated_dict=self.input_dict,
                paired=False
            )

            for input_combination in inputs:
                try:
                    super().run_tool(inputs=input_combination, combination_test=True)
                except Exception as e:
                    super().handle_error_entry(input_combination, str(e))

            for job_info in self.job_id:
                completion_status = super().wait_for_job_completion(job_info[0])
                if completion_status == "error":
                    super().handle_error_entry(job_info[1], "job has error state")

        else:
            inputs = super().generate_input_combinations(
                input_files=self.input_files,
                filter_keyword=self.KEY_WORD,
                value=self.VALUES,
                key=self.SOFTWARE,
                updated_dict=self.input_dict,
                paired=False
            )
            super().run_tool(inputs=inputs)


class CutadaptTool(Tool):
    LIBRARY_TYPE = 'paired'
    MINIMUM_LENGTH = '150'
    QUALITY_CUTOFF = '20'
    OUTPUT_SELECTOR = 'report'
    KEY_WORD = "type"
    VALUES = "values"

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "Cutadapt"
        self.input_dict = {
            "minimum_length": self.MINIMUM_LENGTH,
            "quality_cutoff": self.QUALITY_CUTOFF,
            "output_selector": self.OUTPUT_SELECTOR
        }

    def get_inputs(self, inputs_files: List[str]):
        input_file_1, input_file_2 = inputs_files
        inputs = {
            'library|type': self.LIBRARY_TYPE,
            'library|input_1': {
                'values': input_file_1
            },
            'library|input_2': {
                'values': input_file_2
            },
            'filter_options|minimum_length': self.MINIMUM_LENGTH,
            'read_mod_options|quality_cutoff': self.QUALITY_CUTOFF,
            'output_selector': self.OUTPUT_SELECTOR
        }
        return inputs

    def get_dataset_names(self):
        return "T1A_forward", "T1A_reverse"

    def get_new_names_for_dataset(self):
        return "QC controlled forward reads", "QC controlled reverse reads"

    def get_output_names_of_cutadapt(self):
        return "Read 1 Output", "Read 2 Output"

    def run_tool_with_input_files(self, tool_name, combination_test: bool = False):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names())
        if combination_test:
            inputs = super().get_combination_test_inputs(
                input_files=self.input_files,
                filter_keyword=self.KEY_WORD,
                value=self.VALUES,
                key=self.LIBRARY_TYPE,
                updated_dict=self.input_dict
            )

            for input_combination in inputs:
                try:
                    super().run_tool(inputs=input_combination, combination_test=True)
                except Exception as e:
                    super().handle_error_entry(input_combination, str(e))

            for job_info in self.job_id:
                completion_status = super().wait_for_job_completion(job_info[0])
                if completion_status == "error":
                    super().handle_error_entry(job_info[1], "job has error state")

        else:
            inputs = super().generate_input_combinations(
                input_files=self.input_files,
                filter_keyword=self.KEY_WORD,
                value=self.VALUES,
                key=self.LIBRARY_TYPE,
                updated_dict=self.input_dict
            )
            super().run_tool(inputs=inputs)
            super().update_dataset_names(self.get_new_names_for_dataset(), self.get_output_names_of_cutadapt())


class SortMeRNATool(Tool):
    SEQUEUCING_TYPE_SELECTOR = "paired"
    DATABASES_SELECTOR = 'cached'
    PAIRED_TYPE = '--paired_out'
    ALIGNED_FASTX_OTHER = 'True'
    LOG = 'True'
    INPUT_DATABASES = 'input_databases'
    KEY_WORD = 'sequencing_type_selector'
    VALUES = "values"

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "Filter with SortMeRNA"
        self.input_dict = {
            "log": self.LOG,
            "other": self.ALIGNED_FASTX_OTHER,
            "databases_selector": self.DATABASES_SELECTOR,
            "paired_type": self.PAIRED_TYPE,
            "input_databases": self.get_datatables(),
        }

    def get_inputs(self, inputs_files):
        input_file_1, input_file_2 = inputs_files
        inputs = {
            'sequencing_type|sequencing_type_selector': 'paired',
            'sequencing_type|forward_reads': {
                'values': input_file_1
            },
            'sequencing_type|reverse_reads': {
                'values': input_file_2
            },
            'sequencing_type|paired_type': self.PAIRED_TYPE,
            'databases_type|databases_selector': self.DATABASES_SELECTOR,
            'databases_type|input_databases': self.get_datatables(),
            'aligned_fastx|other': self.ALIGNED_FASTX_OTHER,
            'log': self.LOG
        }
        return inputs

    def get_dataset_names(self):
        return "QC controlled forward reads", "QC controlled reverse reads"

    def run_tool_with_input_files(self, tool_name, combination_test: bool = False):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names())
        if combination_test:
            inputs = super().get_combination_test_inputs(
                input_files=self.input_files,
                filter_keyword=self.KEY_WORD,
                value=self.VALUES,
                key=self.SEQUEUCING_TYPE_SELECTOR,
                updated_dict=self.input_dict
            )

            for input_combination in inputs:
                try:
                    super().run_tool(inputs=input_combination, combination_test=True)
                except Exception as e:
                    super().handle_error_entry(input_combination, str(e))

            for job_info in self.job_id:
                completion_status = super().wait_for_job_completion(job_info[0])
                if completion_status == "error":
                    super().handle_error_entry(job_info[1], "job has error state")

        else:
            inputs = super().generate_input_combinations(
                input_files=self.input_files,
                filter_keyword=self.KEY_WORD,
                value=self.VALUES,
                key=self.SEQUEUCING_TYPE_SELECTOR,
                updated_dict=self.input_dict
            )
            super().run_tool(inputs=inputs)

    def get_datatables(self):
        databases = [
            '2.1b-rfam-5s-database-id98',
            '2.1b-silva-arc-23s-id98',
            '2.1b-silva-euk-28s-id98',
            '2.1b-silva-bac-23s-id98',
            '2.1b-silva-euk-18s-id95',
            '2.1b-silva-bac-16s-id90',
            '2.1b-rfam-5.8s-database-id98',
            '2.1b-silva-arc-16s-id95'
        ]
        return databases


class FASTQinterlacerTool(Tool):
    VALUES = "values"
    KEY_WORD = "reads_selector"
    PAIRED = "paired"

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "FASTQ interlacer"
        self.input_dict = {}

    def get_inputs(self, inputs_files: List[str]):
        input_file_1, input_file_2 = inputs_files
        inputs = {
            'reads|input1_file': {
                'values': input_file_1
            },
            'reads|input2_file': {
                'values': input_file_2
            },
        }
        return inputs

    def get_dataset_names(self):
        return "Unaligned forward reads", "Unaligned reverse reads"

    def get_new_names_for_dataset(self):
        return ["Interlaced non rRNA reads"]

    def get_output_names_of_interlacer(self):
        return ["FASTQ interlacer pairs"]

    def run_tool_with_input_files(self, tool_name: str, combination_test: bool = False):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names())
        inputs = super().generate_input_combinations(
            input_files=self.input_files,
            filter_keyword=self.KEY_WORD,
            value=self.VALUES,
            key=self.PAIRED,
            updated_dict=self.input_dict
        )
        super().run_tool(inputs=inputs)
        super().update_dataset_names(self.get_new_names_for_dataset(), self.get_output_names_of_interlacer())


class MetaPhlAnTool(Tool):
    SELECTOR = 'paired'
    STATE_Q = '0.1'
    KRONA_OUTPUT = "True"
    TAX_LEV_SPLIT_LEVELS = "True"
    DB_SELECTOR = "cached"
    KEY_WORD = "selector"
    VALUES = "values"

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "MetaPhlAn"
        self.input_dict = {
            "krona_output": self.KRONA_OUTPUT,
            "stat_q": self.STATE_Q,
            "db_selector": self.DB_SELECTOR,
            "split_levels": self.TAX_LEV_SPLIT_LEVELS
        }

    def get_inputs(self, inputs_files: List[str]):
        input_file_1, input_file_2 = inputs_files
        inputs = {
            'inputs|in|raw_in|selector': self.SELECTOR,
            'inputs|in|raw_in|in_f': {
                'values': input_file_1
            },
            'inputs|in|raw_in|in_r': {
                'values': input_file_2
            },
            'analysis|analysis_type|tax_lev|split_levels': self.TAX_LEV_SPLIT_LEVELS,
            'analysis|stat_q': self.STATE_Q,
            'out|krona_output': self.KRONA_OUTPUT
        }
        return inputs

    def get_dataset_names(self):
        return "QC controlled forward reads", "QC controlled reverse reads"

    def run_tool_with_input_files(self, tool_name, combination_test: bool = False):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names())
        if combination_test:
            inputs = super().get_combination_test_inputs(
                input_files=self.input_files,
                filter_keyword=self.KEY_WORD,
                value=self.VALUES,
                key=self.SELECTOR,
                updated_dict=self.input_dict
            )

            for input_combination in inputs:
                try:
                    super().run_tool(inputs=input_combination, combination_test=True)
                except Exception as e:
                    super().handle_error_entry(input_combination, str(e))

            for job_info in self.job_id:
                completion_status = super().wait_for_job_completion(job_info[0])
                if completion_status == "error":
                    super().handle_error_entry(job_info[1], "job has error state")

        else:
            inputs = super().generate_input_combinations(
                input_files=self.input_files,
                filter_keyword=self.KEY_WORD,
                value=self.VALUES,
                key=self.SELECTOR,
                updated_dict=self.input_dict
            )
            super().run_tool(inputs=inputs)


class HUMAnNTool(Tool):
    SELECTOR = 'bypass_taxonomic_profiling'
    HUMAnN_NUCLEOTIDE_DATABASE = 'chocophlan-full-3.6.0-29032023'
    HUMAnN_PROTEIN_DATABASE = 'uniref-uniref90_diamond-3.0.0-13052021'
    FILE_PATH = "incorrect_database_combination.tsv"
    KEY_WORD = "selector"
    VALUES = "values"

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "HUMAnN"
        self.input_dict = {
            "nucleotide_database": self.HUMAnN_NUCLEOTIDE_DATABASE,
            "protein_database": self.HUMAnN_PROTEIN_DATABASE

        }

    def get_inputs(self, inputs_files: List[str], nucleotide_database, protein_database):
        input_file_1, input_file_2 = inputs_files
        inputs = {
            'in|input': {
                'values': input_file_1
            },
            'wf|selector|': self.SELECTOR,
            'wf|bypass_taxonomic_profiling|--taxonomic-profile': {
                'values': input_file_2
            },
            'wf|nucleotide_search|nucleotide_db|nucleotide_database': nucleotide_database,
            'wf|translated_search|protein_db|protein_database': protein_database
        }
        return inputs

    def get_dataset_names(self):
        return "Interlaced non rRNA reads", "Predicted taxon relative abundances"

    def get_input_data_ids(self, dataset_names: Optional[str]):
        dataset_ids = []
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False)
        for dataset_name in dataset_names:
            for dataset in datasets:
                if (dataset_name in dataset["name"]
                        and "Krona" not in dataset["name"]
                        and "taxonomic levels" not in dataset["name"]):
                    dataset_ids.append(dataset["id"])
                    print(f"Found dataset '{dataset_name}' with ID: {dataset['id']}")

        return dataset_ids

    def run_tool_with_input_files(self, tool_name, combination_test: bool = False):
        self.datatabels_name = self.get_names_from_data(self.load_data_from_file(self.file_path))
        _, self.tool_id = self.get_newest_tool_version_and_id(tool_name)
        input_data_ids = self.get_input_data_ids(self.get_dataset_names())
        self.input_files = super().get_input_files(input_data_ids)
        self.my_dict = self.build_input_states(tool_id=self.tool_id, history_id=self.history_id)
        # run all possible options of the databases
        if combination_test:
            inputs = super().get_combination_test_inputs(
                input_files=self.input_files,
                filter_keyword=self.KEY_WORD,
                value=self.VALUES,
                key=self.SELECTOR,
                updated_dict=self.input_dict
            )

            for input_combination in inputs:
                try:
                    super().run_tool(inputs=input_combination, combination_test=True)
                except Exception as e:
                    super().handle_error_entry(input_combination, str(e))

            for job_info in self.job_id:
                completion_status = super().wait_for_job_completion(job_info[0])
                if completion_status == "error":
                    super().handle_error_entry(job_info[1], "job has error state")

        else:
            inputs = super().generate_input_combinations(
                input_files=self.input_files,
                filter_keyword=self.KEY_WORD,
                value=self.VALUES,
                key=self.SELECTOR,
                updated_dict=self.input_dict
            )
            super().run_tool(inputs=inputs)


class RenormalizeTool(Tool):

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.pathway_name = ""

    def get_inputs(self, inputs_files: List[str]):
        input_file_1 = inputs_files
        inputs = {
            'input': {
                'values': input_file_1
            },
            'units': 'relab',
        }
        return inputs

    def get_dataset_names(self, name: str):
        self.pathway_name = name
        return [name]

    def get_new_names_for_dataset(self):
        name = ""
        if self.pathway_name == "Gene families and their abundance":
            name = "Normalized gene families"
        elif self.pathway_name == "Pathways and their abundance":
            name = "Normalized pathways"
        return [name]

    def get_output_names_of_renormalize(self):
        return ["Renormalize"]

    def run_tool_with_input_files(self, tool_name: str):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names(self.pathway_name))
        for input_file in self.input_files:
            inputs = self.get_inputs(input_file)
            super().run_tool(inputs=inputs)
        super().update_dataset_names(self.get_new_names_for_dataset(), self.get_output_names_of_renormalize())
