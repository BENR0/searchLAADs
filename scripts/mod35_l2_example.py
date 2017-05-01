from searchlaads.searchLAADS import searchLAADS
import logging.config

#setting up optional logging
logging.basicConfig(level = logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='debug.log',
                    filemode='a')

logger = logging.getLogger(__name__)


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

