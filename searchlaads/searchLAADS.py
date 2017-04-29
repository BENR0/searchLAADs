import os
import math
from SOAPpy import WSDL
from SOAPpy import SOAPProxy
from datetime import datetime, timedelta


class searchLAADS(object):

    wsdl = "http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices?wsdl"
    serviceNamespace = "http://modapsws.gsfc.nasa.gov"
    serviceURL = "https://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices"
    server = SOAPProxy(serviceURL)

    LAADSmaxFiles = 3000

    def __init__(self, product, collection, stime, etime, bbox, coordsOrTiles, dayNightBoth):
        self.product = product
        self.collection = collection
        self.stime = datetime.strptime(stime, "%Y%m%d%H%M")
        self.etime = datetime.strptime(etime, "%Y%m%d%H%M")
        self.bbox = bbox
        self.cot = coordsOrTiles
        self.dnb = dayNightBoth
        self.fileURLs = []


    def numTilesForBbox(self):
        """Calculates the approximate number of tiles which cover the given extent

        Returns
        -------
        int
            Approximate number of tiles to be expected for given bbox.
        """
        
        numlat = (self.bbox[2] - self.bbox[3]) / 20    #one tile is approx. 25 degrees in lat
        numlon = (self.bbox[0] - self.bbox[1]) / 20     #and approx. 22 degrees in lon direction

        # print(numlat*20, numlon*20)
        return math.ceil(abs(numlat))*2 * math.ceil(abs(numlon))*2


    def estimNumFiles(self):
        """Estimates the number of files that need to be downloaded
        to cover the given extent for the specified time intervall.
        
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

        deltaHours = (self.etime - self.stime).total_seconds() / 3600
        numDaysNights = deltaHours / 12
        numFiles = numDaysNights * self.numTilesForBbox()

        return numFiles


    def timeChunks(self):
        """Splits the time intervall between starttime and endtime into chunks.
        The number of files returned by the "searchFiles" function is below the
        6000 limit for each time chunk.

        Returns
        -------
        list
            Returns a list of tuples with the start and endtime of each chunk.


        See Also
        --------
        numFiles: Number of files

        """

        #calculate number of chunks necessary
        numChunks = self.estimNumFiles() / self.LAADSmaxFiles

        #calculate time window for each chunk in hours
        deltaHours = (self.etime - self.stime).total_seconds() / 3600
        chunkHours = deltaHours / numChunks
        #calculate chunk size to full weeks
        chunkWeeks = math.ceil(chunkHours / (7 * 24))

        #create list with tuples of start and end times of chunks
        chunkStime = self.stime
        chunkList = []
        while chunkStime < self.etime:
            chunkEtime = chunkStime + timedelta(weeks = chunkWeeks)
            if chunkEtime < self.etime:
                chunkList.append((chunkStime, chunkEtime))
            else:
                chunkList.append((chunkStime, self.etime))

            #set startime of next chunk to endtime of last chunk
            chunkStime = chunkEtime

        return chunkList


    def list_prods():
        prods = server.listProducts()

        for item in prods:
            print(item["Name"])
        return


    def searchFiles(self):
        """Search LAADS web for files.
        Possible values of most parameters are listed in the LAADS web SOAP API
        documenation at:
        https://ladsweb.modaps.eosdis.nasa.gov/tools-and-services/lws-classic/api.php#searchForFiles

        Return
        ------
        list
            File IDs.


        See Also
        --------
        getFileURLs: Get file URLs for file IDs

        """

        north, south, west, east = self.bbox
        fileURLs = []

        tchunks = self.timeChunks()
        if len(tchunks) > 1:
            print("It seems your are trying to search for many files. This may take a while...")
        else:
            print("Searching for files...")


        for chunk in tchunks:
            starttime = chunk[0].strftime("%Y-%m-%d %H:%M")
            endtime = chunk[1].strftime("%Y-%m-%d %H:%M")

            IDs = self.server.searchForFiles(products=self.product, collection=self.collection, startTime=starttime, endTime=endtime,
                    north=north, south=south, east=east, west=west, coordsOrTiles=self.cot,
                    dayNightBoth=self.dnb)

            IDsFilestring = ",".join(IDs)
            URLs = self.server.getFileUrls(fileIds=IDsFilestring)

            self.fileURLs += URLs

        pass


    def dumpURLs(self, fname, replace = False):
        """Write URLs to file one each row.

        Parameters
        ----------
        fname: str
            filename
        replace: boolean (optional)
            overwrite file if exists

        Return
        ------
        """

        if len(self.fileURLs) < 1:
            print("There are no URLs to write. Please retrive file URLs by using the \"searchFiles\" function first.")
        else:
            #check if file exists
            if os.path.isfile(fname) & (not replace):
                print("The file already exists. Please choose another name or set the \"replace\" parameter to True.")
            else:
                with open(fname, "w") as f:
                    for i in self.fileURLs:
                        f.write(i + "\n")
        
        pass


# if __name__ == "__main__":
