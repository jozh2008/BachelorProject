from bioblend import galaxy
from pprint import pprint

class Workflow:
    def __init__(self, server, api_key) -> None:
        self.gi = galaxy.GalaxyInstance(url = server, key = api_key)
        pprint(self.gi)

    def upload(self, file1, file2):
        pass
