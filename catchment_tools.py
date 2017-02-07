import argparse
import json

from osgeo import ogr

import logging
logger = logging.getLogger(__name__)

def read_catchment_index(index_file):
    with open(index_file) as f:
        data = json.load(f)

    data = {int(k):v for k,v in data.items() if k != 'null'}

    return data

def get_upstream(ogr_ds, netnodeid):

    upstream_ids = [netnodeid]

    sql = """
        WITH RECURSIVE
        upstream(netnodeid) AS (
        VALUES({0})
        UNION
        SELECT
            A.from_id
        FROM
            ahgfnetworkconnectivitydown AS A, upstream
        WHERE
            A.to_id = upstream.netnodeid
        ) SELECT * FROM upstream;
    """

    res = ogr_ds.ExecuteSQL(sql.format(netnodeid))
    for upstream_feature in res:
        upstream_id = upstream_feature['netnodeid']
        upstream_ids.append(upstream_id)

    ogr_ds.ReleaseResultSet(res)

    return upstream_ids

def extract_catchment(ogr_ds, netnodeid, initial_subcatchment):

    catchment_ids = get_upstream(ogr_ds, netnodeid)
    logger.debug("Selecting %s catchment sub-areas", len(catchment_ids))

    sql_start = 'SELECT ST_Union(geometry) as geometry FROM ahgfcatchment WHERE hydroid = {0} OR netnodeid IN ( '.format(initial_subcatchment)
    sql = sql_start + ', '.join([str(s) for s in catchment_ids]) + ')'

    ogr_ds = ogr.Open('geofabric.sqlite')
    res = ogr_ds.ExecuteSQL(sql)
    logger.debug("Found %s result", len(res))

    geojson = res[0].ExportToJson()
    ogr_ds.ReleaseResultSet(res)

    output_filename = '{0}.json'.format(netnodeid)
    with open(output_filename, 'w') as out:
        logger.info("Saving as: %s", output_filename)
        out.write(geojson)

def get_network_node_by_stream(ogr_ds, stream_hydroid):

    sql = "SELECT S.from_node FROM ahgfnetworkstream AS S WHERE S.hydroid = {0}"

    res = ogr_ds.ExecuteSQL(sql.format(stream_hydroid))
    from_node = res[0]['from_node']
    ogr_ds.ReleaseResultSet(res)

    return from_node

def get_catchment_by_latlon(ogr_ds, lat, lon):

    sql = """
    SELECT
        C.hydroid
    FROM
        ahgfcatchment AS C
    WHERE
        MbrIntersects(C.geometry, MakePoint({0}, {1}))
    """

    res = ogr_ds.ExecuteSQL(sql.format(lat, lon))
    hydroid = res[0]['hydroid']
    ogr_ds.ReleaseResultSet(res)

    return hydroid

if __name__ == '__main__':
    logging.basicConfig()
    logger.setLevel(logging.INFO)

    #catchment_index = read_catchment_index('catchment_index.json')

    parser = argparse.ArgumentParser(description='Extract upstream catchment.')
    parser.add_argument('catchment_outlets', metavar='LAT,LON', type=str, nargs='+', help='Coordinates of the catchment outlet.')
    parser.add_argument('--debug', action='store_true', help='Enable debug output.')

    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    ogr_ds = ogr.Open('geofabric.sqlite')

    sql = """
    SELECT
        Min(ST_Distance(MakePoint({0}, {1}), S.geometry)) AS distance, S.HydroID
    FROM
        ahgfnetworkstream AS S
    WHERE
        S.ROWID IN (
        SELECT
            ROWID
        FROM
            SpatialIndex
        WHERE
            f_table_name='ahgfnetworkstream' AND search_frame=ST_Buffer(MakePoint({0}, {1}),0.001)
    );
    """
    for outlet in args.catchment_outlets:
        lat, lon = [ float(x) for x in outlet.split(',') ]
        logger.info("Extracting: %s", outlet)
        initial_subcatchment = get_catchment_by_latlon(ogr_ds, lat, lon)

        res = ogr_ds.ExecuteSQL(sql.format(lat, lon))
        if len(res) > 0:
            logger.debug(res[0].ExportToJson())
            hydro_id = res[0]['hydroid']
            ogr_ds.ReleaseResultSet(res)
        else:
            logger.exception("No nearby stream.")
            continue
        logger.debug("Using stream HydroID: %s", hydro_id)

        netnode_id = get_network_node_by_stream(ogr_ds, hydro_id);
        logger.debug("Using NetNodeID: %s", netnode_id)

        extract_catchment(ogr_ds, netnode_id, initial_subcatchment)

    # Close the dataset (GDAL/OGR bindings aren't very Pythonic)
    ogr_ds = None
