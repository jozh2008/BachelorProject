from galaxytools_workflow import *
import multiprocessing
import yaml
from file_downloader import FileDownloader


# which server should be conncted
server = 'https://usegalaxy.eu/'
#server = "http://localhost:8080/"
# api kex of account
api_key = "mYjQOJmxwALJESXyMerBZpfuIoA4JDI"
#api_key = "ff269704f8decd8811ef2d9824ba869e"
history_name = "Metatranscriptomics Coding 2"


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
    
    def show_invocation(self):
        z = self.gi.workflow_show_invocation()
        pprint(len(z))
        pprint(z)
        self.gi.check_state_workflow(z)
    
    def delete_dataset(self):
        self.input_ids = self.gi.delete_dataset_and_datacollection()
    

def load_config(file_path='config.yml'):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def initialize_workflow(config):
    file_downloader = FileDownloader()

# Download and rename files
    for file_info in config["files"]:
        url = file_info["url"]
        destination_folder = file_info["destination_folder"]
        rename_to = file_info["rename_to"]

        downloaded_file_path = file_downloader.download_file(url, destination_folder)
        file_downloader.rename_file(downloaded_file_path, rename_to)

    # Download workflow file
    workflow_url = config["workflow"]["url"]
    workflow_destination_folder = config["workflow"]["destination_folder"]
    file_downloader.download_file(workflow_url, workflow_destination_folder)

def main():
    file_forward = "Upload_files/newfile_T1A_forward"
    # file_forward = "Upload_files/T1A_forward.fastqsanger"
    file_reverse = "Upload_files/newfile_T1A_reverse"
    # file_reverse = "Upload_files/T1A_reverse.fastqsanger"
    config = load_config()
    initialize_workflow(config=config)
    workflow = GalaxyWorkflow(config['server'], config['api_key'], config['history_name'])
    workflow.get_history()
    
    workflow.define_tools(file_forward=file_forward, file_reverse=file_reverse)
    workflow.show_invocation()


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
