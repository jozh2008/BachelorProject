from bioblend import galaxy
from bioblend import ConnectionError
from pprint import pprint
import threading
import time
import json
import copy
from itertools import product
from xml_parser import XMLParser
from html_content_extractor import HTMLContentExtractor
from galaxy_tool_runner import GalaxyToolRunner
from datetime import datetime
from typing import (
    List,
    Dict,
)


class Tool:
    def __init__(self, server: str, api_key: str) -> None:
        self.gi = galaxy.GalaxyInstance(url=server, key=api_key)
        self.server = server
        self.history_id = ""
        self.json_input = []
        self.my_dict = {}
        self.file_path = "tool_data.json"
        self.datatables_name = []

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
        """
        Upload a file to Galaxy and wait for the completion of the upload job.

        This function uploads a file to a Galaxy history, monitors the upload job's completion,
        and returns the ID of the uploaded dataset.

        Parameters:
        - file_name (str): The name of the file to upload.
        - new_name (str | None, optional): The desired name for the uploaded file. Defaults to None.

        Returns:
        - str: The ID of the uploaded dataset.
        """
        # Upload the file to Galaxy
        job = self.gi.tools.upload_file(path=file_name, history_id=self.history_id, file_name=new_name)
        job_id = job["jobs"][0]["id"]

        # Wait for the completion of the upload job
        self.wait_for_job_completion(job_id=job_id)
        self.gi.jobs.wait_for_job(job_id=job_id)
        self.wait_for_job_completion(job_id=job_id)

        return job["outputs"][0]["id"]

    def workflow_input(self, forward_id: str, reverse_id: str):
        """
        Create input specifications for a Galaxy workflow using forward and reverse dataset IDs.

        This function generates a dictionary representing the inputs for a Galaxy workflow. It expects
        the IDs of forward and reverse datasets and assigns them to the corresponding input slots in the workflow.

        Parameters:
        - forward_id (str): The ID of the forward dataset.
        - reverse_id (str): The ID of the reverse dataset.

        Returns:
        - dict: A dictionary representing the input specifications for the Galaxy workflow.
        """

        workflow_inputs = {
            '0': {'src': 'hda', 'id': forward_id},
            '1': {'src': 'hda', 'id': reverse_id},
        }

        return workflow_inputs

    def run_workflow(self, workflow_inputs: Dict, file_workflow: str):
        """
        Run a Galaxy workflow with the provided inputs.

        This function imports a workflow from a local path, invokes the workflow with specified inputs,
        and waits for a brief period to allow the workflow to complete. The result of invoking the workflow
        is returned.

        Parameters:
        - workflow_inputs (dict): Inputs for the workflow as a dictionary.

        Returns:
        - dict: The result of invoking the workflow.
        """

        # Get names of data tables from tool_data.json and store in a list
        self.datatables_name = self.get_names_from_data(data=self.load_data_from_file(file_path=self.file_path))

        # Import the workflow from a local path
        workflow = self.gi.workflows.import_workflow_from_local_path(file_local_path=file_workflow)
        workflow_id = workflow.get("id", {})

        # Invoke the workflow with provided inputs
        workflow_result = self.gi.workflows.invoke_workflow(
            workflow_id=workflow_id,
            inputs=workflow_inputs,
            history_id=self.history_id
        )

        invocation_id = workflow_result.get("id", {})

        workflow_result = self.wait_for_workflow(workflow_id=workflow_id, invocation_id=invocation_id)

        return workflow_result

    def wait_for_workflow(self, workflow_id: str, invocation_id: str):
        """
        Wait for the completion of a specific workflow invocation.

        This method continuously checks the state of the workflow invocation until it is no longer in the 'new' state.
        It sleeps for 5 seconds between each check.

        Args:
            workflow_id (str): The ID of the workflow.
            invocation_id (str): The ID of the workflow invocation.

        Returns:
            dict: Information about the workflow invocation once it's no longer in the 'new' state.
        """
        while True:
            workflow_invocation_info = self.gi.workflows.show_invocation(workflow_id=workflow_id, invocation_id=invocation_id)
            if workflow_invocation_info['state'] not in {'new'}:
                return workflow_invocation_info
            time.sleep(5)

    def delete_dataset_and_datacollection(self):
        """
        Delete datasets and dataset collections from a Galaxy history, excluding certain predefined histories.

        This function retrieves the items in a Galaxy history and deletes datasets or dataset collections based on their type.
        Datasets are permanently purged when deleted.

        Returns:
        - List of IDs for items in the excluded histories that were not deleted.

        Note:
        - Excluded histories are identified by their 'hid' (history ID) values 1 and 2.
        - Datasets are deleted using 'delete_dataset' method, and dataset collections using 'delete_dataset_collection' method.
        """

        excluded_history_ids = [1, 2]
        excluded_item_ids = []

        items = self.gi.histories.show_history(history_id=self.history_id, contents=True, deleted=False, visible=True)

        for item in items:
            hid = item["hid"]
            item_type = item["type"]
            item_id = item["id"]

            if hid not in excluded_history_ids:
                if item_type == "file":
                    self.gi.histories.delete_dataset(history_id=self.history_id, dataset_id=item_id, purge=True)
                else:
                    self.gi.histories.delete_dataset_collection(history_id=self.history_id, dataset_collection_id=item_id)
            else:
                excluded_item_ids.append(item_id)

        return excluded_item_ids

    def workflow_show_invocation(self):
        """
        Get a list of file IDs in the current Galaxy history that are not in a 'ok' state.

        This function compiles a list of file IDs that are not in an 'ok' state in the current Galaxy history

        Parameters:
        - workflow_id (str): The ID of the workflow.

        Returns:
        - List of file IDs that are not in an 'ok' state in the current Galaxy history.
        """

        # Initialize an empty list to store file IDs
        problematic_file_ids = []

        # Retrieve items in the current Galaxy history
        items = self.gi.histories.show_history(history_id=self.history_id, contents=True, deleted=False, visible=True)
        print(len(items))

        # Iterate through items and identify files not in 'ok' state
        for item in items:
            if item["type"] == "file" and item["state"] != "ok":
                problematic_file_ids.append(item["id"])

        return problematic_file_ids

    def check_state_workflow(self, input_list):
        lst = []
        while input_list:
            current_length = len(input_list)
            time.sleep(5)
            try:
                pprint((current_length))
                for i in input_list:
                    item = (self.gi.datasets.show_dataset(dataset_id=i))
                    item_state = item["state"]
                    if item_state != "ok":
                        if item_state != "paused" and item_state != "error":
                            lst.append(i)
                    else:

                        gt_runner = GalaxyToolRunner(gi=self.gi, history_id=self.history_id)
                        tool_id, tool_input = gt_runner.fetch_dataset_details(item=item)

                        if tool_id not in self.my_dict:
                            self.my_dict[tool_id] = tool_input
                            pprint(self.my_dict)

                            url_link = (self.get_tool_input_options_link(tool_id=tool_id))
                            tool_name = self.get_tool_input_options_name(tool_id=tool_id)
                            pprint(tool_name)
                            pprint(url_link)
                            html_extractor = HTMLContentExtractor()
                            html_extractor.capture_html_content(url=url_link)

                            formatted_xml = html_extractor.extract_and_prettify_xml()

                            if "<options from_data_table" in formatted_xml:
                                thread = threading.Thread(
                                    target=self.run_tool_multithreaded,
                                    args=(formatted_xml, tool_id, tool_input, tool_name)
                                )
                                thread.start()

            except ConnectionError as e:
                print(f"Failed to connect to Galaxy: {e}")
                print("Retrying in 2 seconds...")
                print("workflow_connection")
                time.sleep(2)  # Wait for 2 seconds before retrying
                lst = self.workflow_show_invocation()
                print(len(lst), "after exception in workflow_connection")
            finally:
                # Update input_list to the remaining items after the loop
                print("round", len(lst))
                input_list = lst
                lst = []

        pprint("finished")
        thread.join()

    def run_tool_multithreaded(self, formatted_xml: str, tool_id: str, tool_input, tool_name: str):
        """
        Run a tool with multiple combinations of inputs in a multithreaded manner.

        Args:
            formatted_xml (str): The formatted XML content.
            tool_id (str): The ID of the tool to be executed.
            tool_input: The initial tool input.
            tool_name (str): The name of the tool.

        Returns:
            None
        """
        # Extract databases and process input options
        unique_databases = self.remove_duplicate(self.find_databases_in_xml(xml_content=formatted_xml))
        inputs_options = self.get_tool_input_options(tool_id=tool_id)
        dictionary, multiple_list = self.process_data(unique_databases, inputs_options=inputs_options)
        multiple_list = self.remove_duplicate(multiple_list)

        # Generate combinations of inputs
        all_combinations = self.generate_combinations(dictionary=dictionary, exclude_keys=multiple_list)
        input_list = [self.update_keys(tool_input.copy(), combination) for combination in all_combinations]

        # Display total combinations
        print(f'Total combinations for {tool_name}: {len(input_list)}')

        # Execute tool with each combination
        job_id_list = []
        for inp in input_list:
            updated_input = self.update_values(dic=inp, key="id", new_values="Test ids 3")
            updated_input = self.update_values(
                dic=updated_input,
                key="__workflow_invocation_uuid__",
                new_values="Test workflow_invocation-uuid 3"
            )

            try:
                # Run tool and get job information
                job = self.gi.tools.run_tool(
                    history_id=self.history_id,
                    tool_id=tool_id,
                    tool_inputs=inp,
                    input_format="21.01"
                )
                job_id = job["jobs"][0]["id"]
                job_id_list.append([job_id, updated_input])

            except Exception as e:
                # Handle tool execution exception
                print(tool_name, "Exception")
                self.handle_error_entry(entry=updated_input, error_message=str(e), tool_name=tool_name)
        # Wait for job completion and handle errors
        for job_info in job_id_list:
            completion_status = self.wait_for_job_completion(job_info[0])
            print(tool_name, completion_status)
            if completion_status == "error":
                self.handle_error_entry(
                    entry=job_info[1],
                    tool_name=tool_name,
                    error_message=f"Job has {completion_status} state"
                )

    def find_databases_in_xml(self, xml_content):
        """
        Extract a list of database names from XML content.

        This function uses an XMLParser to fetch data from the provided XML content and extracts
        database names based on the list of datatables names stored in the class instance.

        Parameters:
        - xml_content (str): The XML content to parse and extract database names from.

        Returns:
        - List of unique database names found in the XML content.
        """

        # Initialize an empty list to store database names
        database_names_list = []

        # Create an instance of the XMLParser class
        xml_parser = XMLParser()

        # Fetch XML data using the XMLParser
        xml_parser.fetch_xml_data(xml_content=xml_content)

        # Iterate through the list of datatables names
        for database in self.datatables_name:
            # Append the result of finding databases names to the list
            database_names_list.append(xml_parser.find_databases_names(database))

        # Flatten the list and remove duplicates
        result_list = self.flatten(self.remove_duplicate(original_list=database_names_list))

        return result_list

    def get_history_id(self, history_name: str) -> str:
        """
        Retrieve the history_id for a given history name.

        This function queries the Galaxy server for a history with the provided name and
        extracts the history_id. The retrieved history_id is then stored in the class instance.

        Parameters:
        - history_name (str): The name of the history for which to retrieve the history_id.

        Returns:
        - str: The history_id corresponding to the provided history name.
        """

        # Query Galaxy server for histories with the given name
        histories = self.gi.histories.get_histories(name=history_name)

        # Check if any history with the provided name was found
        if not histories:
            histories = self.gi.histories.create_history(history_name)
            history_id = histories["id"]

        # Extract the history_id from the first matching history
        else:
            history_id = histories[0]["id"]

        # Store the history_id in the class instance
        self.history_id = history_id

        # Return the retrieved history_id
        return history_id

    # wait until job is done, cause tools are dependent of each other
    def wait_for_job(self, job_id: str):
        try:
            self.gi.jobs.wait_for_job(job_id=job_id, interval=30)
        except ConnectionError:
            self.connect_to_galaxy_with_retry()

    def get_tool_input_options(self, tool_id):
        """
        Get detailed input options for a specified tool.

        Parameters:
        - tool_id: The id of the tool.

        Returns:
        - input_options: Detailed input options for the tool.
        """
        # Show the tool with detailed input and output options
        tool_details = self.gi.tools.show_tool(tool_id=tool_id, io_details=True)
        # Extract detailed input options
        input_options = tool_details.get('inputs', {})
        return input_options

    def get_tool_input_options_link(self, tool_id):
        """
        Retrieve the link details for input options of a given tool.

        This method fetches the link details for input options from the Galaxy API based on the tool ID.

        Args:
            tool_id (str): The ID of the tool.

        Returns:
            str: The link details for input options.
        """

        # Retrieve tool details using the Galaxy API
        tool_details = self.gi.tools.show_tool(tool_id=tool_id, io_details=True, link_details=True)

        # Extract input options link from the tool details
        input_options_link = tool_details.get('link', {})

        # Return the input options link as a string
        return f"{self.server}{input_options_link}"

    def get_tool_input_options_name(self, tool_id):
        """
        Retrieve the name of a tool and its input options using the Galaxy API.

        Args:
            tool_id (str): The ID of the tool.

        Returns:
            str: The name of the tool.
        """
        # Retrieve tool details using the Galaxy API
        tool_details = self.gi.tools.show_tool(tool_id=tool_id, io_details=True, link_details=True)

        # Extract the name of the tool
        tool_name = tool_details.get('name', {})

        return tool_name

    def get_databases(self, inputs):
        """
        json_extract returns for every database a list with name, database_name, selected
        return every database_name in a list
        """
        return [inputs[i] for i in range(1, len(inputs), 3)]

    def remove_duplicate(self, original_list):
        """
        Remove duplicates from a list while preserving the original order.

        This function takes a list as input and returns a new list with duplicate elements removed,
        preserving the original order of elements.

        Parameters:
        - original_list (list): The input list containing elements, including duplicates.

        Returns:
        - list: A new list with duplicate elements removed, preserving the original order.
        """

        unique_list = []

        for item in original_list:
            # Add item to the unique_list if it's not already present
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

    def update_keys(self, original, updated):
        """
        Update values in the original dictionary with values from the updated dictionary.

        This function takes two dictionaries as input, the original and the updated,
        and updates the values in the original dictionary with the corresponding values
        from the updated dictionary.

        Parameters:
        - original (dict): The original dictionary to be updated.
        - updated (dict): The dictionary containing values to update the original dictionary.

        Returns:
        - dict: The original dictionary with updated values.
        """

        for key, value in updated.items():
            original = self.update_values(original, key=key, new_values=value)

        return original

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

    def update_values(self, dic, key, new_values):
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

    def flatten(self, nested_list: List):
        """
        Flatten a nested list recursively.

        This function takes a nested list as input and returns a flattened list.

        Parameters:
        - nested_list (list): The input list that may contain nested lists.

        Returns:
        - list: A flattened list obtained by recursively flattening the input list.
        """

        flat_list = []

        for item in nested_list:
            # Check if the item is a list, and if so, recursively flatten it
            if isinstance(item, list):
                flat_list.extend(self.flatten(item))
            else:
                flat_list.append(item)

        return flat_list

    def load_data_from_file(self, file_path: str):
        """
        Load data from a JSON file.

        This method reads the content of a JSON file located at the specified file path
        and returns the loaded data as a Python object.

        Args:
            file_path (str): The path to the JSON file.

        Returns:
            dict or list: The loaded data from the JSON file.
        """
        with open(file_path, 'r') as file:
            loaded_data = json.load(file)

        return loaded_data

    def get_names_from_data(self, data: Dict):
        """
        Extract names from a list of dictionaries.

        This function takes a list of dictionaries and extracts the 'name' attribute
        from each dictionary, returning a list of names.

        Parameters:
        - data (list of dict): Input list containing dictionaries with 'name' attribute.

        Returns:
        - list: A list of names extracted from the 'name' attribute of each dictionary.
        """

        return [entry['name'] for entry in data]

    def generate_combinations(self, dictionary: Dict, exclude_keys: List):
        """
        Generate combinations of key-value pairs from a dictionary, excluding specified keys.

        This method takes a dictionary and a list of keys to exclude. It generates combinations
        of key-value pairs from the remaining keys in the dictionary after excluding the specified keys.

        Args:
            dictionary (dict): The original dictionary to generate combinations from.
            exclude_keys (list): The list of keys to exclude from the combinations.

        Returns:
            list: A list of dictionaries representing different combinations of key-value pairs.
        """
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

    def is_entry_present(self, data: List, entry: Dict):
        """
        Check if a specific entry is present in a list of dictionaries, ignoring the timestamp.

        This method iterates through a list of dictionaries and checks if the 'input' key
        in any dictionary matches the provided entry, ignoring the timestamp.

        Args:
            data (list): A list of dictionaries.
            entry: The entry to check for in the 'input' key.

        Returns:
            bool: True if the entry is present (ignoring timestamp), False otherwise.
        """
        # Check if the entry is present (ignoring timestamp)
        for i in data:
            if i.get("input") == entry:
                return True
        return False

    def add_entry_to_json(self, entry: Dict, file_path: str, error_message: str):
        """
        Add an entry to a JSON file, handling the presence of the entry and updating timestamps.

        This method loads existing JSON data from the specified file, checks if the provided entry
        is already present (ignoring timestamp), and adds the entry with a new timestamp and error message
        if it's not present. If the file doesn't exist, it initializes an empty list and adds the entry.

        Args:
            entry: The entry to be added to the JSON file.
            file_path (str): The path to the JSON file.
            error_message (str): The error message associated with the entry.

        Returns:
            None
        """
        # Load existing JSON data
        try:
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            # If the file doesn't exist, initialize an empty list
            data = []

        # Check if the entry is already present (ignoring timestamp)
        if not self.is_entry_present(data=data, entry=entry):
            # Add the entry to the data with a new timestamp
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

    def handle_error_entry(self, tool_name: str, entry, error_message: str):
        """
        Handle an error entry for a specific tool by adding it to a tool-specific JSON file.

        This method generates a tool-specific JSON file path based on the tool name, and then
        calls the 'add_entry_to_json' method to add the provided entry along with the error message
        to the JSON file. If the file doesn't exist, it initializes an empty list and adds the entry.

        Args:
            tool_name (str): The name of the tool associated with the error entry.
            entry: The entry to be added to the JSON file.
            error_message (str): The error message associated with the entry.

        Returns:
            None
        """
        file_path = f'{tool_name}_incorrect_combination.json'
        self.add_entry_to_json(entry=entry, file_path=file_path, error_message=error_message)

    def wait_for_job_completion(self, job_id: str):
        """
        Wait for the completion of a Galaxy job.

        This function continuously checks the state of a Galaxy job until it's not in a 'queued', 'running', or 'new' state.
        It waits for 5 seconds between each check.

        Parameters:
        - job_id (str): The ID of the Galaxy job to monitor.

        Returns:
        - str: The final state of the job.
        """
        while True:
            try:
                job_info = self.gi.jobs.show_job(job_id)
                print(job_info)
                print(self.gi.jobs.wait_for_job(job_id=job_id, interval=5, check=True))

                if job_info['state'] not in {'queued', 'running', 'new'}:
                    return job_info['state']

                time.sleep(5)

            except ConnectionError as e:
                print(f"Failed to connect to Galaxy: {e}")
                print("Retrying in 2 seconds...")
                print("Job")
                time.sleep(2)
