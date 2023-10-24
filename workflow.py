from bioblend import galaxy
from pprint import pprint
import re

class Workflow:
    def __init__(self, server, api_key) -> None:
        self.gi = galaxy.GalaxyInstance(url = server, key = api_key)
        self.history_id =""
        pprint(self.gi)

    def upload(self, file1, file2, history_name):
       # get the history id to upload files
       history = self.gi.histories.get_histories(name = history_name)
       history_id = history[0]["id"]
       self.gi.tools.upload_file(path=file1, history_id=history_id, file_name="T1A_forward")
       self.gi.tools.upload_file(path=file2, history_id=history_id, file_name="T1A_reverse")


    # for a given tool, give back the newest version of this tool
    def get_newest_tool(self, tool_name):
        tools = (self.gi.tools.get_tools(name=tool_name))
        lst_version = [] # list to save all version of this tool
        lst2 = [] # 
        for tool in tools:
            lst_version.append(tool["version"])
        a = (self.version_key_modified(lst_version))
        newest_version = max(list(a.keys()), key=self.version_key)
        lst2 = a[newest_version]
        res = newest_version + sorted(lst2,reverse=True)[0]
        return res
    
    # calculates the history_id for a given history name
    def get_history_id(self, history_name):
        history = self.gi.histories.get_histories(name = history_name)
        history_id = history[0]["id"]
        self.history_id = history_id
    

    def preprocessing(self):
        (self.get_newest_tool("HUMAnN"))

    


# Define a custom key function to extract and compare version numbers
    def version_key(self, version):
        # Split the version string into components and convert them to integers
        parts = [int(part) for part in re.findall(r'\d+', version)]
        return tuple(parts)


    def version_key_modified(self, version):
        d = dict()
        helperKey = ""
        helperValue = ""
        for ver in version:
            position = ver.find("+")
            if position != -1:
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

