# import zeep
# from zeep.plugins import HistoryPlugin

# history = HistoryPlugin()
# # client = zeep.Client(wsdl=wsdl)
# client = zeep.Client(wsdl=wsdl, plugins = [history])

# # serv = client.create_service("{http://laads.modapsws.gsfc.nasa.gov}MODAPSservicesSoap12Binding","http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices")
# # serv = client.create_service("{http://laads.modapsws.gsfc.nasa.gov}MODAPSservicesHttpBinding","http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices")

# # serv = client.bind("MODAPSservices", "MODAPSservicesHttpSoap12Endpoint")

# # order_type = client.get_element("ns0:listProductsByInstrument")
# # order = zeep.xsd.AnyObject(order_type, order_type("AM1M"))
# value = zeep.xsd.AnyObject(zeep.xsd.String(), "AM1M")
# # response = client.service.listProductsByInstrument(instrument=value)
# client.service.listProductsByInstrument(value)
# # print(response)
# # response = serv.listProducts


#============================
#soapy

from SOAPpy import WSDL
from SOAPpy import SOAPProxy
import math
from datetime import datetime, timedelta

# server = WSDL.Proxy(wsdl)
# server.config.dumpSOAPOut = 1
# server.config.dumpSOAPIn = 1

# print(server.listProducts)

#start and end times as datetime obj
endtime = datetime(2017,4,27,00,00)
starttime = datetime(2010,4,25,00,00)

# endtime = "2017-04-27 00:00:00"
# # starttime = "2015-01-01 00:00:00"
# starttime = "2017-04-26 12:00:00"

product = "MOD35_L2"
collection = 6
north = 2.0
south = -15.0
east = -66.0
west = -82.0
coordsOrTiles = "coords"
dayNightBoth = "dbn"

bbox = [north,south,west,east]

class LAADSsearch(object):

    wsdl = "http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices?wsdl"
    serviceNamespace = "http://modapsws.gsfc.nasa.gov"
    serviceURL = "https://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices"

    LAADSmaxFiles = 5000

    def __init__(self, product, collection, stime, etime, bbox, coordsOrTiles, dayNightBoth):
        self.product = product
        self.collection = collection
        self.stime = datetime.strptime(stime, "%Y%m%d%H%M")
        self.etime = datetime.strptime(etime, "%Y%m%d%H%M")
        self.bbox = bbox
        self.cot = coordsOrTiles
        self.dnb = dayNightBoth


    def numTilesForBbox(bbox):
        """Calculates the approximate number of tiles which cover the given extent

        Parameters
        ----------
        bbox: list
            Bounding box of extent given as [north, south, west, east]


        Returns
        -------
        int
            Approximate number of tiles to be expected for given bbox.
        """
        
        numlat = (bbox[2] - bbox[3]) / 20    #one tile is approx. 25 degrees in lat
        numlon = (bbox[0] - bbox[1]) / 20     #and approx. 22 degrees in lon direction

        # print(numlat*20, numlon*20)
        return math.ceil(abs(numlat))*2 * math.ceil(abs(numlon))*2


    def estimFiles(numTiles, stime, etime):
        """Estimates the number of files that need to be downloaded
        to cover the given extent for the specified time intervall.

        Parameters
        ----------
        numTiles: int
            extimated tiles for bounding box calculated by numTilesForBbox
        stime: datetime
            starttime of time intervall
        etime: datetime
            endtime of time intervall

        
        Returns
        -------
        int
            Number of files


        See Also
        --------
        numTilesForBbox: number of tiles for bounding box

        """
        #calculate time difference between stime and etime in hours
        #divide by 12hours. for every twelve hours there are approx.
        #numtiles tiles.
        #for MOD35_L2 and MYD35_L2 there are actually only half of the daytime 12 hours scenes
        #available if dayNightBoth is specified

        deltaHours = (etime - stime).total_seconds() / 3600
        numDaysNights = deltaHours / 12
        numFiles = numDaysNights * numTiles

        return numFiles


    def timeChunks(stime, etime, numFiles):
        """Splits the time intervall between starttime and endtime into chunks.
        The number of files returned by the "searchFiles" function is below the
        6000 limit for each time chunk.

        Parameters
        ----------
        stime: datetime
            starttime
        etime: datetime
            endtime
        numFiles: int
            number of Files. Result of the "estimFiles" function.


        Returns
        -------
        list
            Returns a list of tuples with the start and endtime of each chunk.


        See Also
        --------
        numFiles: Number of files

        """

        #calculate number of chunks necessary
        numChunks = numFiles / LAADSmaxFiles

        #calculate time window for each chunk in hours
        deltaHours = (etime - stime).total_seconds() / 3600
        chunkHours = deltaHours / numChunks
        #calculate chunk size to full weeks
        chunkWeeks = math.ceil(chunkHours / (7 * 24))

        #create list with tuples of start and end times of chunks
        chunkStime = stime
        chunkList = []
        while chunkStime < etime:
            chunkEtime = chunkStime + timedelta(weeks = chunkWeeks)
            if chunkEtime < etime:
                chunkList.append((chunkStime, chunkEtime))
            else:
                chunkList.append((chunkStime, etime))

            #set startime of next chunk to endtime of last chunk
            chunkStime = chunkEtime

        return chunkList


    def list_prods():
        prods = server.listProducts()

        for item in prods:
            print(item["Name"])
        return


    def searchFiles(prod, coll, stime, etime, bbox, coordsOrTiles, dnb):
        """Search LAADS web for files.
        Possible values of most parameters are listed in the LAADS web SOAP API
        documenation at:
        https://ladsweb.modaps.eosdis.nasa.gov/tools-and-services/lws-classic/api.php#searchForFiles


        Parameters
        ----------
        prod: str
            product name
        coll: int
            collection to use
        stime: datetime
            start date and time of search window.
        etime: datetime
            end date and time of search window
        bbox: list 
            Bounding box in Degrees given as list [north, south, west, east]
        coordsOrTiles: str
            Specify if bbox is given in coords or tile numbers
        dnb:  str
            What data to include; day, night or have both. Values: d,n,dnb and combinations


        Return
        ------
        list
            File IDs.


        See Also
        --------
        getFileURLs: Get file URLs for file IDs

        """
        server = SOAPProxy(self.serviceURL)

        north, south, west, east = self.bbox

        #check if expected number of files is above limit of SOAP service.
        #if true then get file ids iteratively with time chunks
        numExpFiles = numFiles(stime, etime, numTilesForBbox(bbox))

        if numExpFiles > LAADSmaxFiles:

        starttime = stime.strftime("%Y-%m-%d %H:%M")
        endtime = etime.strftime("%Y-%m-%d %H:%M")

        fileIDs = server.searchForFiles(products=prod, collection=coll, startTime=starttime, endTime=endtime,
                north=north, south=south, east=east, west=west, coordsOrTiles=coordsOrTiles, dayNightBoth=dnb)

        return fileIDs

# print(estimFiles(numTilesForBbox(bbox), starttime, endtime))
# print(timeChunks(starttime, endtime, estimFiles(numTilesForBbox(bbox), starttime, endtime)))
# print(len(searchFiles(product,collection,starttime,endtime,[north,south,west,east],coordsOrTiles,dayNightBoth)))




# filestring = ",".join(fileIDs)

# fileURLs = server.getFileUrls(fileIds=filestring)
    

#============================
#suds

# from suds.client import Client

# client = Client(url =  wsdl, location = serviceURL)

# print(client.service.listProductsByInstrument(instrument="AM1M"))
