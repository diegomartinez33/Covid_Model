import os
import pickle
import json
from collections import defaultdict
from itertools import product
import numpy as np
import geopandas as gpd
from geopy import distance
from shapely.geometry import Polygon

def create_grid(city, cell_size):

    shp = gpd.read_file(os.path.join('..', 'Datos', 'Shapes',
                                     city, 'localidades.shp'))

    minx = min(shp.bounds['minx'])
    miny = min(shp.bounds['miny'])
    maxx = max(shp.bounds['maxx'])
    maxy = max(shp.bounds['maxy'])

    distance.EARTH_RADIUS = 6373.0

    shp_w = distance.great_circle((miny,minx), (miny,maxx))
    shp_h = distance.great_circle((miny,minx), (maxy,minx))

    grid_w = int(round(shp_w.meters / cell_size))
    grid_h = int(round(shp_h.meters / cell_size))

    if city == 'bogota':
        import bogota
        zones = bogota.zones

    grid_borders_x = [minx + i*(maxx-minx)/grid_w for i in range(grid_w + 1)]
    grid_borders_y = [miny + i*(maxy-miny)/grid_h for i in range(grid_h + 1)]

    grid_zones = defaultdict(list)
    grid_localidades = defaultdict(list)

    for i, j in product(range(grid_w), range(grid_h)):
        cell = Polygon([(grid_borders_x[i], grid_borders_y[j]),
                        (grid_borders_x[i], grid_borders_y[j+1]),
                        (grid_borders_x[i+1], grid_borders_y[j+1]),
                        (grid_borders_x[i+1], grid_borders_y[j]),
                        (grid_borders_x[i], grid_borders_y[j])])

        intersects = shp.intersects(cell)
        for loc in shp.loc[intersects, 'LocCodigo']:
            grid_zones[zones[loc]].append((i,j))
            grid_localidades[int(loc)].append((i,j))

        for k, v in grid_zones.items():
            grid_zones[k] = sorted(list(set(v)))
            
        for k, v in grid_localidades.items():
            grid_localidades[k] = sorted(list(set(v)))

    with open('Casillas_zona_{}.json'.format(cell_size),
              'w') as outfile:
        json.dump(dict(grid_zones), outfile)
        
    with open('Casillas_localidad_{}.json'.format(cell_size),
              'w') as outfile:
        json.dump(dict(grid_localidades), outfile)

    with open('dim_grida_{}.pickle'.format(cell_size), 'wb') as h:
        pickle.dump((grid_w, grid_h), h)
