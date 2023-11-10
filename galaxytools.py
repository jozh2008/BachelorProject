from bioblend import galaxy
from bioblend import ConnectionError
from pprint import pprint
import re
import time
from urllib.parse import urljoin


class Tool:
    def __init__(self, server, api_key) -> None:
        self.gi = galaxy.GalaxyInstance(url=server, key=api_key)
        self.history_id = ""
        self.tool_id = ""
        self.input_files = []
    
    def connect_to_galaxy_with_retry(self):
        while True:
            try:
                self.gi.config.get_version()
                pprint(self.gi.config.get_version())
                return self.gi
            except ConnectionError as e:
                print(f"Failed to connect to Galaxy: {e}")
                print("Retrying in 2 seconds...")
                time.sleep(2)  # Wait for 2 seconds before retrying


    def upload_file(self, file1, file2):
        job = self.gi.tools.upload_file(path=file1, history_id=self.history_id, file_name="T1A_forward")
        job_id = job["jobs"][0]["id"]
        self.gi.jobs.wait_for_job(job_id=job_id)
        job = self.gi.tools.upload_file(path=file2, history_id=self.history_id, file_name="T1A_reverse")
        return job["jobs"][0]["id"]

    # for a given tool, give back the latest version and the id of this tool
    def get_newest_tool_version_and_id(self, tool_name):
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

    # calculates the history_id for a given history name
    def get_history_id(self, history_name):
        # check if connected to galaxy server
        self.connect_to_galaxy_with_retry()
        history = self.gi.histories.get_histories(name=history_name)
        history_id = history[0]["id"]
        self.history_id = history_id

    def create_history(self, history_name):
        # check if connected to galaxy server
        self.connect_to_galaxy_with_retry()
        histories = self.gi.histories.get_histories()
        # delete if history already exists
        if histories[0]["name"] == history_name:
            self.gi.histories.delete_history(histories[0]["id"])
        history = self.gi.histories.create_history(history_name)
        self.history_id = history["id"]

    # return just the tool_id of latest version
    def get_tool_id(self, tool_version):
        return tool_version[1]
    
    # wait until job is done, cause tools are dependent of each other
    def wait_for_job(self, job_id):
        self.gi.jobs.wait_for_job(job_id=job_id)

    # Define a custom key function to extract and compare version numbers
    def version_key(self, version):
        # Split the version string into components and convert them to integers
        parts = [int(part) for part in re.findall(r'\d+', version)]
        return tuple(parts)

    def get_Datasetnames(self):
        pass

    def get_Inputs(self):
        pass
    
    def run_tool_with_Inputfiles(self, tool_name, datasets_name):
        _ , self.tool_id = self.get_newest_tool_version_and_id(tool_name)
        input_data_ids = self.get_input_data_ids(datasets_name)
        pprint(input_data_ids)
        self.input_files = self.get_input_files(input_data_ids)


    def get_input_data_ids(self, dataset_names):
        dataset_ids = []
        datasets = self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False)
        for dataset_name in dataset_names:
            for dataset in datasets:
                if dataset_name in dataset["name"]:
                    dataset_ids.append(dataset["id"])
                    print(f"Found dataset '{dataset_name}' with ID: {dataset['id']}")

        return dataset_ids

    def get_input_files(self, input_data_ids):
        return [{'src': 'hda', 'id': data_id} for data_id in input_data_ids]
    
    def run_tool(self, inputs):
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=self.tool_id, tool_inputs=inputs)
        job_id = job["jobs"][0]["id"]
        self.wait_for_job(job_id)
        print(f"Tool '{self.tool_id}' has finished processing with job ID: {job_id}")
    
    def update_Dataset_names(self, update_names, old_names):
        input_data_ids = self.get_input_data_ids(old_names)
        for data_id, new_name in zip(input_data_ids, update_names):
            self.gi.histories.update_dataset(history_id=self.history_id, dataset_id=data_id, name=new_name)




class FastQCTool(Tool):

    def __init__(self, server, api_key, history_id):
        super().__init__(server, api_key)
        self.history_id = history_id
    
    def get_Inputs(self, input_file_1, input_file_2):
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
        return inputs_1,inputs_2

    def get_Datasetnames(self):
        dataset_name_1 = "T1A_forward"
        dataset_name_2 = "T1A_reverse"
        return dataset_name_1,dataset_name_2
    
    def run_tool_with_Inputfiles(self, tool_name):
            super().run_tool_with_Inputfiles(tool_name, self.get_Datasetnames())
            inputs_1,inputs_2 = self.get_Inputs(self.input_files[0],self.input_files[1])
            super().run_tool(inputs=inputs_1)
            super().run_tool(inputs=inputs_2)


class MultiQCTool(Tool):
    SOFTWARE = "fastqc"
    def __init__(self, server, api_key, history_id):
        super().__init__(server, api_key)
        self.history_id = history_id
    

    def get_Inputs(self, input_files):
        pprint(input_files)
        inputs = {
            'results_0|software_cond|software': self.SOFTWARE,
            'results_0|software_cond|output_0|input': {
                'values': input_files
            }
        }
        return inputs

    def get_Datasetnames(self):
        return "FastQC on data 1: RawData", "FastQC on data 2: RawData"

    def run_tool_with_Inputfiles(self, tool_name):
        super().run_tool_with_Inputfiles(tool_name, self.get_Datasetnames())
        inputs = self.get_Inputs(self.input_files)
        super().run_tool(inputs=inputs)

