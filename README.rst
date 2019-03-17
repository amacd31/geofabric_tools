Geofabric Tools
===============

Tools for working with the Australian Hydrological Geospatial Fabric (geofabric).
Data from the Bureau of Meterology: http://www.bom.gov.au/water/geofabric/index.shtml

Download and unzip: ftp://ftp.bom.gov.au/anon/home/geofabric/SH_Network_GDB_V2_1_1.zip

Convert SH_Catchments.gdb into a spatialite database::

    $ time ogr2ogr -f SQLite -dsco SPATIALITE=YES geofabric.sqlite SH_Network_GDB/SH_Network.gdb
    
    real    9m51.489s
    user    7m38.091s
    sys     0m7.016s

Add some indexes to the spatialite database::

    $ sqlite3 geofabric.sqlite "CREATE INDEX idx_ahgfnetworkconnectivitydown_to_id ON ahgfnetworkconnectivitydown (to_id);"
    $ sqlite3 geofabric.sqlite "CREATE INDEX idx_ahgfcatchment_hydroid ON ahgfcatchment (hydroid);"
    $ sqlite3 geofabric.sqlite "CREATE INDEX idx_ahgfcatchment_netnodeid ON ahgfcatchment (netnodeid);"

Extract catchment boundary upstream from sub-catchment containing a latitude and longitude::

    $ time python geofabric_tools/catchment_tools.py 148.821,-35.592
    INFO:__main__:Extracting: 148.821,-35.592
    INFO:__main__:Saving as: 1170184.json

    real    0m4.067s
    user    0m2.904s
    sys     0m1.126s

Optionally include an ID to use when saving the output file::

    $ time python geofabric_tools/catchment_tools.py 148.821,-35.592:410730
    INFO:__main__:Extracting: 148.821,-35.592
    INFO:__main__:Saving as: 410730.json

    real    0m5.810s
    user    0m4.645s
    sys     0m0.885s
