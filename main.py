import requests
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from pprint import pprint
import time

application = Nominatim(user_agent="tutorial")

# getting current location coordinates.
x = input("Enter pickup location:")
currentLocation = application.geocode(x).raw
pprint(currentLocation)

# getting destination coordinates.
y = input("Enter destination location: ")
destinationLocation = application.geocode(y).raw
pprint(destinationLocation)

# created Cairo, Egypt's graph using ox.graph_from_place
# then saved it using ox.save_graphml to data folder and then loading it to reduce run time
# you will have to do it yourself since it cannot be pushed as is its 100+ MB.
# G = ox.graph_from_place('Cairo, Egypt', network_type='drive')
# ox.save_graphml(G, './data/graph.graphml')
G = ox.load_graphml('./data/graph.graphml')

# saving start and end coordinates to variables and getting nearest node to them
start = (float(currentLocation['lat']), float(currentLocation['lon']))
end = (float(destinationLocation['lat']), float(destinationLocation['lon']))
start_node = ox.get_nearest_node(G, start)
end_node = ox.get_nearest_node(G, end)

# list that contains all routes.
route_list = []

# route based on shortest distance from start to end, generated using dijkstra's algorithm.
route1 = nx.shortest_path(G, start_node, end_node, weight='length')
route_list.append(route1)

# route based on shortest time travel from start to end, generated using dijkstra's algorithm.
route2 = nx.shortest_path(G, start_node, end_node, weight='Travel time')
route_list.append(route2)

# route based on shortest time travel from start to end, generated using A* algorithm.
route3 = nx.astar_path(G, start_node, end_node)
route_list.append(route3)

# route based on shortest time travel from start to end, generated using bellman-ford's algorithm.
route4 = nx.shortest_path(G, start_node, end_node, method="bellman-ford")
route_list.append(route4)

# color_list = ['green', 'red', 'blue', 'yellow']

# fig, ax = ox.plot_graph_routes(G, route_list, color_list, route_linewidths=10)
# plt.show()

# method that removes duplicate routes from the 4 generated routes if any.
def checkRoutes(routes):
    set_of_routes = set(tuple(o) for o in routes)
    print([list(elem) for elem in list(set_of_routes)])
    return [list(elem) for elem in list(set_of_routes)]


# getting all nodes on each generated route.
def allNodes(routes):
    nodes_proj, edges_proj = ox.graph_to_gdfs(G, nodes=True, edges=True)
    all_route_nodes = []
    for route in routes:
        route_nodes = nodes_proj.loc[route]
        all_route_nodes.append(route_nodes)
    return all_route_nodes


# converting the nodes to a list datatype instead of dataframe datatype i.e list of nodes
def dataframe_to_list(list_of_dataframes):
    allLists = []
    for data in list_of_dataframes:
        converted = data.values.tolist()
        allLists.append(converted)
    return allLists


# converting list of nodes to list of dictionaries each dictionary having lat and lon as keys
def listToDict(nodes):
    list_of_dict = [{"lon": node[0], "lat": node[1]} for node in nodes]
    pprint(list_of_dict)
    return list_of_dict


# for each 5 nodes away from each others in each route calls an api to calculate air pollution
# and calls another api that calculates traffic at this node
# and calculates noise based on Points of Interests near the node
# then return the route with the least sum of the 3 things above.
def calculate():
    updated_route_list = checkRoutes(route_list)
    possible_routes = allNodes(updated_route_list)
    allLists = dataframe_to_list(possible_routes)
    aqi = 0  # aqi returned from the air pollution api.
    minimum = 0  # minimum sum of aqi, traffic_route, noise between different routes.
    best = 0  # best route number.
    all_routes_traffic = []  # list of traffic calculated in each route.
    all_routes_noise = []  # list of noise calculated on each route.
    all_routes_aqi = []  # list of aqi returned on each route.
    for value in allLists:
        traffic_route = 0  # traffic returned at node on the route.
        noise = 0  # noise calculated at a node.
        list_of_dict = listToDict(value)
        list_of_nodes = list_of_dict[::5]
        prev_after = []  # used in comparing nodes in traffic.
        count = 0  # used in traffic.
        # calculating traffic:
        for index in range(len(list_of_nodes)):
            if index % 3 == 0 and index != 0:
                prev_after.clear()
                count = 0
            trafficUrl = f'https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?' \
                         f'key=BUC0xtDe0EKMr6yiAHqNhtE9JXbsMGps&point={list_of_nodes[index]["lon"]},' \
                         f'{list_of_nodes[index]["lat"]}'
            trafficResponse = requests.get(trafficUrl)
            traffic = trafficResponse.json()
            print(traffic)
            prev_after.append(traffic['flowSegmentData'])
            if len(prev_after) == 3:
                if prev_after[0]['roadClosure'] and prev_after[1]['roadClosure'] and prev_after[2]['roadClosure']:
                    traffic_route += 10000
                    all_routes_traffic.append(traffic_route)
                    break
                if prev_after[0]['confidence'] < 0.7 and prev_after[1]['confidence'] < 0.7 and \
                        prev_after[2]['confidence'] < 0.7:
                    traffic_route += 10
                    continue
            if prev_after[count]['freeFlowSpeed'] - prev_after[count]['currentSpeed'] < 10:
                traffic_route += 1
            elif prev_after[count]['freeFlowSpeed'] - prev_after[count]['currentSpeed'] < 20:
                traffic_route += 2
            elif prev_after[count]['freeFlowSpeed'] - prev_after[count]['currentSpeed'] > 20:
                traffic_route += 3
            count += 1

            # calculating air pollution:
            airUrl = "https://air-quality.p.rapidapi.com/history/airquality"
            querystring = {"lon": list_of_nodes[index]['lon'], "lat": list_of_nodes[index]['lat']}
            airHeaders = {
                'x-rapidapi-key': "3511e239c9mshd7fcbcf5c64c90ap143252jsn6129f5800034",
                'x-rapidapi-host': "air-quality.p.rapidapi.com"
            }
            time.sleep(8)  # wait before calling the api again for 8 seconds so that it does not crash.
            airResponse = requests.request("GET", airUrl, headers=airHeaders, params=querystring)
            print(airResponse.json()['data'][0]['aqi'])
            aqi = airResponse.json()['data'][0]['aqi']

            # calculating noise:
            location = application.reverse((list_of_nodes[index]['lon'], list_of_nodes[index]['lat']))
            print(location.raw)
            if 'amenity' in location.raw['address']:
                noise += 3
            if 'road' in location.raw['address']:
                noise += 2
            if 'neighbourhood' in location.raw['address']:
                noise += 1

        # appending to the lists defined above.
        all_routes_aqi.append(aqi)
        all_routes_traffic.append(traffic_route)
        all_routes_noise.append(noise)

    # choose the best route according to the minimum sum
    i = 0
    while i < len(all_routes_noise):
        if i == 0:
            minimum = all_routes_noise[i] + all_routes_traffic[i] + all_routes_aqi[i]
            best = i + 1
        elif all_routes_noise[i] + all_routes_traffic[i] + all_routes_aqi[i] < minimum:
            minimum = all_routes_noise[i] + all_routes_traffic[i] + all_routes_aqi[i]
            best = i + 1
        i += 1

    print("Route " + str(best) + " is the best route")
    # fig, ax = ox.plot_graph_route(G, updated_route_list[best - 1], 'red', route_linewidth=4)
    return updated_route_list[best - 1]


calculate()
