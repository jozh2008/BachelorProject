from bioblend import galaxy
from pprint import pprint, PrettyPrinter
import re

class Tool:
    def __init__(self, server, api_key) -> None:
        self.gi = galaxy.GalaxyInstance(url = server, key = api_key)
        self.history_id =""
        #pprint(self.gi)
        #pprint(self.gi.config.get_version())

    def upload_file(self, file1, file2):
       # get the history id to upload files
       # pprint(self.history_id)

       job = self.gi.tools.upload_file(path=file1, history_id=self.history_id,file_name="T1A_forward")
       job_id = job["jobs"][0]["id"]
       self.gi.jobs.wait_for_job(job_id=job_id)
       job = self.gi.tools.upload_file(path=file2, history_id=self.history_id, file_name="T1A_reverse")
       return job["jobs"][0]["id"]


    # for a given tool, give back the latest version and the id of this tool
    def get_newest_tool_version_and_id(self, tool_name):
        tools = (self.gi.tools.get_tools(name=tool_name))
        lst_version = [] # list to save all version of this tool
        lst2 = [] # 
        for tool in tools:
            lst_version.append(tool["version"])
        a = (self.version_key_modified(lst_version))
        newest_version = max(list(a.keys()), key=self.version_key)
        lst2 = a[newest_version]
        res = newest_version + sorted(lst2,reverse=True)[0]

        tool_id = ""
        for tool in tools:
            if res == tool["version"]:
                tool_id =tool["id"]

        return (res,tool_id) # s
    
    # calculates the history_id for a given history name
    def get_history_id(self, history_name):
        history = self.gi.histories.get_histories(name = history_name)
        ##pprint(history)
        history_id = history[0]["id"]
        self.history_id = history_id
    
    def create_history(self, history_name):
        histories = self.gi.histories.get_histories() 
        #self.gi.histories.create_history(history_name)
        #pprint(histories)
        if histories[0]["name"] == history_name:
            self.gi.histories.delete_history(histories[0]["id"])
        self.gi.histories.create_history(history_name)
            
    # return just the tool_id of latest version
    def get_tool_id(self, tool_version):
        return tool_version[1]

    def run_MultiQC(self):
        # get latest release of the tool
        MultiQC_version = self.get_newest_tool_version_and_id("MultiQC")
        # get the tool Id of this release
        tool_id = self.get_tool_id(MultiQC_version)
        # get all datasets in the history, which are not deleted
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
        lst = []
        # calculate the dataset id  of the dataset, which is needed for the next steps
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
                            'id': input_data_id_2 # Replace with the actual input data ID
                        }

                        # Add more input files as needed
                    ]
        # Define the input with 'software' parameter set to 'fastqc' and multiple input files
        inputs = {
            'results_0|software_cond|software': 'fastqc',
            'results_0|software_cond|output_0|input': {
                'values': input_files
            }
        }
        #run tool
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id,tool_inputs=inputs)
        return job["jobs"][0]["id"]

    def run_cutapdt(self):
        Cutadapt_version = self.get_newest_tool_version_and_id("Cutadapt")
        tool_id = self.get_tool_id(Cutadapt_version)
        input_data_id_1 = ''  # T1A_forward
        input_data_id_2 = ''  # T1A_backward
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
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
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id,tool_inputs=inputs)
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
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
                self.gi.histories.update_dataset(history_id=self.history_id,dataset_id=dataset_id_Cutadapt_Read_1,name=new_name)
            elif "Cutadapt" and "Read 2 Output" in dataset["name"]:
                new_name = "QC controlled reverse reads"
                dataset_id_Cutadapt_Read_2 = dataset["id"]
                dataset["name"] = new_name
                self.gi.histories.update_dataset(history_id=self.history_id,dataset_id=dataset_id_Cutadapt_Read_2,name=new_name)
        return job["jobs"][0]["id"]

    def run_SortMeRNA(self):
        SortMeRNA_version = self.get_newest_tool_version_and_id("Filter with SortMeRNA")
        print(SortMeRNA_version)
        tool_id = self.get_tool_id(SortMeRNA_version)
        input_id = (self.gi.tools.build(tool_id=tool_id,history_id=self.history_id)["state_inputs"])
        pprint(input_id)
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
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
            'databases_type|input_databases': ['2.1b-silva-arc-16s-id95','2.1b-silva-euk-28s-id98','2.1b-silva-euk-18s-id95','2.1b-silva-bac-23s-id98','2.1b-silva-bac-16s-id90','2.1b-rfam-5.8s-database-id98','2.1b-rfam-5s-database-id98','2.1b-silva-arc-23s-id98'],
            'aligned_fastx|other': 'True',
            'log': 'True'
        }
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id,tool_inputs=inputs)
        return job["jobs"][0]["id"]
    
    def run_FASTQinterlacer(self):
        FASTQ_interlacer_version = self.get_newest_tool_version_and_id("FASTQ interlacer")
        tool_id = self.get_tool_id(FASTQ_interlacer_version)
        input_data_id_1 = ''  # unaligend forward reads
        input_data_id_2 = ''  # unaligned reverse reads
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
        for dataset in datasets:
            if "Unaligned forward reads"  in dataset["name"] and "SortMeRNA" in dataset["name"]:
                input_data_id_1 = dataset["id"]
                pprint(input_data_id_1)
                pprint(dataset["name"])
            if "Unaligned reverse reads"  in dataset["name"] and "SortMeRNA" in dataset["name"]:
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
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id,tool_inputs=inputs)
        dataset_id_FASTQ_interlacer_pairs = ""
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
        for dataset in datasets:
            if "FASTQ interlacer pairs" in dataset["name"]:
                pprint("test")
                dataset_id_FASTQ_interlacer_pairs =dataset["id"]
                self.gi.histories.update_dataset(history_id=self.history_id,dataset_id=dataset_id_FASTQ_interlacer_pairs,name="Interlaced non rRNA reads")
        return job["jobs"][0]["id"]

    def run_MetaPhlAn(self):
        MetaPhlAn_version = self.get_newest_tool_version_and_id("MetaPhlAn")
        #print(MetaPhlAn_version)
        tool_id = self.get_tool_id(MetaPhlAn_version)
        input_id = (self.gi.tools.build(tool_id=tool_id,history_id=self.history_id)["state_inputs"])
        pprint(input_id)
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
        input_data_id_1 = ''  # QC controlled forward reads
        input_data_id_2 = ''  # QC controlled backward reads
        for dataset in datasets:
            if "QC controlled forward reads" in dataset["name"]:
                input_data_id_1 = dataset["id"]
                pprint(dataset["id"])
                pprint(dataset["name"])
            if "QC controlled reverse reads" in dataset["name"]:
                pprint(dataset["id"])
                pprint(dataset["name"])
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
            'analysis': {
                'analysis_type':{
                    'tax_lev':{
                        'split_levels': 'True'
                    }
                
                },
                'stat_q':'0.1'
            },
            'analysis|analysis_type|tax_lev|split_levels': 'True',
            'analysis|stat_q':'0.1',
            'out|krona_output' :'True'   
        }
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id,tool_inputs=inputs)
        return job["jobs"][0]["id"]

    def run_HUMAnN(self):
        HUMAnN_version = self.get_newest_tool_version_and_id("HUMAnN")
        print(HUMAnN_version)
        tool_id = self.get_tool_id(HUMAnN_version)
        input_id = (self.gi.tools.build(tool_id=tool_id,history_id=self.history_id)["state_inputs"])
        pprint(input_id)
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))        
        input_data_id_1 = ''  # Interlaced non rRNA reads 
        input_data_id_2 = ''  # Interlaced non rRNA reads 
        for dataset in datasets:
            if "Interlaced non rRNA reads" == dataset["name"]:
                input_data_id_1 = dataset["id"]
            if "Predicted taxon relative abundances" in dataset["name"] and "Krona" not in dataset["name"] and "taxonomic levels" not in dataset["name"]:
                input_data_id_2 = dataset["id"]
                #pprint(dataset["name"])

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
            'wf|selector|':'bypass_taxonomic_profiling',
            'wf|bypass_taxonomic_profiling|--taxonomic-profile': {
                'values': input_file_2
            },
            'wf|nucleotide_search|nucleotide_db|nucleotide_database': 'chocophlan-full-3.6.0-29032023',
            'wf|translated_search|protein_db|protein_database': 'uniref-uniref90_diamond-3.0.0-13052021' 
        }
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id,tool_inputs=inputs)
        return job["jobs"][0]["id"]

    def run_Renormalize(self):
        Renormalize_version = self.get_newest_tool_version_and_id("Renormalize")
        print(Renormalize_version)
        tool_id = self.get_tool_id(Renormalize_version)
        input_id = (self.gi.tools.build(tool_id=tool_id,history_id=self.history_id)["state_inputs"])
        pprint(input_id)
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
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
        self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id,tool_inputs=inputs)
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
        for dataset in datasets:
            if "Renormalize" in dataset["name"]:
                pprint("test")
                dataset_id_FASTQ_interlacer_pairs =dataset["id"]
                self.gi.histories.update_dataset(history_id=self.history_id,dataset_id=dataset_id_FASTQ_interlacer_pairs,name="Normalized gene families")



    def run_tool(self, tool_name):
        FastQC_version = self.get_newest_tool_version_and_id(tool_name)
        tool_id = self.get_tool_id(FastQC_version)
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
        lst = []
        for dataset in datasets:
            #pprint(dataset)
            lst.append(dataset["id"])
        input_id = (self.gi.tools.build(tool_id=tool_id,history_id=self.history_id)["state_inputs"])
        # reverse file 
        # forward file
        #pprint(input_id)
        input_data_id_1 = ''  # T1A_forward
        input_data_id_2 = ''  # T1A_backward
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
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
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id,tool_inputs=inputs_1)
        job_id = job["jobs"][0]["id"]
        self.gi.jobs.wait_for_job(job_id)
        job = self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id,tool_inputs=inputs_2)
        return job["jobs"][0]["id"]
        
     # wait until job is done, cause tools are dependent of each other   
    def wait_for_job(self, job_id):
        self.gi.jobs.wait_for_job(job_id=job_id)
        
# Define a custom key function to extract and compare version numbers
    def version_key(self, version):
        # Split the version string into components and convert them to integers
        parts = [int(part) for part in re.findall(r'\d+', version)]
        return tuple(parts)


    def version_key_modified(self, version):
        """
        version has the following format:
            X.XX.XX+galaxyX
        so to get the latest version, we need split the verion into numbers, and the +galaxy
        i.e 3.07.2+galaxy1 will the key be 3.07.2 and the value galaxy1
        we save everything in a dictionary
        """
        d = dict()
        helperKey = ""
        helperValue = ""
        for ver in version:
            position = ver.find("+") # postion of +, cause seperator
            if position != -1: # if -1 then there is no +galaxy part
                helperKey = ver[:position]
                helperValue = ver[position:]
            else:
                helperKey = ver
                helperValue = ""
            if helperKey not in d:
                d[helperKey] = [helperValue]
            else:
                d[helperKey]= d[helperKey] + [helperValue]
        return(d)


