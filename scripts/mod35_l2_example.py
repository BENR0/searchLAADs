from searchlaads.searchlaads import searchLAADS
import sys
import logging
import logging.config

logFormatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
consoleFormatter = logging.Formatter("%(message)s")

#configure root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#set file log
fileHandler = logging.FileHandler("debug.log")
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(logging.DEBUG)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(consoleFormatter)
consoleHandler.setLevel(logging.INFO)
logger.addHandler(consoleHandler)


#MOD35_L2 available between
#officially available from 200002240000
#SET UP START AND ENDTIME
starttime = "YYYYmmddHHMM"
endtime = "YYYYmmddHHMM"


#SET UP PRODUCT, COLLECTION AND BOUNDING BOX
product = "MOD35_L2"
collection = 6
#Example bounding box for Ecuador
north = 2.0
south = -15.0
east = -66.0
west = -82.0
coordsOrTiles = "coords"
dayNightBoth = "dbn"

bbox = [north,south,west,east]

#instantiate search
mod35 = searchLAADS(product, collection, starttime, endtime, bbox, coordsOrTiles, dayNightBoth)

#search for files (gets file URLs of the ftp server)
mod35.searchFiles()

#optionally write URLs to text file
mod35.dumpURLs("urls.txt", replace = True)

#download the files to DIRECTORY (under DIRECTORY dirs for each year will be generated)
mod35.downloadFiles("DIRECTORY/", multiproc = True)


##other available functions
#check if files were downloaded correctly (needs gdal)
#mod35.checkFiles()

#check for missing files e.g. if some files could not be downloaded
#file urls will be stored in FILE.txt
#mod35.checkMissing(outfile = "FILE.txt)

