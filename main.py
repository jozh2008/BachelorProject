from bioblend import galaxy
from pprint import pprint
server = 'https://usegalaxy.eu/'
api_key = 'mYjQOJmxwALJESXyMerBZpfuIoA4JDI'
gi = galaxy.GalaxyInstance(url=server, key=api_key)
pprint(gi)
pprint(gi.histories.get_histories())

pprint(gi.tools.get_tools(name="MetaPhlAn"))
pprint(gi.tools.show_tool("toolshed.g2.bx.psu.edu/repos/iuc/metaphlan/metaphlan/4.0.6+galaxy1"))
pprint(gi.tools.build(tool_id="toolshed.g2.bx.psu.edu/repos/iuc/metaphlan/metaphlan/4.0.6+galaxy1", history_id="32d6ac5f48b6b3b7"))