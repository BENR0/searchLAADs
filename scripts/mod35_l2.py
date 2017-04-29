from ..searchlaads.searchLAADS import searchLAADS
# server = WSDL.Proxy(wsdl)
# server.config.dumpSOAPOut = 1
# server.config.dumpSOAPIn = 1

#start and end times as datetime obj
endtime = "201704270000"
starttime = "201704250000"


product = "MOD35_L2"
collection = 6
north = 2.0
south = -15.0
east = -66.0
west = -82.0
coordsOrTiles = "coords"
dayNightBoth = "dbn"

bbox = [north,south,west,east]

mod35 = searchLAADS(product, collection, starttime, endtime, bbox, coordsOrTiles, dayNightBoth)


mod35.dumpURLs("urls.txt", replace = True)