class CutadaptTool(Tool):
    LIBRARY_TYPE = 'paired'
    MINIMUM_LENGTH = '150'
    QUALITY_CUTOFF = '20'
    OUTPUT_SELECTOR = 'report'
    def __init__(self, server, api_key, history_id):
        super().__init__(server, api_key)
        self.history_id = history_id
    
    def get_Inputs(self, inputs_files):
        input_file_1,input_file_2 =inputs_files
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

    def get_Datasetnames(self):
        return "T1A_forward", "T1A_reverse"

    def get_new_Names_for_Dataset(self):
        return "QC controlled forward reads", "QC controlled reverse reads"
    
    def get_Output_Names_Of_Cutadapt(self):
        return "Read 1 Output", "Read 2 Output"

    def run_tool_with_Inputfiles(self, tool_name):
        super().run_tool_with_Inputfiles(tool_name, self.get_Datasetnames())
        inputs = self.get_Inputs(self.input_files)
        super().run_tool(inputs=inputs)
        super().update_Dataset_names(self.get_new_Names_for_Dataset(), self.get_Output_Names_Of_Cutadapt())  
    
class SortMeRNATool(Tool):
    DATABASES_SELECTOR = 'cached'
    PAIRED_TYPE = '--paired_out'
    ALIGNED_FASTX_OTHER = 'True'
    LOG = 'True'

    def __init__(self, server, api_key, history_id):
        super().__init__(server, api_key)
        self.history_id = history_id

    def get_Inputs(self, inputs_files):
        input_file_1,input_file_2 =inputs_files
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
            'databases_type|input_databases': [
                '2.1b-silva-arc-16s-id95',
                '2.1b-silva-euk-28s-id98',
                '2.1b-silva-euk-18s-id95',
                '2.1b-silva-bac-23s-id98',
                '2.1b-silva-bac-16s-id90',
                '2.1b-rfam-5.8s-database-id98',
                '2.1b-rfam-5s-database-id98',
                '2.1b-silva-arc-23s-id98'
            ],
            'aligned_fastx|other': self.ALIGNED_FASTX_OTHER,
            'log': self.LOG
        }
        return inputs   
    
    def get_Datasetnames(self):
        return "QC controlled forward reads", "QC controlled reverse reads"
    
    def run_tool_with_Inputfiles(self, tool_name):
        super().run_tool_with_Inputfiles(tool_name, self.get_Datasetnames())
        inputs = self.get_Inputs(self.input_files)
        super().run_tool(inputs=inputs)


class FASTQinterlacerTool(Tool):
    def __init__(self, server, api_key, history_id):
        super().__init__(server, api_key)
        self.history_id = history_id
    
    def get_Inputs(self, inputs_files):
        input_file_1,input_file_2 =inputs_files
        inputs = {
            'reads|input1_file': {
                'values': input_file_1
            },
            'reads|input2_file': {
                'values': input_file_2
            },
        }
        return inputs

    def get_Datasetnames(self):
        return "Unaligned forward reads", "Unaligned reverse reads"
    
    def get_new_Names_for_Dataset(self):
        return ["Interlaced non rRNA reads"]
    
    def get_Output_Names_Of_Cutadapt(self):
        return ["FASTQ interlacer pairs"]
    
    def run_tool_with_Inputfiles(self, tool_name):
        super().run_tool_with_Inputfiles(tool_name, self.get_Datasetnames())
        inputs = self.get_Inputs(self.input_files)
        super().run_tool(inputs=inputs)
        super().update_Dataset_names(self.get_new_Names_for_Dataset(), self.get_Output_Names_Of_Cutadapt())

class MetaPhlAnTool(Tool):
    SELECTOR = 'paired'
    STATE_Q = '0.1'
    KRONA_OUTPUT = "True"
    TAX_LEV_SPLIT_LEVELS = "True"

    def __init__(self, server, api_key, history_id):
        super().__init__(server, api_key)
        self.history_id = history_id

    def get_Inputs(self, inputs_files):
        input_file_1,input_file_2 =inputs_files
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
    
    def get_Datasetnames(self):
        return "QC controlled forward reads", "QC controlled reverse reads"
    
    def run_tool_with_Inputfiles(self, tool_name):
        super().run_tool_with_Inputfiles(tool_name, self.get_Datasetnames())
        inputs = self.get_Inputs(self.input_files)
        super().run_tool(inputs=inputs)


