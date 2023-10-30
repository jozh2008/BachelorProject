from bioblend import galaxy
from pprint import pprint, PrettyPrinter
import re

class Tool:
    def __init__(self, server, api_key) -> None:
        self.gi = galaxy.GalaxyInstance(url = server, key = api_key)
        self.history_id =""
        pprint(self.gi)

    def upload_file(self, file1, file2):
       # get the history id to upload files

       self.gi.tools.upload_file(path=file1, history_id=self.get_history_id, file_name="T1A_forward")
       self.gi.tools.upload_file(path=file2, history_id=self.get_history_id, file_name="T1A_reverse")


    # for a given tool, give back the latest version and the id of this tool
    def get_newest_tool_version_and_id(self, tool_name):
        tools = (self.gi.tools.get_tools(name=tool_name))
        #pprint(tools)
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
        # pprint(history)
        history_id = history[0]["id"]
        self.history_id = history_id
    
    # return just the tool_id of latest version
    def get_tool_id(self, tool_version):
        return tool_version[1]

    def preprocessing(self):

        MultiQC_version = self.get_newest_tool_version_and_id("MultiQC")
        tool_id = self.get_tool_id(MultiQC_version)
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
        # pprint(datasets)
        lst = []
        for dataset in datasets:
            lst.append(dataset["id"])

        input_data_id_1 = '4838ba20a6d8676517bf4126fdd2dd8b'  # Replace with the actual input data ID
        input_data_id_2 = '4838ba20a6d867651787f6001f11eacc'  # Replace with the actual input data ID
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
        self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id,tool_inputs=inputs)

    def run_cutapdt(self):
        Cutadapt_version = self.get_newest_tool_version_and_id("Cutadapt")
        print(Cutadapt_version)
        tool_id = self.get_tool_id(Cutadapt_version)
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
        lst = []
        for dataset in datasets:
            pprint(dataset)
            lst.append(dataset["id"])
        input_id = (self.gi.tools.build(tool_id=tool_id,history_id=self.history_id)["state_inputs"])
        pprint(input_id)
        input_data_id_1 = '4838ba20a6d86765c677cabf65b7c1df'  # Replace with the actual input data ID
        input_data_id_2 = '4838ba20a6d8676558983208f01dea12'  # Replace with the actual input data ID
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
            'read_mod_options|quality_cutoff': '0',
            'output_selector': 'report'
        }
        self.gi.tools.run_tool(history_id=self.history_id, tool_id=tool_id,tool_inputs=inputs)
    
    def run_tool(self, tool_name):
        FastQC_version = self.get_newest_tool_version_and_id(tool_name)
        tool_id = self.get_tool_id(FastQC_version)
        datasets=(self.gi.datasets.get_datasets(history_id=self.history_id,deleted=False))
        lst = []
        for dataset in datasets:
            pprint(dataset)
            lst.append(dataset["id"])
        input_id = (self.gi.tools.build(tool_id=tool_id,history_id=self.history_id)["state_inputs"])
        # reverse file 
        #self.gi.tools.run_tool(self.history_id, tool_id, input_id )
        # forward file
        #print(len(lst))
        h1 = input_id["input_file"]
        h2 = h1["values"][0]
        d = h2.copy()
        d["id"] = lst[len(lst)-1]
        h1["values"] = [d]
        #pprint(input_id)
        h4 = (self.gi.tools.build(tool_id=tool_id,history_id=self.history_id)["state_inputs"])
        #pprint(h4)
        self.gi.tools.run_tool(self.history_id, tool_id, input_id )

        

        
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


