#! /usr/bin/python
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def plot_domain(bbox):
    """
    Plot domain given by lon/lat corners
    
    Parameters
    ----------
    bbox : list
        List of minmal and maximal borders [north, south, west, east]
    
    Returns
    -------
    Nothing
    
    """
    
    maxlat, minlat, minlon, maxlon = bbox #[north, south, west, east]

    x, y = [minlon, minlon, maxlon, maxlon, minlon], [minlat, maxlat, maxlat, minlat, minlat]

    fig = plt.figure()

    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    #ax.stock_img()
    ax.coastlines()
    ax.plot(x, y, marker='o', transform=ccrs.PlateCarree())
    ax.fill(x, y, color='coral', transform=ccrs.PlateCarree(), alpha=0.4)
    ax.add_feature(cfeature.BORDERS)
    ax.set_extent([minlon -10, maxlon + 10, minlat - 10, maxlat + 10], crs=ccrs.PlateCarree()) #[minlon, maxlon, minlat, maxlat]
    plt.show()
    
    return
