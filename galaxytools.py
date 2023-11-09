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
    
    def run_tool_with_one_Inputfile(self, tool_name, datasets_name):
        version = self.get_newest_tool_version_and_id(tool_name)
        self.tool_id = self.get_tool_id(version)
        input_data_id_1 = ''  # 
        input_data_id_2 = ''  # 
        dataset_name1,dataset_name2 = datasets_name
        datasets = (self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False))
        pprint(len(datasets))
        for dataset in datasets:
            if dataset_name1 == dataset["name"]:
                input_data_id_1 = dataset["id"]
                pprint(input_data_id_1)
                pprint(dataset["name"])
            if dataset_name2 == dataset["name"]:
                input_data_id_2 = dataset["id"]
                pprint(input_data_id_2)
                pprint(dataset["name"])


    def run_tool_with_two_Inputfiles(self, tool_name, datasets_name):
        version = self.get_newest_tool_version_and_id(tool_name)
        self.tool_id = self.get_tool_id(version)
        input_data_id_1 = ''  # 
        input_data_id_2 = ''  # 
        dataset_name1,dataset_name2 = datasets_name
        pprint(dataset_name1)
        pprint(self.history_id)
        datasets = (self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False))
        pprint(len(datasets))
        for dataset in datasets:
            if dataset_name1 == dataset["name"]:
                input_data_id_1 = dataset["id"]
                pprint(input_data_id_1)
                pprint(dataset["name"])
            if dataset_name2 == dataset["name"]:
                input_data_id_2 = dataset["id"]
                pprint(input_data_id_2)
                pprint(dataset["name"])

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
        self.input_files = self.get_Input_files(input_file_1=input_file_1,input_file_2=input_file_2)
        
    
    def get_Input_files(self,input_file_1, input_file_2) -> list:
        return [input_file_1, input_file_2]


class FastQCTool(Tool):

    def __init__(self, server, api_key, history_id):
        super().__init__(server, api_key)
        self.history_id = history_id
        pprint(history_id)
        pprint(self.history_id)
        pprint(self.input_files)
    
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
    
    def run_tool_with_two_Inputfiles(self, tool_name):
            super().run_tool_with_two_Inputfiles(tool_name, self.get_Datasetnames())
            pprint(self.input_files)
            inputs_1,inputs_2 = self.get_Inputs(self.input_files[0],self.input_files[1])
            job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=self.tool_id, tool_inputs=inputs_1)
            job_id = job["jobs"][0]["id"]
            self.gi.jobs.wait_for_job(job_id)
            job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=self.tool_id, tool_inputs=inputs_2)
            return job["jobs"][0]["id"]


