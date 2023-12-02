# from bioblend import galaxy
# from pprint import pprint
# from workflow import *
from galaxytools import *
import multiprocessing
# which server should be conncted
server = 'https://usegalaxy.eu/'
# api kex of account
api_key = 'mYjQOJmxwALJESXyMerBZpfuIoA4JDI'

class GalaxyWorkflow:
    def __init__(self, server, api_key, history_name):
        self.server = server
        self.api_key = api_key
        self.history_name = history_name
        self.gi = Tool(server, api_key)
        self.tools = []

    def create_history(self):
        # self.gi.create_history(history_name=self.history_name)
        self.gi.get_history_id(history_name=self.history_name)

    def upload_files(self, file_forward, file_reverse):
        self.gi.upload_file(file_forward, "T1A_forward")
        self.gi.upload_file(file_reverse, "T1A_reverse")
    
    def define_tools(self):
        self.tools = [
            #FastQCTool(server=server, api_key=api_key, history_id=self.gi.history_id),
            MultiQCTool(server=server, api_key=api_key, history_id=self.gi.history_id),
            CutadaptTool(server=server, api_key=api_key, history_id=self.gi.history_id),
            #SortMeRNATool(server=server, api_key=api_key, history_id=self.gi.history_id),
            #FASTQinterlacerTool(server=server, api_key=api_key, history_id=self.gi.history_id),
            #MetaPhlAnTool(server=server, api_key=api_key, history_id=self.gi.history_id),
            #HUMAnNTool(server=server, api_key=api_key, history_id=self.gi.history_id)
        ]

    def run_tools(self):
        for tool in self.tools:
            #tool.show_tool_input(tool.tool_name)
            tool.run_tool_with_input_files(tool.tool_name,True)
            
            

    def run_renormalize_tool(self, datasets_to_check):
        re = RenormalizeTool(server=self.server, api_key=self.api_key, history_id=self.gi.history_id)
        for dataset in datasets_to_check:
            re.get_dataset_names(dataset)
            re.run_tool_with_input_files("Renormalize")



def main():
    file_forward = "Upload_files/newfile_T1A_forward"
    #file_forward = "Upload_files/T1A_forward.fastqsanger"
    file_reverse = "Upload_files/newfile_T1A_reverse"
    #file_reverse = "Upload_files/T1A_reverse.fastqsanger"
    history_name = "Metatranscriptomics Coding 6"

    workflow = GalaxyWorkflow(server, api_key, history_name)
    workflow.create_history()
    # workflow.upload_files(file_forward, file_reverse)
    workflow.define_tools()
    workflow.run_tools()

    #datasets_to_check = ["Gene families and their abundance", "Pathways and their abundance"]
    #workflow.run_renormalize_tool(datasets_to_check)

def check_connection(server: str, api_key: str):
    gi = Tool(server, api_key)
    while True:
        time.sleep(30)
        gi.connect_to_galaxy_with_retry()


if __name__ == '__main__':
    process1 = multiprocessing.Process(target=main)
    process2 = multiprocessing.Process(target=check_connection, args=[server, api_key])
    process1.start()
    process2.start()
    process1.join()
    process2.terminate()
