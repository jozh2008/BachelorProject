from bioblend import galaxy
from pprint import pprint
from workflow import *
#server = 'https://usegalaxy.eu/'
#api_key = 'mYjQOJmxwALJESXyMerBZpfuIoA4JDI'
#vgi = galaxy.GalaxyInstance(url=server, key=api_key)
#pprint(gi)
#pprint(gi.histories.get_histories())

#pprint(gi.tools.get_tools(name="MetaPhlAn"))
#pprint(gi.tools.show_tool("toolshed.g2.bx.psu.edu/repos/iuc/metaphlan/metaphlan/4.0.6+galaxy1"))
#pprint(gi.tools.build(tool_id="toolshed.g2.bx.psu.edu/repos/iuc/metaphlan/metaphlan/4.0.6+galaxy1", history_id="32d6ac5f48b6b3b7"))

def main():
    # which server should be conncted
    server = 'https://usegalaxy.eu/'
    # api kex of account
    api_key = 'mYjQOJmxwALJESXyMerBZpfuIoA4JDI'
    # files to upload
    file_forward = "Upload_files/T1A_forward.fastqsanger"
    file_backward = "Upload_files/T1A_reverse.fastqsanger"

    # History which we use on the galaxy server for the workflow
    history_name = "Metatranscriptomics Coding 3"
    #vgi.tools.upload_file(file_forward,'f11364bf29a5652d')

    gi = Tool(server,api_key)
    #gi.upload_file(file_forward,file_backward, history_name)
    #gi.create_history(history_name=history_name)
    gi.get_history_id(history_name=history_name)
    #gi.test(file_backward)
    gi.get_newest_tool_version_and_id("FastQC")
    gi.get_newest_tool_version_and_id("MultiQC")
    gi.get_newest_tool_version_and_id("Filter with SortMeRNA")
    gi.get_newest_tool_version_and_id("MetaPhlAn")
    gi.get_newest_tool_version_and_id("HUMAnN")
    """
    job=gi.upload_file(file_forward,file_backward)
    gi.wait_for_job(job)
    job = gi.run_tool("FastQC")
    gi.wait_for_job(job)
    job = gi.run_MultiQC()
    gi.wait_for_job(job)
    job = gi.run_cutapdt()
    gi.wait_for_job(job)
    job =gi.run_SortMeRNA()
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

