class MultiQC(Tool):
    def run_MultiQC(self):
        # get latest release of the tool
        MultiQC_version = self.get_newest_tool_version_and_id("MultiQC")
        # get the tool Id of this release
        tool_id = self.get_tool_id(MultiQC_version)
        # get all datasets in the history, which are not deleted
        datasets = (self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False))
        # calculate the dataset id  of the dataset, which is needed for the next steps
        lst=[]
        for dataset in datasets:
            if "RawData" in dataset["name"]:
                lst.append(dataset["id"])

        input_data_id_1 = lst[1]  # Replace with the actual input data ID
        input_data_id_2 = lst[0]  # Replace with the actual input data ID
        input_files = [
            {
                'src': 'hda',
                'id': input_data_id_1  # Replace with the actual input data ID
            },
            {
                'src': 'hda',
                'id': input_data_id_2  # Replace with the actual input data ID
            }
        ]

        # Define the input with 'software' parameter set to 'fastqc' and multiple input files
        inputs = {
            'results_0|software_cond|software': 'fastqc',
            'results_0|software_cond|output_0|input': {
                'values': input_files
            }
        }
        # run tool
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id, tool_inputs=inputs)
        return job["jobs"][0]["id"]      

    def run_cutapdt(self):
        Cutadapt_version = self.get_newest_tool_version_and_id("Cutadapt")
        tool_id = self.get_tool_id(Cutadapt_version)
        input_data_id_1 = ''  # T1A_forward
        input_data_id_2 = ''  # T1A_backward
        datasets = (self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False))
        for dataset in datasets:
            if "T1A_forward" == dataset["name"]:
                input_data_id_1 = dataset["id"]
                pprint(input_data_id_1)
                pprint(dataset["name"])
            if "T1A_reverse" == dataset["name"]:
                input_data_id_2 = dataset["id"]
                pprint(input_data_id_2)
                pprint(dataset["name"])
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
        # Define the input with 'software' parameter set to 'fastqc' and multiple input files
        inputs = {
            'library|type': 'paired',
            'library|input_1': {
                'values': input_file_1
            },
            'library|input_2': {
                'values': input_file_2
            },
            'filter_options|minimum_length': '150',
            'read_mod_options|quality_cutoff': '20',
            'output_selector': 'report'
        }
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id, tool_inputs=inputs)
        datasets = (self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False))
        # Update name of datasets
        # Cutadapt Read 1 output to QC controlled forward reads
        # Cutadapt Read 2 output to QC controlled reverse reads

        dataset_id_Cutadapt_Read_1 = ""
        dataset_id_Cutadapt_Read_2 = ""
        for dataset in datasets:
            if "Cutadapt" and "Read 1 Output" in dataset["name"]:
                new_name = "QC controlled forward reads"
                dataset_id_Cutadapt_Read_1 = dataset["id"]
                dataset["name"] = new_name
                self.gi.histories.update_dataset(history_id=self.history_id, dataset_id=dataset_id_Cutadapt_Read_1, name=new_name)
            elif "Cutadapt" and "Read 2 Output" in dataset["name"]:
                new_name = "QC controlled reverse reads"
                dataset_id_Cutadapt_Read_2 = dataset["id"]
                dataset["name"] = new_name
                self.gi.histories.update_dataset(history_id=self.history_id, dataset_id=dataset_id_Cutadapt_Read_2, name=new_name)
        return job["jobs"][0]["id"]

    def run_SortMeRNA(self):
        SortMeRNA_version = self.get_newest_tool_version_and_id("Filter with SortMeRNA")
        # print(SortMeRNA_version)
        tool_id = self.get_tool_id(SortMeRNA_version)
        datasets = (self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False))
        input_data_id_1 = ''  # QC controlled forward reads
        input_data_id_2 = ''  # QC controlled reverse reads
        for dataset in datasets:
            if dataset["name"] == "QC controlled forward reads":
                input_data_id_1 = dataset["id"]
            if dataset["name"] == "QC controlled reverse reads":
                input_data_id_2 = dataset["id"]

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
            'sequencing_type|sequencing_type_selector': 'paired',
            'sequencing_type|forward_reads': {
                'values': input_file_1
            },
            'sequencing_type|reverse_reads': {
                'values': input_file_2
            },
            'sequencing_type|paired_type': '--paired_out',
            'databases_type|databases_selector': 'cached',
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
            'aligned_fastx|other': 'True',
            'log': 'True'
        }
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id, tool_inputs=inputs)
        return job["jobs"][0]["id"]

    def run_FASTQinterlacer(self):
        FASTQ_interlacer_version = self.get_newest_tool_version_and_id("FASTQ interlacer")
        tool_id = self.get_tool_id(FASTQ_interlacer_version)
        input_data_id_1 = ''  # unaligend forward reads
        input_data_id_2 = ''  # unaligned reverse reads
        datasets = (self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False))
        for dataset in datasets:
            if "Unaligned forward reads" in dataset["name"] and "SortMeRNA" in dataset["name"]:
                input_data_id_1 = dataset["id"]
                pprint(input_data_id_1)
                pprint(dataset["name"])
            if "Unaligned reverse reads" in dataset["name"] and "SortMeRNA" in dataset["name"]:
                input_data_id_2 = dataset["id"]
                pprint(input_data_id_2)
                pprint(dataset["name"])

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
            'reads|input1_file': {
                'values': input_file_1
            },
            'reads|input2_file': {
                'values': input_file_2
            },
        }
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id, tool_inputs=inputs)
        dataset_id_FASTQ_interlacer_pairs = ""
        datasets = (self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False))
        for dataset in datasets:
            if "FASTQ interlacer pairs" in dataset["name"]:
                # pprint("test")
                dataset_id_FASTQ_interlacer_pairs = dataset["id"]
                self.gi.histories.update_dataset(
                    history_id=self.history_id,
                    dataset_id=dataset_id_FASTQ_interlacer_pairs,
                    name="Interlaced non rRNA reads"
                )
        return job["jobs"][0]["id"]

    def run_MetaPhlAn(self):
        MetaPhlAn_version = self.get_newest_tool_version_and_id("MetaPhlAn")
        # print(MetaPhlAn_version)
        tool_id = self.get_tool_id(MetaPhlAn_version)
        # input_id = (self.gi.tools.build(tool_id=tool_id,history_id=self.history_id)["state_inputs"])
        # pprint(input_id)
        datasets = (self.gi.datasets.get_datasets(history_id=self.history_id, deleted=False))
        input_data_id_1 = ''  # QC controlled forward reads
        input_data_id_2 = ''  # QC controlled backward reads
        for dataset in datasets:
            if "QC controlled forward reads" in dataset["name"]:
                input_data_id_1 = dataset["id"]
                # pprint(dataset["id"])
                # pprint(dataset["name"])
            if "QC controlled reverse reads" in dataset["name"]:
                # pprint(dataset["id"])
                # pprint(dataset["name"])
                input_data_id_2 = dataset["id"]

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
            'inputs|in|raw_in|selector': 'paired',
            'inputs|in|raw_in|in_f': {
                'values': input_file_1
            },
            'inputs|in|raw_in|in_r': {
                'values': input_file_2
            },
            'analysis|analysis_type|tax_lev|split_levels': 'True',
            'analysis|stat_q': '0.1',
            'out|krona_output': 'True'
        }
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id, tool_inputs=inputs)
        return job["jobs"][0]["id"]

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


    
    
    

    


    