import os
import pickle
import json
from collections import defaultdict
from itertools import product
import numpy as np
import geopandas as gpd
from geopy import distance
from shapely.geometry import Polygon
import sys
import time

def create_grid(city, cell_size):

    #shp = gpd.read_file(os.path.join('..', 'Datos', 'Shapes',
    #                                 city, 'localidades.shp'))
    shp = gpd.read_file(os.path.join('.', 'localidades.shp'))
    print(shp)

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

    total = len(list(product(range(grid_w), range(grid_h))))
    print(total)
    #sys.exit()

    #start_time = time.time()
    total_time = 0
    cont = 0
    for i, j in product(range(grid_w), range(grid_h)):
        # start_time = time.time()
        cell = Polygon([(grid_borders_x[i], grid_borders_y[j]),
                        (grid_borders_x[i], grid_borders_y[j+1]),
                        (grid_borders_x[i+1], grid_borders_y[j+1]),
                        (grid_borders_x[i+1], grid_borders_y[j]),
                        (grid_borders_x[i], grid_borders_y[j])])

        intersects = shp.intersects(cell)
        # print("\nIntersects:\n")
        # print(intersects)
        # print("Aqui")
        # print(shp.loc[intersects, 'LocCodigo'])
        #print(grid_zones)
        for loc in shp.loc[intersects, 'LocCodigo']:
            # print("Un intersect")
            # print(loc)
            # print(int(loc))
            # print(zones[loc])
            # time.sleep(20)
            grid_zones[zones[loc]].append((i,j))
            grid_localidades[int(loc)].append((i,j))

        for k, v in grid_zones.items():
            grid_zones[k] = sorted(list(set(v)))
            
        for k, v in grid_localidades.items():
            grid_localidades[k] = sorted(list(set(v)))

        # time_loop = time.time() - start_time
        # total_time += time_loop
        # cont += 1
        # mean_time = total_time/cont
        # Remaining_time = (total - cont)*mean_time
        # print("Loop: %d secs\tRemaining time: %f secs" % ((total - cont), Remaining_time))

    print("intersects runned...")
    with open('Casillas_zona_{}_2.json'.format(cell_size),
              'w') as outfile:
        json.dump(dict(grid_zones), outfile)
        
    with open('Casillas_localidad_{}_2.json'.format(cell_size),
              'w') as outfile:
        json.dump(dict(grid_localidades), outfile)

    with open('dim_grida_{}_2.pickle'.format(cell_size), 'wb') as h:
        pickle.dump((grid_w, grid_h), h)
