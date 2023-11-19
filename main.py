# from bioblend import galaxy
# from pprint import pprint
# from workflow import *
from galaxytools import *
import multiprocessing
# which server should be conncted
server = 'https://usegalaxy.eu/'
# api kex of account
api_key = 'mYjQOJmxwALJESXyMerBZpfuIoA4JDI'


def main(server: str, api_key: str):
    # files to upload
    file_forward = "Upload_files/T1A_forward.fastqsanger"
    file_reverse = "Upload_files/T1A_reverse.fastqsanger"
    # History which we use on the galaxy server for the workflow
    history_name = "Metatranscriptomics Coding 5"
    gi = Tool(server, api_key)
    gi.create_history(history_name=history_name)
    gi.get_history_id(history_name=history_name)

    tools = [
        FastQCTool(server=server, api_key=api_key, history_id=gi.history_id),
        MultiQCTool(server=server, api_key=api_key, history_id=gi.history_id),
        CutadaptTool(server=server, api_key=api_key, history_id=gi.history_id),
        SortMeRNATool(server=server, api_key=api_key, history_id=gi.history_id),
        FASTQinterlacerTool(server=server, api_key=api_key, history_id=gi.history_id),
        MetaPhlAnTool(server=server, api_key=api_key, history_id=gi.history_id),
        HUMAnNTool(server=server, api_key=api_key, history_id=gi.history_id)
    ]

    gi.upload_file(file_forward, "T1A_forward")
    gi.upload_file(file_reverse, "T1A_reverse")

    for tool in tools:
        tool.run_tool_with_input_files(tool.tool_name)

    re = RenormalizeTool(server=server, api_key=api_key, history_id=gi.history_id)
    datasets_to_check = ["Gene families and their abundance", "Pathways and their abundance"]
    for dataset in datasets_to_check:
        re.get_dataset_names(dataset)
        re.run_tool_with_input_files("Renormalize")


def check_connection(server: str, api_key: str):
    gi = Tool(server, api_key)
    while True:
        time.sleep(30)
        gi.connect_to_galaxy_with_retry()


def get_Databases(server: str, api_key: str):
    gi = Tool(server, api_key)
    history_name = "Metatranscriptomics Coding 5"
    gi.get_history_id(history_name=history_name)
    si = SortMeRNATool(server, api_key, gi.history_id)
    hu = HUMAnNTool(server, api_key, gi.history_id)
    si.get_datatables()
    hu.get_datatables()


if __name__ == '__main__':
    process1 = multiprocessing.Process(target=main, args=[server, api_key])
    process2 = multiprocessing.Process(target=check_connection, args=[server, api_key])
    process3 = multiprocessing.Process(target=get_Databases, args=[server, api_key])
    process1.start()
    process2.start()
    process3.start()
    process1.join()
    process2.terminate()
    process3.join()
