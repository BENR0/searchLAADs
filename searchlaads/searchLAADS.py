# -*- coding: utf-8 -*-
import os
import math
# import progressbar
import urllib2
import re
import logging
#import gdal
from tqdm import tqdm
from SOAPpy import WSDL
from SOAPpy import SOAPProxy
from datetime import datetime, timedelta
from multiprocessing.dummy import Pool # use threads


logger = logging.getLogger(__name__)


class searchLAADS(object):

    wsdl = "http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices?wsdl"
    serviceNamespace = "http://modapsws.gsfc.nasa.gov"
    serviceURL = "https://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices"
    server = SOAPProxy(serviceURL)

    #Max results returned from LAADS web API is 6000
    #setting it lower to split large queries into many chunks
    #to avoid server 502 error
    LAADSmaxFiles = 1000

    def __init__(self, product, collection, stime, etime, bbox, coordsOrTiles, dayNightBoth):
        self.product = product
        self.collection = collection
        self.stime = datetime.strptime(stime, "%Y%m%d%H%M")
        self.etime = datetime.strptime(etime, "%Y%m%d%H%M")
        self.bbox = bbox
        self.cot = coordsOrTiles
        self.dnb = dayNightBoth
        self.fileURLs = []
        #path list also stores fileURLs so maybe change methods to accomodate that and remove
        self.pathList = []


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


    def list_prods(self):
        """Get a list of available products

        Return
        ------
        list: List of product names

        """

        prods = self.server.listProducts()

        prodList = [prod["Name"] for prod in prods]
        
        return prodList


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
        #hard coded maxRetries for fettching data from SOAP service
        maxRetries

        #split time window in chunks
        tchunks = self.timeChunks()

	logger.debug("Number of time chunks: {0}".format(len(tchunks)))
        if len(tchunks) > 1:
            logger.debug("It seems your are trying to search for many files. This may take a while...")
            print("It seems your are trying to search for many files. This may take a while...")
        else:
            logger.debug("Searching for files...")
            print("Searching for files...")


        for i in tqdm(range(len(tchunks))):
            starttime = tchunks[i][0].strftime("%Y-%m-%d %H:%M")
            endtime = tchunks[i][1].strftime("%Y-%m-%d %H:%M")
	    
            logger.debug("Getting file IDs for chunk {0} of {1}: {2}".format(i,len(tchunks),(starttime,endtime)))

            IDattempts = 0
            while IDattempts < maxRetries:
                try:
                    IDs = self.server.searchForFiles(products=self.product, collection=self.collection, startTime=starttime, endTime=endtime,
                            north=north, south=south, east=east, west=west, coordsOrTiles=self.cot,
                            dayNightBoth=self.dnb)
                except Exception, e:
                    logger.error(e)
                    logger.error("Failed to retrieve file IDs for chunk {0}: {1}".format(i, (starttime,endtime)))
                    pass

            IDsFilestring = ",".join(IDs)

            logger.debug("Getting file URLs for chunk {0} of {1}: {2}".format(i,len(tchunks),(starttime,endtime)))

            URLattempts = 0
            while URLattempts < maxRetries:
                try:
                    URLs = self.server.getFileUrls(fileIds=IDsFilestring)
                except Exception, e:
                    logger.error(e)
                    logger.error("Failed to retrieve file URLs for chunk {0}: {1}".format(i, (starttime,endtime)))
                    pass

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

        logger.debug("Dumping file URLs to text file")

        if len(self.fileURLs) < 1:
            logger.debug("There are no URLs to write. Please retrive file URLs by using the \"searchFiles\" function first.")
            print("There are no URLs to write. Please retrive file URLs by using the \"searchFiles\" function first.")
        else:
            #check if file exists
            if os.path.isfile(fname) & (not replace):
                logger.debug("The file already exists. Please choose another name or set the \"replace\" parameter to True.")
                print("The file already exists. Please choose another name or set the \"replace\" parameter to True.")
            else:
                with open(fname, "w") as f:
                    for i in self.fileURLs:
                        f.write(i + "\n")
        
        pass


    def loadURLsFromFile(self, fpath):
        """Load URLs from previously dumped text file

        Parameters
        ----------
        fpath: str
            Path to file

        Return
        ------
        Stores files list in objects fileURLS variable
        """

        if os.path.isfile(fpath):
            with open(fpath, "r") as f:
                data = f.readlines()

                for line in data:
                    self.fileURLs.append(line)
        else:
            print("File does not exist. Please check filename and path.")

        pass

        
    def downloadFiles(self, directory, maxRetries = 5, multiproc = False, numproc = 3):
        """Download URLs.

        Parameters
        ----------
        directory: str
            Base directory where to save files
        maxRetries: int
            Maximum number of retrys to open the url
        multiproc: boolean
            Download multiple files at the same time.
        numproc: int optional
            Number of processes if multiproc is set to True

        
        Return
        ------
        """
        def pathTuple(url, directory = directory):
            secfield = os.path.basename(url).split(".")[1]
            year = secfield[1:5]
            outdir = os.path.join(directory, year)
            return((url, outdir))

        def download(itemtuple):
            #unpack tuple
            url = itemtuple[0]
            directory = itemtuple[1]

            fname = os.path.basename(url)
            fpath = os.path.join(directory, fname)


            attempts = 0
            while attempts < maxRetries:
                try:
                    response = urllib2.urlopen(url)
                    attempts += 1
                except urllib2.URLError as e:
                    logger.debug(e)
                    logger.debug("File {0} failed to download with the above error".format(url))
                    pass

            with open(fpath, "wb") as f:
                f.write(response.read())

            #update progressbar
            pbar.update(1)


            return


        self.pathList = list(map(pathTuple, self.fileURLs))
        
        #create year directories separate to avoid race condition when
        #using it in the download function itself and multiprocessing enabled
        for d in set([x[1] for x in self.pathList]):
            #check if fpath exists. create if necessary 
            if not os.path.exists(d):
                os.makedirs(d)

        logger.debug("Starting download of files...")
        print("Starting download of files...")

        pbar = tqdm(total = len(self.pathList))

        if multiproc:
            p = Pool(numproc)
            p.map(download, self.pathList)
            p.close()
            p.join()
        else:
            map(download, self.pathList)
        
        pbar.close()


        #check if file was downloaded correctly else download again

        pass


    def checkFiles(self):
        """Check files if they were downloaded correctly

        Parameters
        ----------

        Return
        ------
        return: 0 if file is correct, 1 for error
        """

        def check(fpath):
            try:
                gdal.Open(fpath)
                return 0
            except (RuntimeError) as e:
                logger.error(e)
                return 1 

        print("Checking files...")
        for i in tqdm(range(len(self.pathList))):
            fToCheck = os.path.join(self.pathList[i][1], os.path.basename(self.pathList[i][0]))
            #TODO
            #store result of check somewhere and print result at the end
            check(fToCheck)

        pass

    
    def missingFiles(self, directory, outfile):
        """Check for missing files in time window.
        For example if file did not get downloaded correctly
        or was skipped due to server errors.

        Parameters
        ----------
        directory: str
            Basedirectory were downloaded files are stored
        outfile: str
            File to save results to.

        Returns
        -------
        Text file with missing file URLs
        """

        ###############
        #MOVE THIS FUNCTION TO A COMMON PLACE, THEN REMOVE FROM HERE AND FROM DOWNLOAD FUNCTION
        ##############
        def pathTuple(url, directory = directory):
            secfield = os.path.basename(url).split(".")[1]
            year = secfield[1:5]
            outdir = os.path.join(directory, year)
            return((url, outdir))


        self.pathList = list(map(pathTuple, self.fileURLs))
        #list for urls of missing files
        fmissing = []

        print("Checking for missing files...")
        with open(outfile, "w") as f:
            for i in tqdm(range(len(self.pathList))):
                fToCheck = os.path.join(self.pathList[i][1], os.path.basename(self.pathList[i][0]))
                #TODO
                #store result of check in object in addition to dump to text file to be able to download them again
                if not os.path.isfile(fToCheck):
                    f.write(self.pathList[i][0] + "\n")
                    fmissing.append(self.pathList[i][0])

        if len(fmissing) >= 1:
            print("There are {0} files missing".format(len(fmissing)))


        pass



# if __name__ == "__main__":