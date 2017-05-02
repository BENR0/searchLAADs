searchLAADS
===========

Module to search and download MODIS data via the SOAP API on the LAADS web.


Description
-----------

The searchLAADS module contains functions to search for MODIS data based on
a given time period and extent. The found files can then be downloaded from
the ftp server. Further more there are some functions which products and instruments
are available as well as functions to dump the URLs of found files to a text file,
check if files were downloaded correctly (needs gdal) and to check for files
which are missing from a given time period (e.g. were not downloaded).

The functions regarding searching and listing make use of the SOAP API whose
function can be found at the following link.

https://ladsweb.modaps.eosdis.nasa.gov/tools-and-services/lws-classic/api.php

Not all of the functions at this link are incorporated into the searchLAADS 
module, but might be added as needed in the future.


Usage
-----

There is an example script located in the scripts directory of the repository,
which showcases a possible usage case.

Once it is clear which product should be downloaded a typical workflow would be

1. Instantiate a new searcLAADS object by using the function with the same name
   and specifying start and end date and time as well as the extent for which to
   download data.

2. Use the searchFiles method of the instantiated object.

3. Optionally dump the URLs to a text file for later reference.

4. Download file with the downloadFiles() method

5. Optionally check if files were downloaded correctly with checkFiles().

6. Optionally check if some file could not be downloaded with checkMissing().
   The missing files will be writen to a text file which can be read into a
   searchLAADS instance to be able to try and download those files again.
   If logging was set up (see the example script) and the log will also show
   the files which could not be downloaded.


License
-------

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

