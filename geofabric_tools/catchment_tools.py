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

def extract_catchment(ogr_ds, netnodeid, initial_subcatchment, catchment_id, exclude_sinks=False):

    catchment_ids = get_upstream(ogr_ds, netnodeid)
    logger.debug("Selecting %s catchment sub-areas", len(catchment_ids))

    if exclude_sinks:
        select_stmt = 'ST_Union(geometry)'
    else:
        select_stmt = 'ST_BuildArea(ST_ExteriorRing(ST_Union(geometry)))'

    sql_start = """SELECT {0} as geometry
FROM
    ahgfcatchment
WHERE
    hydroid = {1} OR netnodeid IN ( """.format(
        select_stmt,
        initial_subcatchment
    )
    sql = sql_start + ', '.join([str(s) for s in catchment_ids]) + ')'

    res = ogr_ds.ExecuteSQL(sql)
    logger.debug("Found %s result", len(res))

    geojson = res[0].ExportToJson()
    ogr_ds.ReleaseResultSet(res)

    output_filename = '{0}.json'.format(catchment_id)
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
        ST_Within(MakePoint({0}, {1}), C.geometry)
    """

    res = ogr_ds.ExecuteSQL(sql.format(lon, lat))
    hydroid = res[0]['hydroid']
    ogr_ds.ReleaseResultSet(res)

    return hydroid


def get_netnode_id(ogr_ds, lat, lon):
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

    res = ogr_ds.ExecuteSQL(sql.format(lon, lat))
    if len(res) > 0:
        logger.debug(res[0].ExportToJson())
        hydro_id = res[0]['hydroid']
        ogr_ds.ReleaseResultSet(res)
        if hydro_id is None:
            logger.exception("No nearby stream.")
    else:
        logger.exception("No nearby stream.")
    logger.debug("Using stream HydroID: %s", hydro_id)

    return get_network_node_by_stream(ogr_ds, hydro_id);

if __name__ == '__main__':
    logging.basicConfig()
    logger.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(description='Extract upstream catchment.')
    parser.add_argument('catchment_outlets', metavar='LAT,LON[:CATCHMENT_ID]', type=str, nargs='+', help='Coordinates of the catchment outlet. Takes optional :ID specifier for setting output filename to ID.json instead of defaulting to the initial sub-catchment Geofabric Hydro ID.')
    parser.add_argument('--debug', action='store_true', help='Enable debug output.')
    parser.add_argument(
        '--exclude-sinks',
        action='store_true',
        help='Exclude sinks from final catchment boundary. Can result in inner holes in the geometry. Without this option all sinks are assumed to be part of the catchment and only the exterior ring of the geometry is used.'
    )

    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    ogr_ds = ogr.Open('geofabric.sqlite')

    for outlet in args.catchment_outlets:
        parts = outlet.split(':')

        lon, lat = [ float(x) for x in parts[0].split(',') ]
        logger.info("Extracting: %s", outlet)
        initial_subcatchment = get_catchment_by_latlon(ogr_ds, lat, lon)

        if len(parts) == 1:
            catchment_id = initial_subcatchment
        elif len(parts) == 2:
            catchment_id = parts[1]
        else:
            raise ValueError("Unknown number of parts specified in {0}".format(outlet))

        netnode_id = get_netnode_id(ogr_ds, lat, lon)
        logger.debug("Using NetNodeID: %s", netnode_id)

        extract_catchment(ogr_ds, netnode_id, initial_subcatchment, catchment_id, args.exclude_sinks)

    # Close the dataset (GDAL/OGR bindings aren't very Pythonic)
    ogr_ds = None
