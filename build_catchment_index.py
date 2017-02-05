import fiona
import json

from collections import defaultdict

data = defaultdict(list)

geodb = "SH_Catchments_GDB/SH_Catchments.gdb/"
print("Opening {0} for reading catchment hierarchy".format(geodb))
with fiona.open(geodb, layer='AHGFCatchment') as src:
   for f in src:
       data[f['properties']['HydroID']]
       data[f['properties']['NextDownID']].append(f['properties']['HydroID'])

print("Saving catchment_index.json")
with open('catchment_index.json', 'w') as f:
    json.dump(data, f)
