from galaxytools import *

server = 'http://localhost:8080/'
api_key ='ff269704f8decd8811ef2d9824ba869e'
gi = galaxy.GalaxyInstance(url=server, key= api_key)
pprint(gi.histories.get_histories())
#new_hist = gi.histories.create_history(name='BioBlend test')
#pprint(new_hist)
pprint(gi.tool_data.get_data_tables())

