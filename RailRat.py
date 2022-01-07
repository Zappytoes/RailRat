import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.colors as mpl_colors
import osmnx as ox
ox.config(all_oneway=False) #,use_cache=True, log_console=True) # don't mess with oneway for now
import networkx as nx
import folium
from datetime import datetime, timedelta ,tzinfo
import pytz
import numpy as np

def shortest_path_one_to_many(G,start,destinations,weight='travel_time',start_datetime=None):
  '''
  G: Graph
  start (): origin node id
  destinations (): list of destintion node ids
  weight (string): path to minimize ('travel_time' or 'distance')
  start_datetime (tuple of itegers): (year,month,day,hour,minute,second)
  '''
  if start_datetime == None:
    start_datetime=datetime.now(pytz.UTC)
  else:
    start_datetime=datetime(start_datetime[0],start_datetime[1],
                            start_datetime[2],start_datetime[3],
                            start_datetime[4],start_datetime[5],tzinfo=pytz.UTC)
  
  geo_coded_start = ox.geocoder.geocode(start)
  geo_coded_start_snap = ox.distance.nearest_nodes(G, geo_coded_start[1], geo_coded_start[0])
  geo_coded_start_snap=[geo_coded_start_snap]*len(destinations)

  geo_coded_dest_snap = []
  for d in destinations:
    geo_coded_dest = ox.geocoder.geocode(d)
    geo_coded_dest_snap.append(ox.distance.nearest_nodes(G, geo_coded_dest[1], geo_coded_dest[0]))

  routes = ox.distance.shortest_path(G, geo_coded_start_snap, geo_coded_dest_snap, weight=weight)

  arrival_time_list = []
  tt_list = []
  dist_list = []
  for route in routes:
    attrs = ox.utils_graph.get_route_edge_attributes(G, route)
    tt = 0
    dist = 0
    for edge in attrs:
      tt+=edge['travel_time']
      dist+=edge['length']

    arrival_time_list.append(start_datetime + timedelta(seconds=tt))
    tt_list.append(tt)
    dist_list.append(dist)
  df = pd.DataFrame()
  df['Origin'] = [start]*len(destinations)
  df['Destintation'] = destinations
  df['Arrival-Time(UTC)'] = arrival_time_list
  df['Distance(m)'] = dist_list
  df['Travel-Time(s)'] = tt_list

  return routes, df
  
def rail_isochrone(G,start,weight='travel_time',start_datetime=None,show_map=False):
  '''
  G: Graph
  start (): origin node id
  weight (string): path to minimize ('travel_time' or 'distance')
  start_datetime (tuple of itegers): (year,month,day,hour,minute,second)
  '''
  if start_datetime == None:
    start_datetime=datetime.now(pytz.UTC)
  else:
    start_datetime=datetime(start_datetime[0],start_datetime[1],
                            start_datetime[2],start_datetime[3],
                            start_datetime[4],start_datetime[5],tzinfo=pytz.UTC)
  
  geo_coded_start = ox.geocoder.geocode(start)
  geo_coded_start_snap = ox.distance.nearest_nodes(G, geo_coded_start[1], geo_coded_start[0])
  
  travel_time = nx.shortest_path_length(G, source=geo_coded_start_snap, weight=weight) #networkx function for getting travel time

  df = pd.DataFrame()
  loc = []
  time = []
  arrival_time = []
  node_id = []
  for node in travel_time.keys():
    node_id.append(node)
    loc.append(G.nodes[node])
    time.append(travel_time[node])
    arrival_time.append(start_datetime + timedelta(seconds=travel_time[node]))
  df['osmid'] = node_id
  df['Coordinates'] = loc
  df['Travel-Time(s)'] = time
  df['Arrival-Time(UTC)'] = arrival_time

  if show_map == True:
    r = range(int(np.min(list(travel_time.values()))),int(np.max(list(travel_time.values())))+1)
    iso_colors = ox.plot.get_colors(n=len(r), cmap='rainbow', start=0, return_hex=True)
    len(r), len(iso_colors)
    map = folium.Map(width=500,height=500)
    ox.folium.plot_graph_folium(G,graph_map=map,color='gray')
    index = 0
    for node in G.nodes():
      lon = G.nodes[node]['x'] #lon
      lat = G.nodes[node]['y'] #lat
      folium.CircleMarker((lat,lon),radius=2,weight=3,color=iso_colors[int(travel_time[node])]).add_to(map)
      index+=1
    folium.Marker(geo_coded_start, popup='Origin').add_to(map)

    return df,map
  else:
    return df