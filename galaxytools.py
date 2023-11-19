from bioblend import galaxy
from bioblend import ConnectionError
from pprint import pprint, PrettyPrinter
import re
import time
from typing import (
    List,
    Dict,
    Optional,
)


class Tool:
    def __init__(self, server: str, api_key: str) -> None:
        self.gi = galaxy.GalaxyInstance(url=server, key=api_key)
        self.history_id = ""
        self.tool_id = ""
        self.input_files = []

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
            self.gi.jobs.wait_for_job(job_id=job_id)
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
        _, self.tool_id = self.get_newest_tool_version_and_id(tool_name)
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
        return list with input_file format
        input_files = [
            {
                'src': 'hda',
                'id': input_data_id_1  # Replace with the actual input data ID
            }
        ]
        """
        return [{'src': 'hda', 'id': data_id} for data_id in input_data_ids]

    def run_tool(self, inputs: Dict):
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=self.tool_id, tool_inputs=inputs)
        job_id = job["jobs"][0]["id"]
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

    def write_to_file(self, data):
        with open('output.txt', 'w') as file:
            pp = PrettyPrinter(indent=4, stream=file)
            pp.pprint(data)
        file.close()

    def get_databases(self, inputs):
        # json_extract returns for every database a list with name, database_name, selected
        # return every database_name in a list
        return [inputs[i] for i in range(1, len(inputs), 3)]

    def remove_duplicate(self, orginal_list):
        unique_list = []
        for item in orginal_list:
            if item not in unique_list:
                unique_list.append(item)
        return unique_list

    def get_flattend_list(self, original_list):
        """
        Flatten a list of lists.

         Parameters:
            - original_list: The original list of lists.

        Returns:
            - flattened_list: The flattened list.
        """
        flattened_list = [element for sublist in original_list[0] for element in sublist]
        return flattened_list

    def json_extract(self, obj, key):
        """Recursively fetch values from nested JSON."""
        arr = []

        def extract(obj, arr: list, key):
            """Recursively search for values of key in JSON tree."""
            if isinstance(obj, dict):
                for _, v in obj.items():
                    if isinstance(v, (dict, list)):
                        extract(v, arr, key)
                    if v == key:
                        arr.append(obj.get("options", {}))
            elif isinstance(obj, list):
                for item in obj:
                    extract(item, arr, key)
            return arr
        values = extract(obj, arr, key)
        return values

    def get_datatables(self, tool_name, database_name):
        # Step 1: Get tool input options
        tool_tables = self.get_tool_input_options(tool_name)

        # Step 2: Extract input databases
        input_databases = self.json_extract(tool_tables, database_name)

        # Step 3: Remove duplicates
        unique_databases = self.remove_duplicate(input_databases)

        # Step 4: Flatten the list
        flattened_list = self.get_flattend_list(unique_databases)

        # Step 5: Get databases
        databases = self.get_databases(flattened_list)

        # return the result
        return (databases)


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

    def run_tool_with_input_files(self, tool_name: str):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names())
        inputs_1, inputs_2 = self.get_inputs(self.input_files)
        super().run_tool(inputs=inputs_1)
        super().run_tool(inputs=inputs_2)


class MultiQCTool(Tool):
    SOFTWARE = "fastqc"

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "MultiQC"

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

    def run_tool_with_input_files(self, tool_name: str):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names())
        inputs = self.get_inputs(self.input_files)
        super().run_tool(inputs=inputs)


class CutadaptTool(Tool):
    LIBRARY_TYPE = 'paired'
    MINIMUM_LENGTH = '150'
    QUALITY_CUTOFF = '20'
    OUTPUT_SELECTOR = 'report'

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "Cutadapt"

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

    def run_tool_with_input_files(self, tool_name):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names())
        inputs = self.get_inputs(self.input_files)
        super().run_tool(inputs=inputs)
        super().update_dataset_names(self.get_new_names_for_dataset(), self.get_output_names_of_cutadapt())


class SortMeRNATool(Tool):
    DATABASES_SELECTOR = 'cached'
    PAIRED_TYPE = '--paired_out'
    ALIGNED_FASTX_OTHER = 'True'
    LOG = 'True'
    INPUT_DATABASES = 'input_databases'

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "Filter with SortMeRNA"

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

    def run_tool_with_input_files(self, tool_name):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names())
        inputs = self.get_inputs(self.input_files)
        super().run_tool(inputs=inputs)

    def get_datatables(self):
        databases = super().get_datatables(self.tool_name, self.INPUT_DATABASES)
        pprint(databases)
        return databases


class FASTQinterlacerTool(Tool):
    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "FASTQ interlacer"

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

    def run_tool_with_input_files(self, tool_name: str):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names())
        inputs = self.get_inputs(self.input_files)
        super().run_tool(inputs=inputs)
        super().update_dataset_names(self.get_new_names_for_dataset(), self.get_output_names_of_interlacer())


class MetaPhlAnTool(Tool):
    SELECTOR = 'paired'
    STATE_Q = '0.1'
    KRONA_OUTPUT = "True"
    TAX_LEV_SPLIT_LEVELS = "True"

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "MetaPhlAn"

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

    def run_tool_with_input_files(self, tool_name: str):
        super().run_tool_with_input_files(tool_name, self.get_dataset_names())
        inputs = self.get_inputs(self.input_files)
        super().run_tool(inputs=inputs)


class HUMAnNTool(Tool):
    SELECTOR = 'bypass_taxonomic_profiling'
    HUMAnN_NUCLEOTIDE_DATABASE = 'chocophlan-full-3.6.0-29032023'
    HUMAnN_PROTEIN_DATABASE = 'uniref-uniref90_diamond-3.0.0-13052021'

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.tool_name = "HUMAnN"
        self.nucleotide_database = []
        self.protein_database = []

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

    def run_tool_with_input_files(self, tool_name: str):
        _, self.tool_id = self.get_newest_tool_version_and_id(tool_name)
        input_data_ids = self.get_input_data_ids(self.get_dataset_names())
        self.input_files = super().get_input_files(input_data_ids)
        self.get_datatables()
        inputs = self.get_inputs(
            self.input_files,
            nucleotide_database=self.HUMAnN_NUCLEOTIDE_DATABASE,
            protein_database=self.HUMAnN_PROTEIN_DATABASE
        )
        super().run_tool(inputs=inputs)

    def get_datatables(self):
        self.nucleotide_database = super().get_datatables(self.tool_name, "nucleotide_database")
        self.protein_database = super().get_datatables(self.tool_name, "protein_database")
        pprint(self.nucleotide_database)
        pprint(self.protein_database)


class RenormalizeTool(Tool):

    def __init__(self, server: str, api_key: str, history_id: str):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.pathway_name = ""

    def get_Inputs(self, inputs_files: List[str]):
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
        inputs = self.get_Inputs(self.input_files)
        super().run_tool(inputs=inputs)
        super().update_dataset_names(self.get_new_names_for_dataset(), self.get_output_names_of_renormalize())
