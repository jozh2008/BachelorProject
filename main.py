from bioblend import galaxy
from pprint import pprint
from workflow import *
server = 'https://usegalaxy.eu/'
api_key = 'mYjQOJmxwALJESXyMerBZpfuIoA4JDI'
#gi = galaxy.GalaxyInstance(url=server, key=api_key)
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
    history_name = "Metatranscriptomics Coding"

    gi = Tool(server,api_key)
    #gi.upload_file(file_forward,file_backward, history_name)
    gi.get_history_id(history_name=history_name)
    gi.preprocessing()
if __name__ == '__main__':
    main()

















