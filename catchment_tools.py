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

def get_upstream(hydro_id, catchment_index):

    upstream_ids = [hydro_id]

    def upstream(hydro_id, upstream_ids, catchment_index):

       for upstream_id in catchment_index[hydro_id]:
           upstream_ids.append(upstream_id)
           upstream(upstream_id, upstream_ids, catchment_index)

       return upstream_ids

    upstream_ids = upstream(hydro_id, upstream_ids, catchment_index)

    return upstream_ids

def extract_catchment(hydro_id, catchment_index):

    catchment_ids = get_upstream(hydro_id, catchment_index)
    logger.debug("Selecting %s catchment sub-areas", len(catchment_ids))

    sql_start = 'SELECT ST_Union(geometry) as geometry FROM catchments WHERE hydroid = '
    sql = sql_start + ' OR hydroid = '.join([str(s) for s in catchment_ids])

    ogr_ds = ogr.Open('catchments.sqlite')
    layer = ogr_ds.ExecuteSQL(sql)
    logger.debug("Found %s layers", len(layer))

    geojson = layer[0].ExportToJson()

    output_filename = '{0}.json'.format(hydro_id)
    with open(output_filename, 'w') as out:
        logger.info("Saving as: %s", output_filename)
        out.write(geojson)

    # Close the dataset (GDAL/OGR bindings aren't very Pythonic)
    ogr_ds = None

if __name__ == '__main__':
    logging.basicConfig()
    logger.setLevel(logging.INFO)

    catchment_index = read_catchment_index('catchment_index.json')

    parser = argparse.ArgumentParser(description='Extract upstream catchment.')
    parser.add_argument('catchment_outlets', metavar='LAT,LON', type=str, nargs='+', help='Coordinates of the catchment outlet.')
    parser.add_argument('--debug', action='store_true', help='Enable debug output.')

    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    ogr_ds = ogr.Open('catchments.sqlite')

    sql = "SELECT HydroID FROM catchments where ST_Within(MakePoint({0}, {1}), geometry);"
    for outlet in args.catchment_outlets:
        lat, lon = [ float(x) for x in outlet.split(',') ]
        logger.info("Extracting: %s", outlet)

        hydro_id = ogr_ds.ExecuteSQL(sql.format(lat, lon))[0]['hydroid']
        logger.debug("Using HydroID: %s", hydro_id)

        extract_catchment(hydro_id, catchment_index)

    # Close the dataset (GDAL/OGR bindings aren't very Pythonic)
    ogr_ds = None
