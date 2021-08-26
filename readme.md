**Autonomous bike global path planning module**
In this module, an autonomous bike should be able to select the shortest route from pickup location to destination location from openstreetmaps based on traffic, air pollution, and noise pollution.
So I began by getting pickup and destination location's coordinates by address then from these coordinates I try to generate 4 possible short routes if exists.
For each route I got all the nodes coordinates on it then started calling two web APIS on each node.
The first webAPI which calculates traffic at each node on each route is https://developer.tomtom.com/traffic-api/traffic-api-documentation
Then according to the currentSpeed, and the expectedSpeed I assumed some numbers. Also I checked if the road is closed then it should not be taken, and I checked for the confidence of the returned data however a route might be correct and be taken if confidence is low, so I put that into consideration too.
The second webAPI which calculates air pollution at each node is https://rapidapi.com/weatherbit/api/air-quality/
It returns the AQI which is air quality index in that area based on gases in the air which differs if there is a factory nearby, green-area or high traffic, etc...
As for the noise, I got near Point of Interests around each node such as malls, schools, neighbourhoods, etc... and assumed a number for each of them.
Finally, I take the sum of noise, traffic, AQI on each route and then compare all routes together, and the one with the least sum is the one returned.