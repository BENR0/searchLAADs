from searchlaads.searchLAADS import searchLAADS
import logging.config

logging.basicConfig(level = logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='debug.log',
                    filemode='w')

# #define handler which write info messages to screen
# console = logging.StreamHandler()
# console.setLevel(logging.INFO)
# # set a format which is simpler for console use
# # formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# formatter = logging.Formatter('%(message)s')
# # tell the handler to use this format
# console.setFormatter(formatter)
# # add the handler to the root logger
# logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# server = WSDL.Proxy(wsdl)
# server.config.dumpSOAPOut = 1
# server.config.dumpSOAPIn = 1

#start and end times as datetime obj
endtime = "201704270000"
starttime = "201704260000"


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

mod35.searchFiles()

# mod35.dumpURLs("urls.txt", replace = True)
mod35.downloadFiles("data/", True)