class HUMAnNTool(Tool):

    def __init__(self, server, api_key, history_id):
        super().__init__(server, api_key)
        self.history_id = history_id
    
    def get_Inputs(self, inputs_files):
        input_file_1,input_file_2 =inputs_files
        inputs = {
            'in|input': {
                'values': input_file_1
            },
            'wf|selector|': 'bypass_taxonomic_profiling',
            'wf|bypass_taxonomic_profiling|--taxonomic-profile': {
                'values': input_file_2
            },
            'wf|nucleotide_search|nucleotide_db|nucleotide_database': 'chocophlan-full-3.6.0-29032023',
            'wf|translated_search|protein_db|protein_database': 'uniref-uniref90_diamond-3.0.0-13052021'
        }
        return inputs
    
    def get_Datasetnames(self):
        return "Interlaced non rRNA reads", "Predicted taxon relative abundances"

    def get_input_data_ids(self, dataset_names):
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
    
    def run_tool_with_Inputfiles(self, tool_name):
        _ , self.tool_id = self.get_newest_tool_version_and_id(tool_name)
        input_data_ids = self.get_input_data_ids(self.get_Datasetnames())
        self.input_files = super().get_input_files(input_data_ids)
        inputs = self.get_Inputs(self.input_files)
        super().run_tool(inputs=inputs)

    def run_HUMAnN(self):
        HUMAnN_version = self.get_newest_tool_version_and_id("HUMAnN")
        print(HUMAnN_version)
        tool_id = self.get_tool_id(HUMAnN_version)
        input_id = (self.gi.tools.build(tool_id=tool_id, history_id=self.history_id)["state_inputs"])
        pprint(input_id)
        datasets = (self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False))
        input_data_id_1 = ''  # Interlaced non rRNA reads
        input_data_id_2 = ''  # Interlaced non rRNA reads
        for dataset in datasets:
            if "Interlaced non rRNA reads" == dataset["name"]:
                input_data_id_1 = dataset["id"]
            if ("Predicted taxon relative abundances" in dataset["name"]
                    and "Krona" not in dataset["name"]
                    and "taxonomic levels" not in dataset["name"]):
                input_data_id_2 = dataset["id"]
                # pprint(dataset["name"])

        input_file_1 = [
            {
                'src': 'hda',
                'id': input_data_id_1  # Replace with the actual input data ID
            }
        ]
        input_file_2 = [
            {
                'src': 'hda',
                'id': input_data_id_2  # Replace with the actual input data ID
            }
        ]
        inputs = {
            'in|input': {
                'values': input_file_1
            },
            'wf|selector|': 'bypass_taxonomic_profiling',
            'wf|bypass_taxonomic_profiling|--taxonomic-profile': {
                'values': input_file_2
            },
            'wf|nucleotide_search|nucleotide_db|nucleotide_database': 'chocophlan-full-3.6.0-29032023',
            'wf|translated_search|protein_db|protein_database': 'uniref-uniref90_diamond-3.0.0-13052021'
        }
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id, tool_inputs=inputs)
        return job["jobs"][0]["id"]

class RenormalizeTool(Tool):

    def __init__(self, server, api_key, history_id):
        super().__init__(server, api_key)
        self.history_id = history_id
        self.pathway_name = ""

    def get_Inputs(self, inputs_files):
        input_file_1 = inputs_files
        inputs = {
            'input': {
                'values': input_file_1
            },
            'units': 'relab',
        }
        return inputs
    
    def get_Datasetnames(self, name):
        self.pathway_name = name
        return [name]

    def get_new_Names_for_Dataset(self):
        name = ""
        if self.pathway_name == "Gene families and their abundance":
            name = "Normalized gene families"
        elif self.pathway_name == "Pathways and their abundance":
            name = "Normalized pathways"
        return [name]
    
    def get_Output_Names_Of_Cutadapt(self):
        return ["Renormalize"]
    
    def run_tool_with_Inputfiles(self, tool_name):
        super().run_tool_with_Inputfiles(tool_name, self.get_Datasetnames(self.pathway_name))
        inputs = self.get_Inputs(self.input_files)
        super().run_tool(inputs=inputs)
        super().update_Dataset_names(self.get_new_Names_for_Dataset(), self.get_Output_Names_Of_Cutadapt())   

    def run_Renormalize(self):
        Renormalize_version = self.get_newest_tool_version_and_id("Renormalize")
        print(Renormalize_version)
        tool_id = self.get_tool_id(Renormalize_version)
        input_id = (self.gi.tools.build(tool_id=tool_id, history_id=self.history_id)["state_inputs"])
        pprint(input_id)
        datasets = (self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False))
        input_data_id_1 = ''  # Interlaced non rRNA reads
        for dataset in datasets:
            if "Gene families and their abundance" in dataset["name"]:
                input_data_id_1 = dataset["id"]
                pprint(dataset["name"])

        input_file_1 = [
            {
                'src': 'hda',
                'id': input_data_id_1  # Replace with the actual input data ID
            }
        ]
        inputs = {
            'input': {
                'values': input_file_1
            },
            'units': 'relab',
        }
        self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id, tool_inputs=inputs)
        datasets = (self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False))
        for dataset in datasets:
            if "Renormalize" in dataset["name"]:
                pprint("test")
                dataset_id_FASTQ_interlacer_pairs = dataset["id"]
                self.gi.histories.update_dataset(
                    history_id=self.history_id,
                    dataset_id=dataset_id_FASTQ_interlacer_pairs,
                    name="Normalized gene families"
                )
