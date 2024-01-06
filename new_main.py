# from bioblend import galaxy
# from pprint import pprint
# from workflow import *
from galaxytools_workflow import *
import multiprocessing
import threading


# which server should be conncted
server = 'https://usegalaxy.eu/'
# api kex of account
api_key = f'mYjQOJmxwALJESXyMerBZpfuIoA4JDI'
history_name = "Metatranscriptomics Coding 13"


class GalaxyWorkflow:
    def __init__(self, server, api_key, history_name):
        self.server = server
        self.api_key = api_key
        self.history_name = history_name
        self.gi = Tool(server, api_key)
        self.tools = []
        self.input_ids = []

    def create_history(self):
        self.gi.create_history(history_name=self.history_name)
        self.gi.get_history_id(history_name=self.history_name)

    def get_history(self):
        self.gi.get_history_id(history_name=self.history_name)

    def upload_files(self, file_forward, file_reverse):
        self.input_ids.append(self.gi.upload_file(file_forward, "T1A_forward"))
        self.input_ids.append(self.gi.upload_file(file_reverse, "T1A_reverse"))

    def define_tools(self, file_forward, file_reverse):
        self.delete_dataset()
        if not self.input_ids:
            self.upload_files(file_forward, file_reverse)
        forward_id, reverse_id = self.input_ids
        workflow_ids = self.gi.workflow_input(forward_id=forward_id, reverse_id=reverse_id)
        a = self.gi.run_workflow(workflow_inputs=workflow_ids)
        pprint(a)
    
    def show_invocation(self, worfklow_id):
        z = self.gi.workflow_show_invocation(workflow_id=worfklow_id)
        pprint(len(z))
        pprint(z)
        self.gi.check_state_workflow(z)
    
    def delete_dataset(self):
        self.input_ids = self.gi.delete_dataset_and_datacollection()




    def run_tools(self, tool, parallel):
        # Modify the run_tools method to take the tool and parallel flag
        # and call run_tool_with_input_files with the tool and parallel flag
        tool.run_tool_with_input_files(tool.tool_name, parallel)

    def run_single(self, parallel):
        for tool in self.tools:
            self.run_tools(tool, parallel)

    def run_tools_parallel(self, parallel):
        threads = []
        for tool in self.tools:
            # Pass the tool and parallel flag to run_tools method
            thread = threading.Thread(target=self.run_tools, args=(tool, parallel))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()
    


def main():
    file_forward = "Upload_files/newfile_T1A_forward"
    # file_forward = "Upload_files/T1A_forward.fastqsanger"
    file_reverse = "Upload_files/newfile_T1A_reverse"
    # file_reverse = "Upload_files/T1A_reverse.fastqsanger"

    workflow = GalaxyWorkflow(server, api_key, history_name)
    #workflow.create_history()
    workflow.get_history()
    
    #workflow.upload_files(file_forward, file_reverse)
    #workflow.define_tools()
    #workflow.show_invocation("a1c8530242a0767b")
    #workflow.delete_dataset()
    workflow.define_tools(file_forward=file_forward, file_reverse=file_reverse)
    workflow.show_invocation("a1c8530242a0767b")
    #workflow.run_single(parallel=False)
    #workflow.print_dataset()
    

    #datasets_to_check = ["Gene families and their abundance", "Pathways and their abundance"]
    #workflow.run_renormalize_tool(datasets_to_check)


def test_multiple():
    workflow = GalaxyWorkflow(server, api_key, history_name)
    workflow.get_history()
    workflow.define_tools()
    workflow.run_tools_parallel(parallel=True)


def check_connection(server: str, api_key: str):
    gi = Tool(server, api_key)
    while True:
        time.sleep(30)
        gi.connect_to_galaxy_with_retry()


if __name__ == '__main__':
    process1 = multiprocessing.Process(target=main)
    process2 = multiprocessing.Process(target=check_connection, args=[server, api_key])
    #process3 = multiprocessing.Process(target=test_multiple)
    process1.start()
    process2.start()
    process1.join()
    #process3.start()
    #process3.join()
    process2.terminate()
