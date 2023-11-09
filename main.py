# from bioblend import galaxy
# from pprint import pprint
#from workflow import *
from galaxytools import *


def main():
    # which server should be conncted
    server = 'https://usegalaxy.eu/'
    # api kex of account
    api_key = 'mYjQOJmxwALJESXyMerBZpfuIoA4JDI'
    # files to upload
    file_forward = "Upload_files/T1A_forward.fastqsanger"
    file_backward = "Upload_files/T1A_reverse.fastqsanger"
    # History which we use on the galaxy server for the workflow
    history_name = "Metatranscriptomics Coding 5"
    gi = Tool(server, api_key)

    gi.create_history(history_name=history_name)
    gi.get_history_id(history_name=history_name)
    pprint(gi.get_history_id(history_name=history_name))
    fc = FastQCTool(server=server,api_key=api_key,history_id=gi.history_id)
    # gi.test(file_backward)
    """
    gi.get_newest_tool_version_and_id("FastQC")
    gi.get_newest_tool_version_and_id("MultiQC")
    gi.get_newest_tool_version_and_id("Filter with SortMeRNA")
    gi.get_newest_tool_version_and_id("MetaPhlAn")
    gi.get_newest_tool_version_and_id("HUMAnN")
    """
    job = gi.upload_file(file_forward, file_backward)
    gi.wait_for_job(job)
    fc.run_tool_with_two_Inputfiles("FastQC")
    #job = gi.run_tool_with_two_Inputfiles("FastQC")
    """
    gi.wait_for_job(job)
    job = gi.run_MultiQC()
    gi.wait_for_job(job)
    job = gi.run_cutapdt()
    gi.wait_for_job(job)
    job = gi.run_SortMeRNA()
    gi.wait_for_job(job)
    job = gi.run_FASTQinterlacer()
    gi.wait_for_job(job)
    job = gi.run_MetaPhlAn()
    gi.wait_for_job(job)
    job = gi.run_HUMAnN()
    gi.wait_for_job(job)
    job = gi.run_Renormalize()
    """


if __name__ == '__main__':
    main()
