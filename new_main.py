from galaxytools_workflow import *
import multiprocessing
import yaml
from file_downloader import FileDownloader

server = 'https://usegalaxy.eu/'
api_key = "mYjQOJmxwALJESXyMerBZpfuIoA4JDI"


class GalaxyWorkflow:
    def __init__(self, server, api_key, history_name):
        self.server = server
        self.api_key = api_key
        self.history_name = history_name
        self.gi = Tool(server, api_key)
        self.tools = []
        self.input_ids = []

    def get_history(self):
        self.gi.get_history_id(history_name=self.history_name)

    def upload_files(self, file_forward, file_reverse):
        self.input_ids.append(self.gi.upload_file(file_forward, "T1A_forward"))
        self.input_ids.append(self.gi.upload_file(file_reverse, "T1A_reverse"))

    def define_tools(self, file_forward, file_reverse, file_workflow):
        self.delete_dataset()
        if not self.input_ids:
            self.upload_files(file_forward, file_reverse)
        forward_id, reverse_id = self.input_ids
        workflow_ids = self.gi.workflow_input(forward_id=forward_id, reverse_id=reverse_id)
        self.gi.run_workflow(workflow_inputs=workflow_ids, file_workflow=file_workflow)

    def show_invocation(self):
        """
        Display information about the current state of a workflow invocation.

        This function retrieves information about the current state of a workflow invocation,
        prints the length of the result, and then checks the state of the workflow.

        Returns:
            None
        """
        # Retrieve information about the workflow invocation
        workflow_invocation_info = self.gi.workflow_show_invocation()

        # Print the length and details of the retrieved information
        pprint(f"Length of workflow invocation information: {len(workflow_invocation_info)}")
        pprint(workflow_invocation_info)

        # Check the state of the workflow
        self.gi.check_state_workflow(workflow_invocation_info)

    def delete_dataset(self):
        self.input_ids = self.gi.delete_dataset_and_datacollection()


def load_config(file_path='config.yml'):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def initialize_workflow(config):
    file_downloader = FileDownloader()
    file_path = []

    # Download and rename files
    for file_info in config["files"]:
        url = file_info["url"]
        destination_folder = file_info["destination_folder"]
        rename_to = file_info["rename_to"]

        downloaded_file_path = file_downloader.download_file(url, destination_folder)
        file_path.append(file_downloader.rename_file(downloaded_file_path, rename_to))

    # Download workflow file
    workflow_url = config["workflow"]["url"]
    workflow_destination_folder = config["workflow"]["destination_folder"]
    file_path.append(file_downloader.download_file(workflow_url, workflow_destination_folder))
    return file_path


def main():
    config = load_config()
    file_forward, file_reverse, file_workflow = initialize_workflow(config=config)
    file_forward = "Upload_files/newfile_T1A_forward"
    file_reverse = "Upload_files/newfile_T1A_reverse"

    server = config['server']
    api_key = config['api_key']
    history_name = config['history_name']
    workflow = GalaxyWorkflow(server=server, api_key=api_key, history_name=history_name)
    workflow.get_history()

    workflow.define_tools(file_forward=file_forward, file_reverse=file_reverse, file_workflow=file_workflow)
    workflow.show_invocation()


def check_connection(server: str, api_key: str):
    gi = Tool(server, api_key)
    while True:
        time.sleep(60)
        gi.connect_to_galaxy_with_retry()


if __name__ == '__main__':
    process1 = multiprocessing.Process(target=main)
    process2 = multiprocessing.Process(target=check_connection, args=[server, api_key])
    process1.start()
    process2.start()
    process1.join()
    process2.terminate()
