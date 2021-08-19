import requests
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from pprint import pprint

application = Nominatim(user_agent="tutorial")

# getting current location coordinates
# will make them with eval input to be inputs from the user
currentLocation = application.geocode("city stars").raw
pprint(currentLocation)

# getting destination coordinates
destinationLocation = application.geocode("Cairo Festival City").raw
pprint(destinationLocation)

# created Cairo, Egypt's graph using ox.graph_from_place
# then saved it using ox.save_graphml to data folder and then loading it to reduce run time
# you will have to do it yourself since it cannot be pushed as is its 100+ MB
#
G = ox.load_graphml('./data/graph.graphml')

# saving start and end coordinates to variables and getting nearest node to them
start = (float(currentLocation['lat']), float(currentLocation['lon']))
end = (float(destinationLocation['lat']), float(destinationLocation['lon']))
start_node = ox.get_nearest_node(G, start)
end_node = ox.get_nearest_node(G, end)

# list that contains all routes
route_list = []

# route based on shortest distance from start to end
route1 = nx.shortest_path(G, start_node, end_node, weight='length')
route_list.append(route1)

# route based on shortest time travel from start to end
route2 = nx.shortest_path(G, start_node, end_node, weight='Travel time')
route_list.append(route2)

# rc = ['r', 'y']
#
# getting all nodes on the 2 routes, hard coded so far just for testing
nodes_proj, edges_proj = ox.graph_to_gdfs(G, nodes=True, edges=True)
route1_nodes = nodes_proj.loc[route1]
route2_nodes = nodes_proj.loc[route2]

# converting the nodes to a list datatype instead of dataframe data type i.e list of nodes
list1 = route1_nodes.values.tolist()
list2 = route2_nodes.values.tolist()

allLists = [list1, list2]


# converting list of nodes to list of dictionaries each dictionary having lat and lon as keys
def listToDict(nodes):
    list_of_dict = [{"lon": node[0], "lat": node[1]} for node in nodes]
    pprint(list_of_dict)
    return list_of_dict


def calculate():
    # for each 5 nodes away from each others in each route calls an api to calculate air pollution
    # will add noise and traffic too.
    # however all nodes coordinates are close from each other so there is no big difference and I made sure by searching
    # on openstreetmaps.org by searching by node id and the coordinates are correct.
    for value in allLists:
        list_of_dict = listToDict(value)
        for dictionary in list_of_dict[::5]:
            url = "https://air-quality.p.rapidapi.com/history/airquality"
            querystring = {"lon": dictionary['lon'], "lat": dictionary['lat']}
            headers = {
                'x-rapidapi-key': "3511e239c9mshd7fcbcf5c64c90ap143252jsn6129f5800034",
                'x-rapidapi-host': "air-quality.p.rapidapi.com"
            }
            response1 = requests.request("GET", url, headers=headers, params=querystring)
            print(response1.json()['data'][0]['aqi'])
        if value == allLists[0]:
            aqi1 = response1.json()['data'][0]['aqi']
            # min1 will be sum of values from air pollution, noise pollution and traffic returned on route 1
            min1 = aqi1
        else:
            aqi2 = response1.json()['data'][0]['aqi']
            # min2 will be sum of values from air pollution, noise pollution and traffic returned on route 2
            min2 = aqi2
    if min1 <= min2:
        print("route 1 is the best route")
        return route_list[0]
    else:
        print("route 2 is the best route")
        return route_list[1]


calculate()
