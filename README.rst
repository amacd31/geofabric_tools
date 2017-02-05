Geofabric Tools
===============

Tools for working with the Australian Hydrological Geospatial Fabric (geofabric).
Data from the Bureau of Meterology: http://www.bom.gov.au/water/geofabric/index.shtml

Download and unzip: ftp://ftp.bom.gov.au/anon/home/geofabric/SH_Catchments_GDB_V2_1_1.zip

Convert SH_Catchments.gdb into a spatiallite database::

    ogr2ogr -f SQLite -dsco SPATIALITE=YES catchments.sqlite SH_Catchments_GDB/SH_Catchments.gdb

Build catchment hierarchy index (stored in catchment_index.json)::

    $ time python build_catchment_index.py
    Opening SH_Catchments_GDB/SH_Catchments.gdb/ for reading catchment hierarchy
    
    real    1m21.497s
    user    1m20.473s
    sys     0m0.413s

Extract catchment boundary upstream from sub-catchment containing a latitude and longitude::

    $ time python catchment_tools.py 148.821,-35.592
    INFO:__main__:Extracting: 148.821,-35.592
    INFO:__main__:Saving as: 6764135.json
    
    real    0m13.465s
    user    0m10.777s
    sys     0m2.570s

