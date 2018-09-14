# -*- coding: utf-8 -*-
import os
import math
# import progressbar
import urllib2
import re
import logging
import random
import gdal
from tqdm import tqdm
from SOAPpy import WSDL
from SOAPpy import SOAPProxy
from datetime import datetime, timedelta
from multiprocessing.dummy import Pool # use threads


logger = logging.getLogger(__name__)

#web service function description
#https://ladsweb.modaps.eosdis.nasa.gov/tools-and-services/lws-classic/api.php
#websites with more information about modis products
#land products overview (filenames etc.):
#https://lpdaac.usgs.gov/dataset_discovery/modis
#land products table:
#https://lpdaac.usgs.gov/dataset_discovery/modis/modis_products_table
#atmosphere and cloud products overview
#https://modis-atmos.gsfc.nasa.gov/products

class searchLAADS(object):

    wsdl = "http://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices?wsdl"
    serviceNamespace = "http://modapsws.gsfc.nasa.gov"
    serviceURL = "https://modwebsrv.modaps.eosdis.nasa.gov/axis2/services/MODAPSservices"
    server = SOAPProxy(serviceURL)

    #Max results returned from LAADS web API is 6000
    #setting it lower to split large queries into many chunks
    #to avoid server 502 error
    LAADSmaxFiles = 1000

    def __init__(self, product, collection, stime, etime, bbox, coordsOrTiles = "coords", dayNightBoth = "DNB", targetDir = None):
        #TODO
        #add checks for init variables
        #add defaults for missing values
        #errors for required values
        self.product = product
        self.collection = collection
        self.stime = datetime.strptime(stime, "%Y%m%d%H%M")
        self.etime = datetime.strptime(etime, "%Y%m%d%H%M")
        #north, south, west, east = bbox
        self.bbox = bbox
        self.cot = coordsOrTiles
        self.dnb = dayNightBoth
        self.targetDir = targetDir
        self.fileURLs = []
        #path list also stores fileURLs so maybe change methods to accomodate that and remove
        self.pathList = []


    def _numTilesForBbox(self):
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


    def _estimNumFiles(self):
        """Estimates the number of files that need to be downloaded
        to cover the given extent for the specified time intervall.
        
        Returns
        -------
        int
            Number of files


        See Also
        --------
        _numTilesForBbox: number of tiles for bounding box

        """
        #calculate time difference between stime and etime in hours
        #divide by 12hours. for every twelve hours there are approx.
        #numtiles tiles.
        #for MOD35_L2 and MYD35_L2 there are actually only half of the daytime 12 hours scenes
        #available if dayNightBoth is specified

        deltaHours = (self.etime - self.stime).total_seconds() / 3600
        numDaysNights = deltaHours / 12
        numFiles = numDaysNights * self._numTilesForBbox()

        return numFiles


    def _timeChunks(self):
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
        numChunks = self._estimNumFiles() / self.LAADSmaxFiles

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


    def getListOf(self, get = None, args = None):
        """Get a list of available products

        Parameters
        ----------
        get: str
            Keyword for what to get a list of
        args: str
            Additional arguments needed e.g. instrument for ProdsByInstrument

        Return
        ------
        list: list of results

        """
        keywords = {"instruments": "listSatelliteInstruments", "products": "listProducts",
                "prodsByInstrument": "listProductsByInstrument", "groups": "listProductGroups"}

        #define array with results from instruments as workaround because SOAP
        #call to listSatelliteInstruments is not working
        results = [("AM1M","Terra MODIS"), ("ANC","Ancillary Data"), ("PM1M","Aqua MODIS"),
                ("AMPM","Combined Aqua & Terra MODIS"), ("NPP","Suomi NPP VIIRS")]

        try:
            if get is None:
                raise TypeError
            else:
                if (get == "prodsByInstrument") or (get == "groups"):
                    try:
                        if args is None:
                            raise TypeError
                        else:
                            toCall = getattr(self.server, keywords[get])#(instrument = args)
                            answer = toCall(instrument = args)
                    except TypeError:
                        print("No instrument given.")
                        print("Possible values for instrument are:")
                        # print(getattr(self.server, "getListOf")(get = keywords["instruments"]))
                        # print(self.server.listSatelliteInstruments)
                        for i in results:
                            print("{:18} {}".format(i[0], i[1]))
                elif get == "products":
                    toCall = getattr(self.server, keywords[get])
                    answer = toCall()

            
            if get == "products":
                results = [(item["Name"], item["Description"]) for item in answer]
            # elif (get == "instruments") or (get == "groups"):
            elif get == "groups":
                results = [(item["name"], item["value"]) for item in answer]
            elif get == "prodsByInstrument":
                results = [(item, "") for item in answer]

            #print results to screen
            print("Available {0}:".format(get))
            for i in results:
                print("{:18} {}".format(i[0], i[1]))
            

            return results

        except TypeError:
            print("Nothing specified to list.")
            print("Possible values for get are:")
            for key in keywords.keys():
                print(key)

        pass
        


    def searchFiles(self, getGeoLoc = False, maxRetries = 5):
        """Search LAADS web for files.
        Possible values of most parameters are listed in the LAADS web SOAP API
        documenation at:
        https://ladsweb.modaps.eosdis.nasa.gov/tools-and-services/lws-classic/api.php#searchForFiles

        Parameters
        ----------
        getGeoLoc: boolean
            Also search for corresponding geolocation files.

        Return
        ------
        list
            File IDs.


        See Also
        --------
        getFileURLs: Get file URLs for file IDs

        """

        north, south, west, east = self.bbox

        #search string for geoloaction
        #if getGeoLoc:
            #if self.product == "MOD":
                #self.product = ",".join([self.product, "MOD03"])
            #else:
                #self.product = ",".join([self.product, "MYD03"])

        #split time window in chunks
        tchunks = self._timeChunks()

	logger.debug("Number of time chunks: {0}".format(len(tchunks)))
        if len(tchunks) > 1:
            msg = "It seems your are trying to search for many files. This may take a while..."
            logger.info(msg)
        else:
            msg = "Searching for files..."
            logger.info(msg)


        for i in tqdm(range(len(tchunks))):
            starttime = tchunks[i][0].strftime("%Y-%m-%d %H:%M:%S")
            endtime = tchunks[i][1].strftime("%Y-%m-%d %H:%M:%S")
	    
            logger.debug("Getting file IDs for chunk {0} of {1}: {2}".format(i,len(tchunks),(starttime,endtime)))

            IDattempts = 0
            while IDattempts < maxRetries:
                try:
                    IDs = self.server.searchForFiles(products=self.product, collection=self.collection, startTime=starttime, endTime=endtime,
                            north=north, south=south, east=east, west=west, coordsOrTiles=self.cot,
                            dayNightBoth=self.dnb)
                    break
                except Exception, e:
                    logger.error(e)
                    logger.error("Failed to retrieve file IDs for chunk {0}: {1}".format(i, (starttime,endtime)))
                    IDattempts += 1
                    pass

            IDsFilestring = ",".join(IDs)

            logger.debug("Getting file URLs for chunk {0} of {1}: {2}".format(i,len(tchunks),(starttime,endtime)))

            URLattempts = 0
            while URLattempts < maxRetries:
                try:
                    URLs = self.server.getFileUrls(fileIds=IDsFilestring)
                    break
                except Exception, e:
                    logger.error(e)
                    logger.error("Failed to retrieve file URLs for chunk {0}: {1}".format(i, (starttime,endtime)))
                    URLattempts += 1
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

        logger.info("Dumping file URLs to text file")

        if len(self.fileURLs) < 1:
            msg = "There are no URLs to write. Please retrive file URLs by using the \"searchFiles\" function first."
            logger.debug(msg)
            print(msg)
        else:
            #check if file exists
            if os.path.isfile(fname) & (not replace):
                msg = "The file already exists. Please choose another name or set the \"replace\" parameter to True."
                logger.debug(msg)
                print(msg)
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

        print("Reading URLs from file...")
        if os.path.isfile(fpath):
            with open(fpath, "r") as f:
                data = f.read().splitlines()

                for line in data:
                    self.fileURLs.append(line)
        else:
            print("File does not exist. Please check filename and path.")

        pass

        
    def downloadFiles(self, directory = None, maxRetries = 5, multiproc = False, numproc = 3, overwrite = False):
        """Download URLs.

        TODO
        ----
        - overwrite parameter: to be able to skip or overwrite existing files
        - write urls of failed downloads to file?

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
        overwrite: boolean
            Should existing files be overwritten?

        
        Return
        ------
        """
        directory = self.targetDir

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
	    if not os.path.isfile(fpath):
                while attempts < maxRetries:
                    try:
                        response = urllib2.urlopen(url)
		        with open(fpath, "wb") as f:
		 	    f.write(response.read())

                        break
                    except urllib2.URLError as e:
                        logger.debug(e)
                        logger.debug("File {0} failed to download with the above error".format(url))
                        if attempts == maxRetries -1:
                            with open("download_failed.txt", "w") as f:
                                f.write(url + "\n")

                        attempts += 1
                        pass

            #update progressbar
            pbar.update(1)

            return


        try:
            if directory is not None:
                self.pathList = list(map(pathTuple, self.fileURLs))
            else:
                raise TypeError
        except TypeError:
            print("""No target directory were to store files given. Instantiate search obejct with 
                    directory or set the directory parameter of downloadFiles.""")
        
        #create year directories separate to avoid race condition when
        #using it in the download function itself and multiprocessing enabled
        for d in set([x[1] for x in self.pathList]):
            #check if fpath exists. create if necessary 
            if not os.path.exists(d):
                os.makedirs(d)

        msg = "Starting download of files..."
        logger.info(msg)
        #print(msg)

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


    def checkFiles(self, directory = None, outfile = None):
        """Check files if they were downloaded correctly

        TODO
        ----
        - Combine this and the following function since most of the code is the same

        Parameters
        ----------
        directory: str
            Basedirectory were downloaded files are stored
        outfile: str
            File to save results to.

        Return
        ------
        return: File with URLs of broken files
        return: 0 if file is correct, 1 for error

        Notes
        -----
        Needs gdal installed
        """

        directory = self.targetDir

        ###############
        #MOVE THIS FUNCTION TO A COMMON PLACE, THEN REMOVE FROM HERE AND FROM DOWNLOAD FUNCTION
        ##############
        def pathTuple(url, directory = directory):
            secfield = os.path.basename(url).split(".")[1]
            year = secfield[1:5]
            outdir = os.path.join(directory, year)
            return((url, outdir))


        def check(fpath):
            try:
                gdal.Open(fpath)
                return 0
            except (RuntimeError) as e:
                logger.error(e)
                return fpath 

        if len(self.fileURLs) >= 1:
            try:
                if directory is not None:
                    self.pathList = list(map(pathTuple, self.fileURLs))
                else:
                    raise TypeError
            except TypeError:
                print("""No target directory were to store files given. Instantiate search obejct with
                        directory or set the directory parameter of downloadFiles.""")
        else:
            print("Search for files first.")


        self.brokenFiles = []
        print("Checking files...")

        directory = self.targetDir

        def pathTuple(url, directory = directory):
            secfield = os.path.basename(url).split(".")[1]
            year = secfield[1:5]
            outdir = os.path.join(directory, year)
            return((url, outdir))


        #TODO
        #make it possible to instantiate object/ read in list of urls and directory with files
        #to check
        if len(self.fileURLs) >= 1:
            try:
                if directory is not None:
                    self.pathList = list(map(pathTuple, self.fileURLs))
                else:
                    raise TypeError
            except TypeError:
                print("""No target directory were to store files given. Instantiate search obejct with
                        directory or set the directory parameter of downloadFiles.""")
        else:
            print("Search for files first.")

        #list for urls of missing files
        fmissing = []

        print("Checking for missing files...")
        try:
            with open(outfile, "w") as f:
                for i in tqdm(range(len(self.pathList))):
                    fToCheck = os.path.join(self.pathList[i][1], os.path.basename(self.pathList[i][0]))
                    #TODO
                    #store result of check in object in addition to dump to text file to be able to download them again
                    resCheck = check(fToCheck)
                    if resCheck == 1:
                        f.write(self.pathList[i][0] + "\n")
                        fmissing.append(self.pathList[i][0])
        except IOError as e:
            print("Not outputfile given.")

        if len(fmissing) >= 1:
            print("There are {0} files missing".format(len(fmissing)))

        pass

    
    def checkMissing(self, directory = None, outfile = None):
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


        directory = self.targetDir

        ###############
        #MOVE THIS FUNCTION TO A COMMON PLACE, THEN REMOVE FROM HERE AND FROM DOWNLOAD FUNCTION
        ##############
        directory = self.targetDir

        def pathTuple(url, directory = directory):
            secfield = os.path.basename(url).split(".")[1]
            year = secfield[1:5]
            outdir = os.path.join(directory, year)
            return((url, outdir))

        #TODO
        #make it possible to instantiate object/ read in list of urls and directory with files
        #to check
        if len(self.fileURLs) >= 1:
            try:
                if directory is not None:
                    self.pathList = list(map(pathTuple, self.fileURLs))
                else:
                    raise TypeError
            except TypeError:
                print("""No target directory were to store files given. Instantiate search obejct with
                        directory or set the directory parameter of downloadFiles.""")
        else:
            print("Search for files or read in URLs from file first ")

        #list for urls of missing files
        fmissing = []

        print("Checking for missing files...")
        try:
            with open(outfile, "w") as f:
                for i in tqdm(range(len(self.pathList))):
                    fToCheck = os.path.join(self.pathList[i][1], os.path.basename(self.pathList[i][0]))
                    #TODO
                    #store result of check in object in addition to dump to text file to be able to download them again
                    if not os.path.isfile(fToCheck):
                        f.write(self.pathList[i][0] + "\n")
                        fmissing.append(self.pathList[i][0])
        except IOError as e:
            print("Not outputfile given.")

        if len(fmissing) >= 1:
            print("There are {0} files missing".format(len(fmissing)))


        pass

    
    def estimateHDDspace(self, nsamples = 20):
        """Estimate disk space needed to download all files
        found in search.

        Parameters
        ----------
        nsamples: integer
            number of samples to consider for estimating needed space, default 20

        Returns
        -------
        float
        """
        print("Estimating needed HDD space. This may take a couple of seconds.")
        size = 0

        fids = random.sample(range(len(self.fileURLs)), nsamples)
        sampledURLs = [self.fileURLs[i] for i in fids]

        for url in sampledURLs:
            response = urllib2.urlopen(url)
            csize = response.info().get("Content-Length")
            if csize is None:
                csize = 0
            size += float(csize)

        #convert file size to Mb and calculate mean
        size = float(size)/1024.0/1024.0/nsamples*len(self.fileURLs)
        print("The download of the files for the selected time intervall and domain approximately needs {space:d} Mb of hard disk space".format(space = int(size)))

        return size

# if __name__ == "__main__":
