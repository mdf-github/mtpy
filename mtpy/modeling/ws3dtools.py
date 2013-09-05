# -*- coding: utf-8 -*-
"""
Created on Mon Apr 02 11:54:33 2012

@author: a1185872
"""

import os,sys
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.patches import Ellipse
from matplotlib.colors import LinearSegmentedColormap,Normalize
import matplotlib.colorbar as mcb
import matplotlib.gridspec as gridspec
import mtpy.core.z as mtz
import mtpy.core.edi as mtedi
import mtpy.imaging.mtplottools as mtplottools
import matplotlib.widgets as widgets
import matplotlib.colors as colors
import matplotlib.cm as cm

import mtpy.utils.latlongutmconversion as ll2utm

#tolerance to find frequencies
ptol = .15

#error of data in percentage
zerr = .05
#errormap values which is multiplied by zerr to get a total error
zxxerrmap = 10
zxyerrmap = 1
zyxerrmap = 1
zyyerrmap = 10
zerrmap = [zxxerrmap,zxyerrmap,zyxerrmap,zyyerrmap]

#==============================================================================
# Colormaps for plots
#==============================================================================
#phase tensor map
ptcmapdict = {'red':((0.0,1.0,1.0),(1.0,1.0,1.0)),
            'green':((0.0,0.0,1.0),(1.0,0.0,1.0)),
            'blue':((0.0,0.0,0.0),(1.0,0.0,0.0))}
ptcmap = LinearSegmentedColormap('ptcmap',ptcmapdict,256)

#phase tensor map for difference (reverse)
ptcmapdictr = {'red':((0.0,1.0,1.0),(1.0,1.0,1.0)),
            'green':((0.0,1.0,0.0),(1.0,1.0,0.0)),
            'blue':((0.0,0.0,0.0),(1.0,0.0,0.0))}
ptcmapr = LinearSegmentedColormap('ptcmapr',ptcmapdictr,256)

#resistivity tensor map for calculating delta
ptcmapdict2 = {'red':((0.0,1.0,0.0),(1.0,1.0,0.0)),
            'green':((0.0,0.5,0.5),(1.0,0.5,0.5)),
            'blue':((0.0,0.5,0.5),(1.0,0.5,0.5))}
ptcmap2 = LinearSegmentedColormap('ptcmap2',ptcmapdict2,256)

#resistivity tensor map for calcluating resistivity difference
rtcmapdict = {'red':((0.0,0.0,0.0),(0.5,1.0,1.0),(1.0,1.0,0.0)),
            'green':((0.0,0.0,0.0),(0.5,1.0,1.0),(1.0,0.0,0.0)),
            'blue':((0.0,0.0,1.0),(0.5,1.0,1.0),(1.0,0.0,0.0))}
rtcmap = LinearSegmentedColormap('rtcmap',rtcmapdict,256)

#resistivity tensor map for calcluating apparent resistivity
rtcmapdictr = {'red':((0.0,1.0,1.0),(0.5,1.0,1.0),(1.0,0.0,0.0)),
            'green':((0.0,0.0,0.0),(0.5,1.0,1.0),(1.0,0.0,0.0)),
            'blue':((0.0,0.0,0.0),(0.5,1.0,1.0),(1.0,1.0,1.0))}
rtcmapr = LinearSegmentedColormap('rtcmapr',rtcmapdictr,256)

#==============================================================================
#  define some helping functions
#==============================================================================
#make a class to pick periods
class ListPeriods:
    def __init__(self,fig):
        self.plst = []
        self.fig = fig
        self.count = 1
    
    def connect(self):
        self.cid = self.fig.canvas.mpl_connect('button_press_event',
                                                self.onclick)
    def onclick(self,event):
        print '{0} Period: {1:.5g}'.format(self.count,event.xdata)
        self.plst.append(event.xdata)
        self.count += 1

    def disconnect(self):
        self.fig.canvas.mpl_disconnect(self.cid)

def readWLOutFile(out_fn,ncol=5):
    """
    read .out file from winglink
    
    Inputs:
        out_fn = full path to .out file from winglink
        
    Outputs:
        dx,dy,dz = cell nodes in x,y,z directions (note x is to the West here
                    and y is to the north.)
    """
    
    wingLinkDataFH = file(out_fn,'r')
    raw_data       = wingLinkDataFH.read().strip().split()
    
    nx = int(raw_data[0])
    ny = int(raw_data[1])
    nz = int(raw_data[2])


    dx = np.zeros(nx)
    dy = np.zeros(ny)
    dz = np.zeros(nz)
    
    for x_idx in range(nx):
      dx[x_idx] = raw_data[x_idx + 5]
    for y_idx in range(ny):
      dy[y_idx] = raw_data[y_idx + 5 + nx]
    for z_idx in range(nz):
      dz[z_idx] = raw_data[z_idx + 5 + nx + ny]
            
    return dx,dy,dz
    
def readSitesFile(sites_fn):
    """
    read sites_ file output from winglink
    
    Input: 
        sites_fn = full path to the sites file output by winglink
        
    Output:
        slst = list of dictionaries for each station.  Keys include:
            station = station name
            dx = number of blocks from center of grid in East-West direction
            dy = number of blocks from center of grid in North-South direction
            dz = number of blocks from center of grid vertically
            number = block number in the grid
        sitelst = list of station names 
    """
    
    sfid = file(sites_fn,'r')
    slines = sfid.readlines()
    
    slst = []
    sitelst = []
    for ss in slines:
        sdict = {}
        sline = ss.strip().split()
        sdict['station'] = sline[0][0:-4]
        sdict['dx'] = int(sline[1])-1
        sdict['dy'] = int(sline[2])-1
        sdict['dz'] = int(sline[3])-1
        sdict['something'] = int(sline[4])
        sdict['number'] = int(sline[5])
        slst.append(sdict)
        sitelst.append(sline[0][0:-4])
    return slst,sitelst
    
def getXY(sites_fn,out_fn,ncol=5):
    """
    get x (e-w) and y (n-s) position of station and put in middle of cell
    
    Input:
        sites_fn = full path to sites file output from winglink
        out_fn = full path to .out file output from winglink
        ncol = number of columns the data is in
        
    Outputs:
        coord_dict = dictionary with xy coordinate-tuples for the stations
        (keys are stationnames)
        #xarr = array of relative distance for each station from center of the
        #        grid.  Note this is W-E direction
        #yarr = array of relative distance for each station from center of the
        #        grid.  Note this is S-N direction
                
    """
    
    slst,sitelst = readSitesFile(sites_fn)
    
    dx,dy,dz = readWLOutFile(out_fn,ncol=ncol)
    x_totallength = np.sum(dx)
    y_totallength = np.sum(dy)
    z_totaldepth = np.sum(dz)

    x_coords = []
    position = 0.

    position = 0.5*dx[0]
    x_coords.append(position)
    for i in range(len(dx)-1):
        position += 0.5*(dx[i]+dx[i+1])
        x_coords.append(position)
    x_coords = [i-0.5*x_totallength for i in x_coords]
    
    y_coords = []
    position = 0.5*dy[0]
    y_coords.append(position)
    for i in range(len(dy)-1):
        position += 0.5*(dy[i]+dy[i+1])
        y_coords.append(position)

    y_coords = [i-0.5*y_totallength for i in y_coords]
    
    ns = len(slst)
    nxh = len(dx)/2
    nyh = len(dy)/2
    xarr = np.zeros(ns)
    yarr = np.zeros(ns)
    
    coord_dict = {}
    for ii,sdict in enumerate(slst):
        xx = sdict['dx']
        yy = sdict['dy']
        station = sdict['station']
        coord_dict[station] = (x_coords[xx],y_coords[yy])
        # xarr[ii] = x_coords[xx]
        # yarr[ii] = y_coords[yy]
        # print sdict, xarr[ii],yarr[ii]

    return coord_dict#xarr,yarr  

def getPeriods(edilst,errthresh=10):
    """
    Plots periods for all stations in edipath and the plot is interactive, just
    click on the period you want to select and it will appear in the console,
    it will also be saved to lp.plst.  To sort this list type lp.plst.sort()
    
    The x's mark a conformation that the station contains that period.  So 
    when looking for the best periods to invert for look for a dense line of 
    x's
    
    Inputs:
        edipath = path to where all your edi files are.  Note that only the 
            impedance components are supported so if you have spectra data, 
            export them from wingling to have impedance information.
        errthresh = threshold on the error in impedance estimation, this just 
                    gives an indication on where bad stations and bad periods
                    are, anything above this level will be colored in red.
    
    Outputs:
        periodlst = list of periods for each station
        errorlst = error in the impedance determinant for each station at 
                   each period.
        lp = data type lp has attributes: 
            plst = period list of chosen periods, again to sort this list type
                    lp.plst.sort().  this will then be the input to make the 
                    data file later.
        
    """

    
    plt.rcParams['font.size'] = 10
    plt.rcParams['figure.subplot.left'] = .13
    plt.rcParams['figure.subplot.right'] = .98
    plt.rcParams['figure.subplot.bottom'] = .1
    plt.rcParams['figure.subplot.top'] = .95
    plt.rcParams['figure.subplot.wspace'] = .25
    plt.rcParams['figure.subplot.hspace'] = .05    
    
    periodlst = []
    errorlst = []
    
    fig1 = plt.figure(5)
    ax = fig1.add_subplot(1,1,1)
    for edi in edilst:
        if not os.path.isfile(edi):
            print 'Could not find '+edi
        else:
            z1 = mtedi.Edi()
            z1.readfile(edi)
            periodlst.append(z1.period)
            zdet = np.array([np.sqrt(abs(np.linalg.det(zz))) 
                             for zz in z1.Z.z])
            error = np.array([np.sqrt(abs(np.linalg.det(zz))) 
                              for zz in z1.Z.zerr])
            perror = (error/zdet)*100 
            errorlst.append(perror)
            #make a plot to pick frequencies from showing period and percent 
            #error
            ax.scatter(z1.period, 
                       perror, 
                       marker='x', 
                       picker=5)
            pfind = np.where(perror>errthresh)[0]
            if len(pfind)>0: 
                print 'Error greater than {0:.3f} for {1}'.format(errthresh,
                                                                  z1.station)
                for jj in pfind:
                    ax.scatter(z1.period[jj], 
                               perror[jj],
                               marker='x',
                               color='r')
                    ax.text(z1.period[jj],
                            perror[jj]*1.05,
                            z1.station,
                            horizontalalignment='center',
                            verticalalignment='baseline',
                            fontdict={'size':8,'color':'red'})
                    print jj, z1.period[jj]
                    
    ax.set_xscale('log')
    ax.set_xlim(10**np.floor(np.log10(z1.period.min())),
                10**np.ceil(np.log10(z1.period.max())))
    ax.set_ylim(0, 3*errthresh)
    ax.set_yscale('log')
    ax.set_xlabel('Period (s)',fontdict={'size':12,'weight':'bold'})
    ax.set_ylabel('Percent Error',fontdict={'size':12,'weight':'bold'})
    ax.grid('on',which='both')    
    
    lp = ListPeriods(fig1)
    lp.connect()
    
    plt.show()
        
    return periodlst, errorlst, lp
    
def make3DGrid(edilst, xspacing=500, yspacing=500, z1layer=10, xpad=5, ypad=5,
               zpad=5, xpadroot=5, ypadroot=5, zpadroot=2, zpadpow=(5,15),
                nz=30, plotyn='y', plotxlimits=None, plotylimits=None,
                plotzlimits=None):
    """
    makes a grid from the edifiles to go into wsinv3d.  The defaults usually
    work relatively well, but it might take some effort to get a desired grid.

    Inputs:
    --------
        **edilst** : list
                     list of full paths to the .edi files to be included in 
                     the inversion.
        
        **xspacing** : float
                       spacing of cells in the east-west direction in meters.
                       *default* is 500 (m)
                       
        **yspacing** : float
                       spacing of cells in the north-south direction in meters.
                       *default* is 500 (m)
                       
        **z1layer** : float
                      the depth of the first layer in the model in meters.  
                      This is usually about 1/10th of your shallowest skin 
                      depth.
                      *default* is 10 (m)
                      
        **xpad** : int
                   number of cells to pad on either side in the east-west 
                   direction.  The width of these cells grows exponentially 
                   to the edge.
                   *default* is 5
                      
        **ypad** : int
                   number of cells to pad on either side in the north-south 
                   direction.  The width of these cells grows exponentially 
                   to the edge.
                   *default* is 5
                      
        **zpad** : int
                   number of cells to pad on either side in the vertical 
                   direction.  This is to pad beneath the depth of 
                   investigation and grows faster exponentially than the zone 
                   of study.  The purpose is to decrease the number of cells
                   in the model.
                   *default* is 5
                   
        **xpadroot** : float
                       the root number that is multiplied to itself for 
                       calculating the width of the padding cells in the 
                       east-west direction.
                       *default* is 5
                   
        **ypadroot** : float
                       the root number that is multiplied to itself for 
                       calculating the width of the padding cells in the 
                       north-south direction.
                       *default* is 5
                       
        **zpadroot** : float
                       the root number that is multiplied to itself for 
                       calculating the width of the padding cells in the 
                       vertical direction.
                       *default* is 2
                       
        **zpadpow** : tuple (min,max)
                      the power to which zpadroot is raised for the padding
                      cells in the vertical direction.  Input as a tuple with
                      minimum power and maximum power.
                      *default* is (5,15)
                      
        **nz** : int
                 number of layers in the vertical direction.  Remember that 
                 the inversion code automatically adds 7 air layers to the 
                 model which need to be used when estimating the memory that
                 it is going to take to run the model.
                 *default* is 30
                 
        **plotyn** : [ 'y' | 'n' ]
                     if plotyn=='y' then a plot showing map view (east:north)
                     and a cross sectional view (east:vertical) plane                     
                     
                     * 'y' to plot the grid with station locations
                     
                     * 'n' to suppress the plotting.
                    
        **plotxlimits** : tuple (xmin,xmax)
                         plot min and max distances in meters for the east-west 
                         direction.  If not input, the xlimits will be set to 
                         the furthest stations east and west.
                         *default* is None
                    
        **plotylimits** : tuple (ymin,ymax)
                         plot min and max distances in meters for the east-west 
                         direction. If not input, the ylimits will be set to 
                         the furthest stations north and south.
                         *default* is None
                    
        **plotzlimits** : tuple (zmin,zmax)
                         plot min and max distances in meters for the east-west 
                         direction.  If not input, the zlimits will be set to 
                         the nz layer and 0.
                         *default* is None
                         
    Returns:
    --------
        xgrid,ygrid,zgrid,locations,slst
        **xgrid** : np.array
                    array of the east-west cell locations  
                    
        **ygrid** : np.array
                    array of the north-south cell locations
                    
        **zgrid** : np.array
                    array of the vertical cell locations 
                    
        **locations** : np.array (ns,2)
                        array of station locations placed in the center of 
                        the cells. 
                        * column 1 is for east-west locations
                        * column 2 is for the north-south location
                        
        **slst** : list
                   list of dictionaries for each station with keys:
                       * *'station'* for the station name
                       * *'east'* for easting in model coordinates
                       * *'east_c'* for easting in model coordinates to place 
                                    the station at the center of the cell 
                       * *'north'* for northing in model coordinates
                       * *'north_c'* for northing in model coordinates to place 
                                    the station at the center of the cell 
                        
                       
    :Example: ::
        
        >>> import mtpy.modeling.ws3dtools as ws
        >>> import os
        >>> edipath=r"/home/edifiles"
        >>> edilst=[os.path.join(edipath,edi) for os.listdir(edipath)]
        >>> xg,yg,zg,loc,statlst=ws.make3DGrid(edilst,plotzlimits=(-2000,200))
    
    """
    ns = len(edilst)
    slst = np.zeros(ns, dtype=[('station','|S10'), ('east', np.float),
                               ('north', np.float), ('east_c', np.float),
                               ('north_c', np.float)])
    for ii,edi in enumerate(edilst):
        zz = mtedi.Edi()
        zz.readfile(edi)
        zone, east, north = ll2utm.LLtoUTM(23, zz.lat, zz.lon)
        slst[ii]['station'] = zz.station
        slst[ii]['east'] = east
        slst[ii]['north'] = north
    
    #estimate the mean distance to  get into relative coordinates
    xmean = slst['east'].mean()
    ymean = slst['north'].mean()
     
    #remove the average distance to get coordinates in a relative space
    slst['east'] -= xmean
    slst['north'] -= ymean
 
    #translate the stations so they are relative to 0,0
    xcenter = (slst['east'].max()-np.abs(slst['east'].min()))/2
    ycenter = (slst['north'].max()-np.abs(slst['north'].min()))/2
    
    #remove the average distance to get coordinates in a relative space
    slst['east'] -= xcenter
    slst['north'] -= ycenter

    #pickout the furtherst south and west locations 
    #and put that station as the bottom left corner of the main grid
    xleft = slst['east'].min()-xspacing/2
    xright = slst['east'].max()+xspacing/2
    ybottom = slst['north'].min()-yspacing/2
    ytop = slst['north'].max()+yspacing/2

    #---make a grid around the stations from the parameters above---
    #make grid in east-west direction
    midxgrid = np.arange(start=xleft,stop=xright+xspacing,
                         step=xspacing)
    xpadleft = np.round(-xspacing*xpadroot**np.arange(start=.5,
                                                      stop=3,
                                                      step=3./xpad))+xleft
    xpadright = np.round(xspacing*xpadroot**np.arange(start=.5,
                                                      stop=3,
                                                      step=3./xpad))+xright
    xgridr = np.append(np.append(xpadleft[::-1], midxgrid), xpadright)
    
    #make grid in north-south direction 
    midygrid = np.arange(start= ybottom, stop=ytop+yspacing, step=yspacing)
    ypadbottom = np.round(-yspacing*ypadroot**np.arange(start=.5,
                                                        stop=3,
                                                        step=3./ypad))+ybottom
    ypadtop = np.round(yspacing*ypadroot**np.arange(start=.5,
                                                    stop=3,
                                                    step=3./ypad))+ytop
    ygridr = np.append(np.append(ypadbottom[::-1], midygrid), ypadtop)
    
    
    #make depth grid
    zgrid1 = z1layer*zpadroot**np.round(np.arange(0,zpadpow[0],
                                           zpadpow[0]/(nz-float(zpad))))
    zgrid2 = z1layer*zpadroot**np.round(np.arange(zpadpow[0],zpadpow[1],
                                         (zpadpow[1]-zpadpow[0])/(zpad)))
    
    zgrid = np.append(zgrid1, zgrid2)
    
    #--Need to make an array of the individual cell dimensions for the wsinv3d
    xnodes = xgridr.copy()    
    nx = xgridr.shape[0]
    xnodes[:nx/2] = np.array([abs(xgridr[ii]-xgridr[ii+1]) 
                            for ii in range(int(nx/2))])
    xnodes[nx/2:] = np.array([abs(xgridr[ii]-xgridr[ii+1]) 
                            for ii in range(int(nx/2)-1,nx-1)])

    ynodes = ygridr.copy()
    ny = ygridr.shape[0]
    ynodes[:ny/2] = np.array([abs(ygridr[ii]-ygridr[ii+1]) 
                            for ii in range(int(ny/2))])
    ynodes[ny/2:] = np.array([abs(ygridr[ii]-ygridr[ii+1]) 
                            for ii in range(int(ny/2)-1,ny-1)])
                            
    #--put the grids into coordinates relative to the center of the grid
    xgrid = xnodes.copy()
    xgrid[:int(nx/2)] = -np.array([xnodes[ii:int(nx/2)].sum() 
                                    for ii in range(int(nx/2))])
    xgrid[int(nx/2):] = np.array([xnodes[int(nx/2):ii+1].sum() 
                            for ii in range(int(nx/2),nx)])-xnodes[int(nx/2)]
                            
    ygrid = ynodes.copy()
    ygrid[:int(ny/2)] = -np.array([ynodes[ii:int(ny/2)].sum() 
                                    for ii in range(int(ny/2))])
    ygrid[int(ny/2):] = np.array([ynodes[int(ny/2):ii+1].sum() 
                            for ii in range(int(ny/2),ny)])-ynodes[int(ny/2)]
                            
                            
    #make sure that the stations are in the center of the cell as requested by
    #the code.
    for ii in range(ns):
        #look for the closest grid line
        xx = [nn for nn,xf in enumerate(xgrid) if xf>(slst[ii]['east']-xspacing) 
            and xf<(slst[ii]['east']+xspacing)]
        
        #shift the station to the center in the east-west direction
        if xgrid[xx[0]] < slst[ii]['east']:
            slst[ii]['east_c'] = xgrid[xx[0]]+xspacing/2
        elif xgrid[xx[0]] > slst[ii]['east']:
            slst[ii]['east_c'] = xgrid[xx[0]]-xspacing/2
        
        #look for closest grid line
        yy = [mm for mm,yf in enumerate(ygrid) 
              if yf >(slst[ii]['north']-yspacing) 
              and yf<(slst[ii]['north']+yspacing)]
        
        #shift station to center of cell in north-south direction
        if ygrid[yy[0]] < slst[ii]['north']:
            slst[ii]['north_c'] = ygrid[yy[0]]+yspacing/2
        elif ygrid[yy[0]] > slst[ii]['north']:
            slst[ii]['north_c'] = ygrid[yy[0]]-yspacing/2
            
        
    #=Plot the data if desired=========================
    if plotyn == 'y':
        fig = plt.figure(1,figsize=[6,6],dpi=300)
        plt.clf()
        
        #---plot map view    
        ax1 = fig.add_subplot(1,2,1,aspect='equal')
        
        #make sure the station is in the center of the cell
        ax1.scatter(slst['east_c'], slst['north_c'], marker='v')
                
        for xp in xgrid:
            ax1.plot([xp,xp],[ygrid.min(),ygrid.max()],color='k')
            
        for yp in ygrid:
            ax1.plot([xgrid.min(),xgrid.max()],[yp,yp],color='k')
        
        if plotxlimits == None:
            ax1.set_xlim(slst['east'].min()-10*xspacing,
                         slst['east'].max()+10*xspacing)
        else:
            ax1.set_xlim(plotxlimits)
        
        if plotylimits == None:
            ax1.set_ylim(slst['north'].min()-50*yspacing,
                         slst['north'].max()+50*yspacing)
        else:
            ax1.set_ylim(plotylimits)
            
        ax1.set_ylabel('Northing (m)',fontdict={'size':10,'weight':'bold'})
        ax1.set_xlabel('Easting (m)',fontdict={'size':10,'weight':'bold'})
        
        ##----plot depth view
        ax2 = fig.add_subplot(1,2,2,aspect='auto')
                
        for xp in xgrid:
            ax2.plot([xp,xp],[-zgrid.sum(),0],color='k')
            
        ax2.scatter(slst['east_c'], [0]*ns, marker='v')
            
        for zz,zp in enumerate(zgrid):
            ax2.plot([xgrid.min(),xgrid.max()],[-zgrid[0:zz].sum(),
                      -zgrid[0:zz].sum()],color='k')
        
        if plotzlimits == None:
            ax2.set_ylim(-zgrid1.max(),200)
        else:
            ax2.set_ylim(plotzlimits)
            
        if plotxlimits == None:
            ax2.set_xlim(slst['east'].min()-xspacing,
                         slst['east'].max()+xspacing)
        else:
            ax2.set_xlim(plotxlimits)
            
        ax2.set_ylabel('Depth (m)', fontdict={'size':10, 'weight':'bold'})
        ax2.set_xlabel('Easting (m)', fontdict={'size':10, 'weight':'bold'})  
        
        plt.show()
    

    
    
    print '-'*15
    print '   Number of stations = {0}'.format(len(slst))
    print '   Dimensions: '
    print '      e-w = {0}'.format(xgrid.shape[0])
    print '      n-s = {0}'.format(ygrid.shape[0])
    print '       z  = {0} (without 7 air layers)'.format(zgrid.shape[0])
    print '   Extensions: '
    print '      e-w = {0:.1f} (m)'.format(xnodes.__abs__().sum())
    print '      n-s = {0:.1f} (m)'.format(ynodes.__abs__().sum())
    print '      0-z = {0:.1f} (m)'.format(zgrid.__abs__().sum())
    print '-'*15
    
    loc = np.array([slst['east_c'], slst['north_c']])
    return ynodes, xnodes, zgrid, loc.T, slst            
    
    
def writeWSDataFile(periodlst, edilst, sites_fn=None, out_fn=None,
                    sitelocations=None, errorfloor=.05,
                    ptol=.15, zerrmap=[10,1,1,10], savepath=None, ncol=5,
                    units='mv'):
    """
    writes a data file for WSINV3D from winglink outputs
    
    Inputs:
    --------
        **periodlst** :list
                        periods to extract from edifiles, can get them from 
                        using the function getPeriods.
                        
        **edilst** : list
                    list of full paths to .edi files to use for inversion
                    
        **sitelocations**  : np.array (ns,2)
                            array of station locations where [:,0] corresponds
                            to the east-west location and [:,1] corresponds to
                            the north-south location.  This can be found from 
                            Make3DGrid.  Locations are in meters in grid
                            coordinates.
                            
        **sites_fn** : string
                     if you used Winglink to make the model then you need to
                     input the sites filename (full path)
                     
        **out_fn** : string
                    if you used Winglink to make the model need to input the
                    winglink .out file (full path)
                    
        **savepath** : string
                       directory or full path to save data file to, default 
                       path is dirname(sites_fn).  
                       saves as: savepath/WSDataFile.dat
                       *Need to input if you did not use Winglink*
                       
        **errorfloor** : float
                  minimum percent error to give to impedance tensor components in 
                  decimal form --> 10% = 0.10
                  *default* is .05
                  
        **ptol** : float
                   percent tolerance to locate frequencies in case edi files 
                   don't have the same frequencies.  Need to add interpolation.
                   *default* is 0.15
                   
        **zerrmap** :  tuple (zxx,zxy,zyx,zyy)
                       multiple to multiply err of zxx,zxy,zyx,zyy by.
                       Note the total error is zerr*zerrmap[ii]
                       
        **ncol** : int
                   number of columns in out_fn, sometimes it outputs different
                   number of columns.
        
    
    Returns:
    --------
        
        **data_fn** : full path to data file, saved in dirname(sites_fn) or 
                     savepath where savepath can be a directory or full 
                     filename
    """
    
    ns = len(edilst)
    
    #get units correctly????
    #what the heck is mv ??????????????
    if units == 'mv':
        zconv = 1./796.

    #create the output filename
    if savepath == None:
        ofile = os.path.join(os.path.dirname(sites_fn),'WSDataFile.dat')
    elif savepath.find('.') == -1:
        ofile = os.path.join(savepath,'WSDataFile.dat')
    else:
        ofile = savepath
    
    #if there is a site file from someone who naively used winglink
    if sites_fn != None:    
        #read in stations from sites file
        sitelst, slst = readSitesFile(sites_fn)

        
        #get x and y locations on a relative grid
        #CAREFUL: contains ALL coordinates for ALL stations in the file
        #maybe not all of them are used!!!
        coord_dict = getXY(sites_fn,out_fn,ncol=ncol)
    
    #if the user made a grid in python or some other fashion
    if sitelocations != None:
        if type(sitelocations[0]) is dict:
            xlst = np.zeros(ns)
            ylst = np.zeros(ns)
            slst = []
            for dd, sd in enumerate(sitelocations):
                xlst[dd] = sd['east_c']
                ylst[dd] = sd['north_c']
                slst.append(sd['station'])
        else:
            xlst = sitelocations[:, 0]
            ylst = sitelocations[:, 1]
            
    #define some lengths
    nperiod = len(periodlst)
    
    #make an array to put data into for easy writing
    zarr = np.zeros((ns, nperiod, 4), dtype='complex')
    zerror = np.zeros((ns, nperiod, 4), dtype='complex')

    #--------find frequencies and subsection of station coordinates-------------
    linelst = []
    counter = 0 
    x_coords = []
    y_coords = []
    for ss, edi in enumerate(edilst):
        if not os.path.isfile(edi):
            raise IOError('Could not find '+edi)
            
        
        z1 = mtedi.Edi()
        z1.readfile(edi)
        x_coords.append(coord_dict[z1.station][0])
        y_coords.append(coord_dict[z1.station][1])

        sdict = {}
        fspot = {}
        for ff, f1 in enumerate(periodlst):
            for kk,f2 in enumerate(1./z1.freq):
                if f2 >= (1-ptol)*f1 and f2 <= (1+ptol)*f1:
                    zderr = np.array([abs(z1.Z.zerr[kk, nn, mm])/
                                    abs(z1.Z.z[kk, nn, mm])*100 
                                    for nn in range(2) for mm in range(2)])

                    print '   Matched {0:.6g} to {1:.6g}'.format(f1, f2)
                    fspot['{0:.6g}'.format(f1)] = (kk, f2, zderr[0], zderr[1],
                                                  zderr[2], zderr[3])
                    zarr[ss, ff, :] = z1.Z.z[kk].reshape(4,)
                    zerror[ss, ff, :] = z1.Z.zerr[kk].reshape(4,)
                    for j in range(len(zerror[ss, ff, :])):
                        if errorfloor<zderr[j]:
                            continue
                        else:
                            zerror[ss, ff, j] = zarr[ss, ff, j] * errorfloor
                    break
        counter += 1        
        #print z1.station,counter, z1.station, len(fspot)
        sdict['fspot'] = fspot
        sdict['station'] = z1.station
        linelst.append(sdict)
    
    #-----Write data file-------------------------------------------------------
    
    ofid=file(ofile,'w')
    ofid.write('{0:d} {1:d} {2:d}\n'.format(ns,nperiod,8))
    
    #write N-S locations
    ofid.write('Station_Location: N-S \n')
    for ii in range(ns):
        ofid.write('{0:+.4e} '.format(y_coords[ii]))
        if (ii+1)%8==0:
            ofid.write('\n')
    if ns%8!=0:        
        ofid.write('\n')
    
    #write E-W locations
    ofid.write('Station_Location: E-W \n')
    for ii in range(ns):
        ofid.write('{0:+.4e} '.format(x_coords[ii]))
        if (ii+1)%8==0:
            ofid.write('\n')
    if ns%8!=0:        
        ofid.write('\n')

        
    #write impedance tensor components
    for ii, p1 in enumerate(periodlst):
        ofid.write('DATA_Period: {0:3.6f}\n'.format(p1))
        for ss in range(ns):
            zline=zarr[ss,ii,:]
            for jj in range(4):
                ofid.write('{0:+.4e} '.format(zline[jj].real*zconv))
                #use minus sign here, if i omega t convention is different
                #ofid.write('{0:+.4e} '.format(zline[jj].imag*zconv))
                ofid.write('{0:+.4e} '.format(-zline[jj].imag*zconv))

            ofid.write('\n')

    
    #write error as a percentage of Z
    for ii, p1 in enumerate(periodlst):
        ofid.write('ERROR_Period: {0:3.6f}\n'.format(p1))
        for ss in range(ns):
            zline=zerror[ss,ii,:]
            for jj in range(4):
                ofid.write('{0:+.4e} '.format(zline[jj].real*zerr*zconv))
                ofid.write('{0:+.4e} '.format(zline[jj].imag*zerr*zconv))
            ofid.write('\n')
            
    #write error maps
    for ii, p1 in enumerate(periodlst):
        ofid.write('ERMAP_Period: {0:3.6f}\n'.format(p1))
        for ss in range(ns):
            for jj in range(4):
                ofid.write('{0:.5e} '.format(zerrmap[jj]))
                ofid.write('{0:.5e} '.format(zerrmap[jj]))
            ofid.write('\n')
    ofid.close()
    print 'Wrote file to: '+ofile
    
    #write out places where errors are larger than error tolerance
    errfid = file(os.path.join(os.path.dirname(ofile),'DataErrorLocations.txt'),
                'w')
    errfid.write('Errors larger than error tolerance of: \n')
    errfid.write('Zxx={0} Zxy={1} Zyx={2} Zyy={3} \n'.format(zerrmap[0]*zerr,
                 zerrmap[1]*zerr,zerrmap[2]*zerr,zerrmap[3]*zerr))
    errfid.write('-'*20+'\n')
    errfid.write('station  T=period(s) Zij err=percentage \n')
    for pfdict in linelst:
        for kk, ff in enumerate(pfdict['fspot']):
            if pfdict['fspot'][ff][2]>zerr*100*zerrmap[0]:
                errfid.write(pfdict['station']+'  T='+ff+\
                        ' Zxx err={0:.3f} \n'.format(pfdict['fspot'][ff][2])) 
            if pfdict['fspot'][ff][3]>zerr*100*zerrmap[1]:
                errfid.write(pfdict['station']+'  T='+ff+\
                        ' Zxy err={0:.3f} \n'.format(pfdict['fspot'][ff][3])) 
            if pfdict['fspot'][ff][4]>zerr*100*zerrmap[2]:
                errfid.write(pfdict['station']+'  T='+ff+\
                        ' Zyx err={0:.3f} \n'.format(pfdict['fspot'][ff][4]))
            if pfdict['fspot'][ff][5]>zerr*100*zerrmap[3]:
                errfid.write(pfdict['station']+'  T='+ff+\
                        ' Zyy err={0:.3f} \n'.format(pfdict['fspot'][ff][5])) 
    errfid.close()
    print 'Wrote errors larger than tolerance to: '
    print os.path.join(os.path.dirname(ofile),'DataErrorLocations.txt')
                
    
    return ofile#, linelst


def writeInit3DFile_wl(out_fn, rhostart=100, ncol=5, savepath=None):
    """
    Makes an init3d file for WSINV3D
    
    Inputs:
        out_fn = full path to .out file from winglink
        rhostart = starting homogeneous half space in Ohm-m
        ncol = number of columns for data to be written in
        savepath = full path to save the init file
        
    Output:
        ifile = full path to init file
    """
    
    #create the output filename
    if savepath == None:
        ifile = os.path.join(os.path.dirname(out_fn), 'init3d')
    elif savepath.find('.') == -1:
        ifile = os.path.join(savepath, 'init3d')
    else:
        ifile = savepath
        
    dx, dy, dz=readWLOutFile(out_fn,ncol=ncol)
    
    nx = len(dx)
    ny = len(dy)
    nz = len(dz)
    
    init_modelFH = open(ifile,'w')
    init_modelFH.write('#Initial model \n')
    init_modelFH.write('{0} {1} {2} 1 \n'.format(ny, nx, nz))
        
    #write y locations
    y_list = []
    y_counter = 0 
    for yy in range(ny):
        y_list.append('{0: .3e}'.format(dy[yy]))
        y_counter += 1
        if y_counter == 8:
            y_list.append('\n')
            y_counter = 0
    if ny%8:
        y_list.append('\n')
    init_modelFH.write('  '.join(y_list))
    
    #write x locations
    x_list = []
    x_counter = 0 
    for xx in range(nx):
        x_list.append('{0: .3e}'.format(dx[xx]))
        x_counter += 1
        if x_counter == 8:
            x_list.append('\n')
            x_counter = 0
    if nx%8:		    
	x_list.append('\n')
    init_modelFH.write(''.join(x_list))

    #write z locations
    z_list = []
    z_counter = 0 
    for zz in range(nz):
        z_list.append('{0: .3e}'.format(dz[zz]))
        z_counter += 1
        if z_counter == 8:
            z_list.append('\n')
            z_counter = 0   
    if nz%8:
        z_list.append('\n')
    init_modelFH.write(''.join(z_list))
   

        
    init_modelFH.write('{0} \n'.format(rhostart))
    
    init_modelFH.close()
    
    print 'Wrote init file to: '+ ifile

    
    return ifile
    
    
def writeInit3DFile(xgrid, ygrid, zgrid, savepath, reslst=100,
                    title='Initial File for WSINV3D', resmodel=None):
                        
    """
    will write an initial file for wsinv3d.  At the moment can only make a 
    layered model that can then be manipulated later.  Input for a layered
    model is in layers which is [(layer1,layer2,resistivity index for reslst)]
    
    Note that x is assumed to be S --> N, y is assumed to be W --> E and
    z is positive downwards. 
    
    Also, the xgrid, ygrid and zgrid are assumed to be the relative distance
    between neighboring nodes.  This is needed because wsinv3d builds the 
    model from the bottom NW corner assuming the cell width from the init file.
    
    Therefore the first line or index=0 is the southern most row of cells, so
    if you build a model by hand the the layer block will look upside down if
    you were to picture it in map view. Confusing, perhaps, but that is the 
    way it is.  
    
    Argumens:
    ----------
    
        **xgrid** : np.array(nx)
                    block dimensions (m) in the N-S direction. **Note** that 
                    the code reads the grid assuming that index=0 is the 
                    southern most point.
        
        **ygrid** : np.array(ny)
                    block dimensions (m) in the E-W direction.  **Note** that
                    the code reads in the grid assuming that index=0 is the 
                    western most point.
                    
        **zgrid** : np.array(nz)
                    block dimensions (m) in the vertical direction.  This is
                    positive downwards.
                    
        **savepath** : string
                      Path to the director where the initial file will be saved
                      as savepath/init3d
                      
        **reslst** : float or list
                    The start resistivity as a float or a list of resistivities
                    that coorespond to the starting resistivity model 
                    **resmodel**.  This must be input if you input **resmodel**
                    
        **title** : string
                    Title that goes into the first line of savepath/init3d
                    
        **resmodel** : np.array((nx,ny,nz))
                        Starting resistivity model.  Each cell is allocated an
                        integer value that cooresponds to the index value of
                        **reslst**.  **Note** again that the modeling code 
                        assumes that the first row it reads in is the southern
                        most row and the first column it reads in is the 
                        western most column.  Similarly, the first plane it 
                        reads in is the Earth's surface.
                        
    Returns:
    --------
        
        **init_fn** : full path to initial file 
                        
                    
                      
    """
    if type(reslst) is not list and type(reslst) is not np.ndarray:
        reslst = [reslst]
     
    if os.path.isdir(savepath) == True:
        init_fn = os.path.join(savepath, "init3d")

    else:
        init_fn = os.path.join(savepath)
    
    ifid = file(init_fn, 'w')
    ifid.write('# {0}\n'.format(title.upper()))
    ifid.write('{0} {1} {2} {3}\n'.format(xgrid.shape[0], ygrid.shape[0],
                                          zgrid.shape[0], len(reslst)))

    #write S --> N node block
    for ii, xx in enumerate(xgrid):
        ifid.write('{0:>12}'.format('{:.1f}'.format(abs(xx))))
        if ii != 0 and np.remainder(ii+1, 5) == 0:
            ifid.write('\n')
        elif ii == xgrid.shape[0]-1:
            ifid.write('\n')
    
    #write W --> E node block        
    for jj, yy in enumerate(ygrid):
        ifid.write('{0:>12}'.format('{:.1f}'.format(abs(yy))))
        if jj != 0 and np.remainder(jj+1, 5) == 0:
            ifid.write('\n')
        elif jj == ygrid.shape[0]-1:
            ifid.write('\n')

    #write top --> bottom node block
    for kk, zz in enumerate(zgrid):
        ifid.write('{0:>12}'.format('{:.1f}'.format(abs(zz))))
        if kk != 0 and np.remainder(kk+1, 5) == 0:
            ifid.write('\n')
        elif kk == zgrid.shape[0]-1:
            ifid.write('\n')

    #write the resistivity list
    for ff in reslst:
        ifid.write('{0:.1f} '.format(ff))
    ifid.write('\n')
    
    if resmodel == None:
        ifid.close()
    else:
        #get similar layers
        l1 = 0
        layers = []
        for zz in range(zgrid.shape[0]-1):
            if (resmodel[:, :, zz] == resmodel[:, :, zz+1]).all() == False:
                layers.append((l1, zz))
                l1 = zz+1
        #need to add on the bottom layers
        layers.append((l1, zgrid.shape[0]-1))
        
        #write out the layers from resmodel
        for ll in layers:
            ifid.write('{0} {1}\n'.format(ll[0]+1, ll[1]+1))
            for xx in range(xgrid.shape[0]):
                for yy in range(ygrid.shape[0]):
                    ifid.write('{0:.0f} '.format(resmodel[xx, yy, ll[0]]))
                ifid.write('\n')
        ifid.close()
    
    print 'Wrote file to: {0}'.format(init_fn)
    return init_fn 

def readInit3D(init_fn):
    """
    read an initial file and return the pertinent information including grid
    positions in coordinates relative to the center point (0,0) and 
    starting model.

    Arguments:
    ----------
    
        **init_fn** : full path to initializing file.
        
    Returns:
    --------
        
        **xgrid** : np.array(nx)
                    array of nodes in S --> N direction
        
        **ygrid** : np.array(ny) 
                    array of nodes in the W --> E direction
                    
        **zgrid** : np.array(nz)
                    array of nodes in vertical direction positive downwards
        
        **resistivitivityModel** : dictionary
                    dictionary of the starting model with keys as layers
                    
        **reslst** : list
                    list of resistivity values in the model
        
        **titlestr** : string
                       title string
                       
    """

    ifid = file(init_fn,'r')    
    ilines = ifid.readlines()
    ifid.close()
    
    titlestr = ilines[0]

    #get size of dimensions, remembering that x is N-S, y is E-W, z is + down    
    nsize = ilines[1].strip().split()
    nx = int(nsize[0])
    ny = int(nsize[1])
    nz = int(nsize[2])

    #initialize empy arrays to put things into
    xnodes = np.zeros(nx)
    ynodes = np.zeros(ny)
    znodes = np.zeros(nz)
    resmodel = np.zeros((nx,ny,nz))
    
    #get the grid line locations
    nn = 2
    xx = 0
    while xx < nx:
        iline = ilines[nn].strip().split()
        for xg in iline:
            xnodes[xx] = float(xg)
            xx += 1
        nn += 1
    
    yy = 0
    while yy < ny:
        iline = ilines[nn].strip().split()
        for yg in iline:
            ynodes[yy] = float(yg)
            yy += 1
        nn += 1
    
    zz = 0
    while zz < nz:
        iline = ilines[nn].strip().split()
        for zg in iline:
            znodes[zz] = float(zg)
            zz += 1
        nn += 1
    
    #put the grids into coordinates relative to the center of the grid
    xgrid = xnodes.copy()
    xgrid[:int(nx/2)] = -np.array([xnodes[ii:int(nx/2)].sum() 
                                    for ii in range(int(nx/2))])
    xgrid[int(nx/2):] = np.array([xnodes[int(nx/2):ii+1].sum() 
                            for ii in range(int(nx/2),nx)])-xnodes[int(nx/2)]
                            
    ygrid = ynodes.copy()
    ygrid[:int(ny/2)] = -np.array([ynodes[ii:int(ny/2)].sum() 
                                    for ii in range(int(ny/2))])
    ygrid[int(ny/2):] = np.array([ynodes[int(ny/2):ii+1].sum() 
                            for ii in range(int(ny/2),ny)])-ynodes[int(ny/2)]
                            
    zgrid = np.array([znodes[:ii+1].sum() for ii in range(nz)])
    
    #get the resistivity values
    reslst = [float(rr) for rr in ilines[nn].strip().split()]
    nn += 1    
    
    #get model
    try:
        iline = ilines[nn].strip().split()
        
    except IndexError:
        resmodel[:, :, :] = reslst[0]
        return xgrid,ygrid,zgrid,reslst,titlestr,resmodel,xnodes,ynodes,znodes
        
    if len(iline) == 0 or len(iline) == 1:
        resmodel[:, :, :] = reslst[0]
        return xgrid,ygrid,zgrid,reslst,titlestr,resmodel,xnodes,ynodes,znodes
    else:
        while nn < len(ilines):
            
            iline = ilines[nn].strip().split()
            if len(iline) == 2:
                l1 = int(iline[0])-1
                l2 = int(iline[1])
                nn += 1
                xx = 0
            elif len(iline) == 0:
                break
            else:
                yy = 0
                while yy < ny:
                    resmodel[xx, yy, l1:l2] = int(iline[yy])
                    yy += 1
                xx += 1
                nn += 1
            
        return xgrid,ygrid,zgrid,reslst,titlestr,resmodel,xnodes,ynodes,znodes
        
        
def writeStartupFile(data_fn, initial_fn=None, output_fn=None, savepath=None,
                     apriori_fn=None, modells=[5,0.3,0.3,0.3], targetrms=1.0,
                     control=None, maxiter=10, errortol=None, static_fn=None,
                     lagrange=None):
    """
    makes a startup file for WSINV3D.  Most of these parameters are not input
    
    Inputs:
        data_fn = full path to the data file written for inversion
        initialfn = full path to init file
        output_fn = output stem to which the _model and _resp will be written
        savepath = full path to save the startup file to
        aprior_fn = full path to apriori model
        modells = smoothing parameters 
        targetrms = target rms
        control = something
        maxiter = maximum number of iterations
        errotol = error tolerance for the computer?
        static_fn = full path to static shift file name
        lagrange = starting lagrange multiplier
        
    Outputs:
        sfile = full path to startup file
        
    """
    
    #create the output filename
    if savepath == None:
        sfile = os.path.join(os.path.dirname(data_fn), 'startup')
    elif savepath.find('.') == -1:
        sfile = os.path.join(savepath, 'startup')
    else:
        sfile = savepath
    
    sfid = file(sfile,'w')
    
    sfid.write('DATA_FILE{0}../{1}\n'.format(' '*11, os.path.basename(data_fn)))
 
    if output_fn == None:
        sfid.write('OUTPUT_FILE{0}Iter_ \n'.format(' '*9))
    else:
        sfid.write('OUTPUT_FILE{0}{1}\n'.format(' '*9, output_fn))
        
    if initial_fn == None:
        sfid.write('INITIAL_MODEL_FILE{0}../init3d \n'.format(' '*2))
    else:
        sfid.write('INITIAL_MODEL_FILE{0}{1} \n'.format(' '*2, initial_fn))
        
    if apriori_fn == None:
        sfid.write('PRIOR_MODEL_FILE{0}default \n'.format(' '*4))
    else:
        sfid.write('PRIOR_MODEL_FILE'+' '*4+apriori_fn+' \n')
        sfid.write('PRIOR_MODEL_FILE{0}{1} \n'.format(' '*4, apriori_fn))
        
    if control==None:
        sfid.write('CONTROL_MODEL_INDEX default \n')
    else:
        sfid.write('CONTROL_MODEL_INDEX {0} \n'.format(control))
        
    sfid.write('TARGET_RMS{0}{1} \n'.format(' '*10, targetrms))
    
    sfid.write('MAX_NO_ITERATION{0}{1} \n'.format(' '*4, maxiter))

    sfid.write('MODEL_LENGTH_SCALE  {0} {1:.1f} {2:.1f} {3:.1f} \n'.format(
                                                                modells[0],
                                                                modells[1],
                                                                modells[2],
                                                                modells[3]))
        
    if lagrange==None:
        sfid.write('LAGRANGE_INFO{0}default \n'.format(' '*7))
    else:
         sfid.write('LAGRANGE_INFO{0}{1} \n'.format(' '*7, lagrange))
    

    if errortol==None:
        sfid.write('ERROR_TOL_LEVEL{0}default \n'.format(' '*5))
    else:
         sfid.write('ERROR_TOL_LEVEL{0}{1} \n'.format(' '*5, errortol))
         
    if static_fn==None:
        sfid.write('STATIC_FILE{0}default \n'.format(' '*9))
    else:
         sfid.write('STATIC_FILE{0}{1} \n'.format(' '*9, static_fn))

    sfid.close()
    
    print 'Wrote startup file to: {0}'.format(sfile)
    
    return sfile
    
def readDataFile(data_fn, sites_fn=None, units='mv'):
    """
    read in data file
    
    Inputs:
        data_fn = full path to data file
        sites_fn = full path to sites file output by winglink
        units = 'mv' always
        
    Outputs:
       period = list of periods used for the inversion
       zarr = array of impedance values 
               (number of staitons x number of periods x 2 x 2)
       zerr = array of errors in impedance component
       nsarr = station locations relative distance from center of grid in N-S
       ewarr = station locations relative distance from center of grid in E-W
       sitelst = list of sites used in data         
    """
    
    if units == 'mv':
        zconv = 796.
    else:
        zconv = 1
    
        
    dfid = file(data_fn,'r')
    dlines = dfid.readlines()

    #get size number of stations, number of frequencies, number of Z components    
    ns, nf, nz = np.array(dlines[0].strip().split(), dtype='int')
    nsstart = 2
    
    findlst = []
    for ii, dline in enumerate(dlines[1:50], 1):
        if dline.find('Station_Location: N-S') == 0:
            findlst.append(ii)
        elif dline.find('Station_Location: E-W') == 0:
            findlst.append(ii)
        elif dline.find('DATA_Period:') == 0:
            findlst.append(ii)
            
    ncol = len(dlines[nsstart].strip().split())
    
    #get site names if entered a sites file
    if sites_fn != None:
        slst, sitelst = readSitesFile(sites_fn)
    else:
        sitelst = np.arange(ns)

    #get N-S locations
    nsarr = np.zeros(ns)
    for ii, dline in enumerate(dlines[findlst[0]+1:findlst[1]],0):
        dline = dline.strip().split()
        for jj in range(ncol):
            try:
                nsarr[ii*ncol+jj] = float(dline[jj])
            except IndexError:
                pass
            except ValueError:
                break
            
    #get E-W locations
    ewarr = np.zeros(ns)
    for ii, dline in enumerate(dlines[findlst[1]+1:findlst[2]],0):
        dline = dline.strip().split()
        for jj in range(8):
            try:
                ewarr[ii*ncol+jj] = float(dline[jj])
            except IndexError:
                pass
            except ValueError:
                break
    #make some empty array to put stuff into
    period = np.zeros(nf)
    zarr = np.zeros((ns, nf, 2, 2), dtype=np.complex)
    zerr = np.zeros_like(zarr)
    zerrmap = np.zeros_like(zarr)

    #get data
    pcount = 0
    zcount = 0
    for ii, dl in enumerate(dlines[findlst[2]:findlst[2]+nf*(ns+1)]):
        if dl.find('DATA_Period')==0:
            period[pcount] = float(dl.strip().split()[1])
            kk = 0
            pcount += 1
            if ii == 0:
                pass
            else:
                zcount += 1
        else:
            zline = np.array(dl.strip().split(), dtype=np.float)*zconv
            zarr[kk, zcount, :, :] = np.array([[zline[0]-1j*zline[1],
                                                zline[2]-1j*zline[3]],
                                                [zline[4]-1j*zline[5],
                                                 zline[6]-1j*zline[7]]])
            kk += 1
    
    #if the data file is made from this program or is the input data file than
    #get the errors from that file
    if len(dlines) > 2*nf*ns:
        print 'Getting Error'
        pecount = 0
        zecount = 0
        for ii, dl in enumerate(dlines[findlst[2]+nf*(ns+1):findlst[2]+2*nf*(ns+1)]):
            if dl.find('ERROR_Period') == 0:
                kk = 0
                pecount += 1
                if ii == 0:
                    pass
                else:
                    zecount += 1
            else:
                zline = np.array(dl.strip().split(), dtype=np.float)*zconv
                zerr[kk, zecount, :, :] = np.array([[zline[0]-1j*zline[1],
                                                    zline[2]-1j*zline[3]],
                                                    [zline[4]-1j*zline[5],
                                                     zline[6]-1j*zline[7]]])
                kk += 1
                
    #get errormap values
    if len(dlines) > 3*nf*ns:
        print 'Getting Error Map'
        pmcount = 0
        zmcount = 0
        for ii,dl in enumerate(dlines[findlst[2]+2*nf*(ns+1):findlst[2]+3*nf*(ns+1)]):
            if dl.find('ERMAP_Period') == 0:
                kk = 0
                pmcount += 1
                if ii == 0:
                    pass
                else:
                    zmcount += 1
            else:
                #account for end of file empty lines
                if len(dl.split()) > 2:
                    zline = np.array(dl.strip().split(),dtype=np.float)
                    zerrmap[kk, zmcount, :, :]=np.array([[zline[0]-1j*zline[1],
                                                        zline[2]-1j*zline[3]],
                                                        [zline[4]-1j*zline[5],
                                                         zline[6]-1j*zline[7]]])
                    kk += 1
    
    #multiply errmap and error and convert from Ohm to mv/km nT
    zerr = zerr*zerrmap                                           

        
    return period, zarr, zerr, nsarr, ewarr, sitelst
    
def plotDataResPhase(data_fn, resp_fn=None, station_lst=None, sites_fn=None,
                     plottype='1', plotnum=1, dpi=150, units='mv', 
                     colormode='color'):
    """
    plot responses from the data file and if there is a response file
    
    Inputs:
        data_fn = fullpath to data file
        resp_fn = full path to respsonse file, if not input, just the data is
                 plotted. Can be a list of response files from the same 
                 inversion
        plottype= '1' to plot each station in a different window
                  [stations] for list of stations to plot (stations are numbers)
        plotnum = 1 for just xy,yx
                  2 for all components
    """

    
    #plot in color mode or black and white
    if colormode == 'color':
        #color for data
        cted = (0, 0, 1)
        ctmd = (1, 0, 0)
        mted = '*'
        mtmd = '*'
        
        #color for occam model
        ctem = (0, .3, 1.0)
        ctmm = (1, .3, 0)
        mtem = '+'
        mtmm = '+'
        
    elif colormode == 'bw':
        #color for data
        cted = (0, 0, 0)
        ctmd = (0, 0, 0)
        mted = '*'
        mtmd = 'v'
        
        #color for occam model
        ctem = (0.6, .6, .6)
        ctmm = (.6, .6, .6)
        mtem = '+'
        mtmm = 'x'
    
    
    #load the data file     
    period, dz, dzerr, north, east, slst = readDataFile(data_fn,
                                                        sites_fn=sites_fn,
                                                        units=units)
    #get shape of impedance tensors
    ns = dz.shape[0]
    nf = dz.shape[1]

    #read in response files
    if resp_fn!=None:
        rzlst=[]
        rzerrlst=[]
        if type(resp_fn) is not list:
            resp_fn=[resp_fn]
        for rfile in resp_fn:
            period, rz, rzerr, north, east, slst = readDataFile(rfile,
                                                            sites_fn=sites_fn,
                                                            units=units)
            rzlst.append(rz)
            rzerrlst.append(rzerr)
    else:
        rzlst = []
    #get number of response files
    nr = len(rzlst)
    
    if type(plottype) is list:
        ns = len(plottype)
      
    plt.rcParams['font.size'] = 10
    plt.rcParams['figure.subplot.left'] = .13
    plt.rcParams['figure.subplot.right'] = .98
    plt.rcParams['figure.subplot.bottom'] = .1
    plt.rcParams['figure.subplot.top'] = .92
    plt.rcParams['figure.subplot.wspace'] = .25
    plt.rcParams['figure.subplot.hspace'] = .05
    
    fontdict = {'size':12, 'weight':'bold'}    
    gs = gridspec.GridSpec(2, 2, height_ratios=[2, 1.5], hspace=.1)    
    
    
    if plottype != '1':
        pstationlst = []
        if type(plottype) is not list:
            plottype = [plottype]
        for ii, station in enumerate(slst):
            if type(station) is str:
                for pstation in plottype:
                    if station.find(str(pstation)) >= 0:
                        pstationlst.append(ii)
            else:
                for pstation in plottype:
                    if station == int(pstation):
                        pstationlst.append(ii)
    else:
        pstationlst = np.arange(ns)
    
    for jj in pstationlst:
        print 'Plotting: {0}'.format(slst[jj])
        
        #check for masked points
        dz[jj][np.where(dz[jj] == 7.95204E5-7.95204E5j)] = 0.0+0.0j
        dzerr[jj][np.where(dz[jj] == 7.95204E5-7.95204E5j)] = 1.0+1.0j
        
        #convert to apparent resistivity and phase
        z_object =  mtz.Z(z_array=dz[jj], zerr_array=dzerr[jj])
        z_object.freq = 1./period

        rp = mtplottools.ResPhase(z_object)
        
        #find locations where points have been masked
        nzxx = np.where(rp.resxx!=0)[0]
        nzxy = np.where(rp.resxy!=0)[0]
        nzyx = np.where(rp.resyx!=0)[0]
        nzyy = np.where(rp.resyy!=0)[0]
        
        if resp_fn != None:
            plotr = True
        else:
            plotr = False
        
        #make figure for xy,yx components
        if plotnum == 1: 
            fig = plt.figure(jj,[10,12],dpi=dpi)
            gs.update(hspace=.1,wspace=.15,left=.1)
        elif plotnum == 2:
            fig=plt.figure(jj,[12,12],dpi=dpi)
            gs.update(hspace=.1,wspace=.15,left=.07)
        
        #---------plot the apparent resistivity-----------------------------------
        if plotnum==1:
            ax=fig.add_subplot(gs[0,:])
            ax2=fig.add_subplot(gs[1,:],sharex=ax)
            ax.yaxis.set_label_coords(-.055, 0.5)
            ax2.yaxis.set_label_coords(-.055, 0.5)
        elif plotnum == 2:
            ax = fig.add_subplot(gs[0,0])
            ax2 = fig.add_subplot(gs[1,0],sharex=ax)
            ax3 = plt.subplot(gs[0,1], sharex=ax)
            ax4 = plt.subplot(gs[1,1], sharex=ax)
            
            ax3.yaxis.set_label_coords(-.1, 0.5)
            ax4.yaxis.set_label_coords(-.1, 0.5)
            ax.yaxis.set_label_coords(-.075, 0.5)
            ax2.yaxis.set_label_coords(-.075, 0.5)
        
        fig.suptitle(str(slst[jj]),fontdict={'size':15,'weight':'bold'})
        erxy=ax.errorbar(period[nzxy],
                         rp.resxy[nzxy],
                         marker=mted,ms=4,
                         mfc='None',
                         mec=cted,
                         mew=1,ls=':',
                         yerr=rp.resxy_err[nzxy], 
                         ecolor=cted, 
                         color=cted)
                         
        eryx=ax.errorbar(period[nzyx], 
                         rp.resyx[nzyx],
                         marker=mtmd,
                         ms=4,
                         mfc='None',
                         mec=ctmd,
                         mew=1,
                         ls=':',
                         yerr=rp.resyx_err[nzyx],
                         ecolor=ctmd,
                         color=ctmd)
        if plotr==True:
            for rr in range(nr):
                if colormode=='color':   
                    cxy=(0,.4+float(rr)/(3*nr),0)
                    cyx=(.7+float(rr)/(4*nr),.13,.63-float(rr)/(4*nr))
                elif colormode=='bw':
                    cxy=(1-1.25/(rr+2.),1-1.25/(rr+2.),1-1.25/(rr+2.))                    
                    cyx=(1-1.25/(rr+2.),1-1.25/(rr+2.),1-1.25/(rr+2.))
                
                resp_z_object =  mtz.Z(z_array=rzlst[rr][jj], 
                                       zerr_array=rzerrlst[rr][jj], 
                                       freq=1./period)

                rpr = mtplottools.ResPhase(resp_z_object)

                rms=np.sqrt(np.mean(
                                [(np.sqrt(abs(np.linalg.det(z_object.z[ll])))-
                                np.sqrt(abs(np.linalg.det(resp_z_object.z[ll]))))**2 
                                for ll in range(len(z_object.freq))]))
                print 'RMS = {:.2f}'.format(rms)
                erxyr=ax.errorbar(period[nzxy],
                                  rpr.resxy[nzxy],
                                  marker=mtem,
                                  ms=8,
                                  mfc='None',
                                  mec=cxy,
                                  mew=1,
                                  ls='--',
                                  yerr=rpr.resxy_err[nzxy],
                                  ecolor=cxy,
                                  color=cxy)
                                  
                eryxr=ax.errorbar(period[nzyx],
                                  rpr.resyx[nzyx],
                                  marker=mtmm,
                                  ms=8,
                                  mfc='None',
                                  mec=cyx,
                                  mew=1,
                                  ls='--',
                                  yerr=rpr.resyx_err[nzyx],
                                  ecolor=cyx,
                                  color=cyx)
                                  
                #plot response phase            
                ax2.errorbar(period[nzxy],
                             rpr.phasexy[nzxy],
                             marker=mtem,
                             ms=8,
                             mfc='None',
                             mec=cxy,
                             mew=1,
                             ls='--',
                             yerr=rp.phasexy_err[nzxy],
                             ecolor=cxy,
                             color=cxy)
                ax2.errorbar(period[nzyx],
                             np.array(rpr.phaseyx[nzyx]),
                             marker=mtmm,
                             ms=8,
                             mfc='None',
                             mec=cyx,
                             mew=1,
                             ls='--',
                             yerr=rp.phaseyx_err[nzyx],
                             ecolor=cyx,
                             color=cyx)
                             
                if plotnum == 2:
                    erxxr=ax3.errorbar(period[nzxx],
                                       rpr.resxx[nzxx],
                                       marker=mtem,
                                       ms=8,
                                       mfc='None',
                                       mec=cxy,
                                       mew=1,
                                       ls='--',
                                       yerr=rpr.resxx_err[nzxx],
                                       ecolor=cxy,
                                       color=cxy)
                    eryyr=ax3.errorbar(period[nzyy],
                                       rpr.resyy[nzyy],
                                       marker=mtmm,
                                       ms=8,
                                       mfc='None',
                                       mec=cyx,
                                       mew=1,
                                       ls='--',
                                       yerr=rpr.resyy_err[nzyy],
                                       ecolor=cyx,
                                       color=cyx)
                                       
                    #plot response phase
                    ax4.errorbar(period[nzxx],
                                 rpr.phasexx[nzxx],
                                 marker=mtem,
                                 ms=8,
                                 mfc='None',
                                 mec=cxy,
                                 mew=1,
                                 ls='--',
                                 yerr=rp.phasexx_err[nzxx],
                                 ecolor=cxy,
                                 color=cxy)
                                 
                    ax4.errorbar(period[nzyy],
                                 np.array(rpr.phaseyy[nzyy]),
                                 marker=mtmm,
                                 ms=8,
                                 mfc='None',
                                 mec=cyx,
                                 mew=1,
                                 ls='--',
                                 yerr=rp.phaseyy_err[nzyy], 
                                 ecolor=cyx,
                                 color=cyx)
                                  
        #ax.set_xlabel('Period (s)',fontdict=fontdict)
        plt.setp( ax.get_xticklabels(), visible=False)
        ax.set_ylabel('App. Res. ($\mathbf{\Omega \cdot m}$)',
                   fontdict=fontdict)
        ax.set_yscale('log')
        ax.set_xscale('log')
        ax.set_xlim(xmin=10**(np.floor(np.log10(period[0]))),
                 xmax=10**(np.ceil(np.log10(period[-1]))))
        ax.grid(True,alpha=.25)
        if plotr==True:
            ax.legend((erxy[0],eryx[0],erxyr[0],eryxr[0]),
                      ('Data $E_x/B_y$','Data $E_y/B_x$',
                      'Mod $E_x/B_y$','Mod $E_y/B_x$'),
                      loc=0,
                      markerscale=1,
                      borderaxespad=.01,
                      labelspacing=.07,
                      handletextpad=.2,
                      borderpad=.02)
        else:
            ax.legend((erxy[0],eryx[0]),
                      ('$E_x/B_y$','$E_y/B_x$'),
                      loc=0,
                      markerscale=1,
                      borderaxespad=.01,
                      labelspacing=.07,
                      handletextpad=.2,
                      borderpad=.02)
        
        #-----Plot the phase----------------------------------------------------
        
        ax2.errorbar(period[nzxy], 
                     rp.phasexy[nzxy],
                     marker=mted,
                     ms=4,
                     mfc='None',
                     mec=cted,
                     mew=1,
                     ls=':',
                     yerr=rp.phasexy_err[nzxy],
                     ecolor=cted,
                     color=cted)
                     
        ax2.errorbar(period[nzyx],
                     np.array(rp.phaseyx[nzyx]),
                     marker=mtmd,
                     ms=4,
                     mfc='None',
                     mec=ctmd,
                     mew=1,
                     ls=':',
                     yerr=rp.phaseyx_err[nzyx],
                     ecolor=ctmd,
                     color=ctmd)
                
        ax2.set_xlabel('Period (s)',fontdict)
        ax2.set_ylabel('Phase (deg)',fontdict)
        ax2.set_xscale('log')
        #check the phase to see if any point are outside of [0:90]    
        if min(rp.phasexy) < 0 or min(rp.phaseyx+180) < 0:
            pymin = min([min(rp.phasexy), min(rp.phaseyx)])
            if pymin > 0:
                pymin = 0
        else:
            pymin = 0
        
        if max(rp.phasexy) > 90 or max(rp.phaseyx) > 90:
            pymax=min([max(rp.phasexy), max(rp.phaseyx)])
            if pymax < 91:
                pymax = 90
        else:
            pymax = 90
        
        ax2.set_ylim(ymin=pymin, ymax=pymax)        
        ax2.yaxis.set_major_locator(MultipleLocator(30))
        ax2.yaxis.set_minor_locator(MultipleLocator(1))
        ax2.grid(True,alpha=.25)
        
        if plotnum == 2:
            #---------plot the apparent resistivity----------------------------
            erxx=ax3.errorbar(period[nzxx],
                              rp.resxx[nzxx],
                              marker=mted,
                              ms=4,
                              mfc='None',
                              mec=cted,
                              mew=1,
                              ls=':',
                              yerr=rp.resxx_err[nzxx],
                              ecolor=cted,
                              color=cted)
            eryy=ax3.errorbar(period[nzyy],
                              rp.resyy[nzyy],
                              marker=mtmd,
                              ms=4,
                              mfc='None',
                              mec=ctmd,
                              mew=1,
                              ls=':',
                              yerr=rp.resyy_err[nzyy],
                              ecolor=ctmd,
                              color=ctmd)

            ax3.set_yscale('log')
            ax3.set_xscale('log')
            plt.setp( ax3.get_xticklabels(), visible=False)
            ax3.set_xlim(xmin=10**(np.floor(np.log10(period[0]))),
                     xmax=10**(np.ceil(np.log10(period[-1]))))
            ax3.grid(True,alpha=.25)
            if plotr==True:
                ax3.legend((erxx[0],eryy[0],erxxr[0],eryyr[0]),
                          ('Data $E_x/B_x$','Data $E_y/B_y$',
                          'Mod $E_x/B_x$','Mod $E_y/B_y$'),
                          loc=0, markerscale=1,borderaxespad=.01,
                          labelspacing=.07,handletextpad=.2,borderpad=.02)
            else:
                ax3.legend((erxx[0],eryy[0]),('$E_x/B_x$','$E_y/B_y$'),loc=0,
                            markerscale=1,borderaxespad=.01,labelspacing=.07,
                            handletextpad=.2,borderpad=.02)
            
            #-----Plot the phase-----------------------------------------------
            ax4.errorbar(period[nzxx],
                         rp.phasexx[nzxx],
                         marker=mted,
                         ms=4,
                         mfc='None',
                         mec=cted,
                         mew=1,
                         ls=':',
                         yerr=rp.phasexx_err[nzxx],
                         ecolor=cted,
                         color=cted)
                         
            ax4.errorbar(period[nzyy],
                         np.array(rp.phaseyy[nzyy]),
                         marker=mtmd,
                         ms=4,
                         mfc='None',
                         mec=ctmd,
                         mew=1,
                         ls=':',
                         yerr=rp.phaseyy_err[nzyy],
                         ecolor=ctmd,
                         color=ctmd)
 
            ax4.set_xlabel('Period (s)',fontdict)
            ax4.set_xscale('log')
            ax4.set_ylim(ymin=-180,ymax=180)        
            ax4.yaxis.set_major_locator(MultipleLocator(30))
            ax4.yaxis.set_minor_locator(MultipleLocator(5))
            ax4.grid(True,alpha=.25)

def plotTensorMaps(data_fn,resp_fn=None,sites_fn=None,periodlst=None,
                   esize=(1,1,5,5),ecolor='phimin',
                   colormm=[(0,90),(0,1),(0,4),(-2,2)],
                   xpad=.500,units='mv',dpi=150):
    """
    plot phase tensor maps for data and or response, each figure is of a
    different period.  If response is input a third column is added which is 
    the residual phase tensor showing where the model is not fitting the data 
    well.  The data is plotted in km in units of ohm-m.
    
    Inputs:
        data_fn = full path to data file
        resp_fn = full path to response file, if none just plots data
        sites_fn = full path to sites file
        periodlst = indicies of periods you want to plot
        esize = size of ellipses as:
                0 = phase tensor ellipse
                1 = phase tensor residual
                2 = resistivity tensor ellipse
                3 = resistivity tensor residual
        ecolor = 'phimin' for coloring with phimin or 'beta' for beta coloring
        colormm = list of min and max coloring for plot, list as follows:
                0 = phase tensor min and max for ecolor in degrees
                1 = phase tensor residual min and max [0,1]
                2 = resistivity tensor coloring as resistivity on log scale
                3 = resistivity tensor residual coloring as resistivity on 
                    linear scale
        xpad = padding of map from stations at extremities (km)
        units = 'mv' to convert to Ohm-m 
        dpi = dots per inch of figure
    """
    
    period,zd,zderr,nsarr,ewarr,sitelst=readDataFile(data_fn,sites_fn=sites_fn,
                                                      units=units)
    
    if resp_fn!=None:
        period,zr,zrerr,nsarr,ewarr,sitelst=readDataFile(resp_fn,sites_fn=sites_fn,
                                                         units=units)
    
    if periodlst==None:
        periodlst=range(len(period))
        
    #put locations into an logical coordinate system in km
    nsarr=-nsarr/1000
    ewarr=-ewarr/1000

    #get coloring min's and max's    
    if colormm!=None:
        ptmin,ptmax=(colormm[0][0]*np.pi/180,colormm[0][1]*np.pi/180)
        ptrmin,ptrmax=colormm[1]
        rtmin,rtmax=colormm[2]
        rtrmin,rtrmax=colormm[3]
    else:
        pass
    
    #get ellipse sizes
    ptsize=esize[0]
    ptrsize=esize[1]
    rtsize=esize[2]
    rtrsize=esize[3]
        
    plt.rcParams['font.size']=10
    plt.rcParams['figure.subplot.left']=.03
    plt.rcParams['figure.subplot.right']=.98
    plt.rcParams['figure.subplot.bottom']=.1
    plt.rcParams['figure.subplot.top']=.90
    plt.rcParams['figure.subplot.wspace']=.005
    plt.rcParams['figure.subplot.hspace']=.005
    
    ns=zd.shape[0]
    
    for ff,per in enumerate(periodlst):
        print 'Plotting Period: {0:.5g}'.format(period[per])
        fig=plt.figure(per+1,dpi=dpi)

        #get phase tensor
        pt=Z.PhaseTensor(zd[:,per])

        #get resistivity tensor
        rt=Z.ResistivityTensor(zd[:,per],np.repeat(1./period[per],ns))
        
        if resp_fn!=None:
            #get phase tensor and residual phase tensor
            ptr=Z.PhaseTensor(zr[:,per])
            ptd=Z.PhaseTensorResidual(zd[:,per],zr[:,per])
            
            #get resistivity tensor and residual
            rtr=Z.ResistivityTensor(zr[:,per],np.repeat(1./period[per],ns))
            rtd=Z.ResistivityTensorResidual(zd[:,per],zr[:,per],
                                            np.repeat(1./period[per],ns))
            
            if colormm==None:
                if ecolor=='phimin':
                    ptmin,ptmax=(ptr.phimin.min()/(np.pi/2),
                                 ptr.phimin.max()/(np.pi/2))
                elif ecolor=='beta':
                    ptmin,ptmax=(ptr.beta.min(),ptr.beta.max())
                    
                ptrmin,ptrmax=(ptd.ecolor.min(),ptd.ecolor.max())
                rtmin,rtmax=(np.log10(rtr.rhodet.min()),
                             np.log10(rtr.rhodet.max()))
                rtrmin,rtrmax=rtd.rhodet.min(),rtd.rhodet.max()
            #make subplots            
            ax1=fig.add_subplot(2,3,1,aspect='equal')
            ax2=fig.add_subplot(2,3,2,aspect='equal')
            ax3=fig.add_subplot(2,3,3,aspect='equal')
            ax4=fig.add_subplot(2,3,4,aspect='equal')
            ax5=fig.add_subplot(2,3,5,aspect='equal')
            ax6=fig.add_subplot(2,3,6,aspect='equal')
            
            for jj in range(ns):
                #-----------plot data phase tensors---------------
                eheightd=pt.phimin[jj]/ptr.phimax.max()*ptsize
                ewidthd=pt.phimax[jj]/ptr.phimax.max()*ptsize
            
                ellipd=Ellipse((ewarr[jj],nsarr[jj]),width=ewidthd,
                               height=eheightd,angle=pt.azimuth[jj])
                #color ellipse:
                if ecolor=='phimin':
                    cvar=(pt.phimin[jj]/(np.pi/2)-ptmin)/(ptmax-ptmin)
                    if abs(cvar)>1:
                        ellipd.set_facecolor((1,0,.1))
                    else:
                        ellipd.set_facecolor((1,1-abs(cvar),.1))
                if ecolor=='beta':
                    cvar=(abs(pt.beta[jj])-ptmin)/(ptmax-ptmin)
                    if abs(cvar)>1:
                        ellipd.set_facecolor((1,1,.1))
                    else:
                        ellipd.set_facecolor((1-cvars,1-cvars,1))
                
                ax1.add_artist(ellipd)
                
                #----------plot response phase tensors---------------------
                eheightr=ptr.phimin[jj]/ptr.phimax.max()*ptsize
                ewidthr=ptr.phimax[jj]/ptr.phimax.max()*ptsize
            
                ellipr=Ellipse((ewarr[jj],nsarr[jj]),width=ewidthr,
                               height=eheightr,angle=ptr.azimuth[jj])
                #color ellipse:
                if ecolor=='phimin':
                    cvar=(ptr.phimin[jj]/(np.pi/2)-ptmin)/(ptmax-ptmin)
                    if abs(cvar)>1:
                        ellipr.set_facecolor((1,0,.1))
                    else:
                        ellipr.set_facecolor((1,1-abs(cvar),.1))
                if ecolor=='beta':
                    cvar=(abs(ptr.beta[jj])-ptmin)/(ptmax-ptmin)
                    if abs(cvar)>1:
                        ellipr.set_facecolor((1,1,.1))
                    else:
                        ellipr.set_facecolor((1-cvars,1-cvars,1))
                ax2.add_artist(ellipr)
                
                #--------plot residual phase tensors-------------
                eheight=ptd.phimin[jj]/ptd.phimax.max()*ptrsize
                ewidth=ptd.phimax[jj]/ptd.phimax.max()*ptrsize
            
                ellip=Ellipse((ewarr[jj],nsarr[jj]),width=ewidth,
                               height=eheight,angle=ptd.azimuth[jj]-90)
                #color ellipse:
                cvar=(ptd.ecolor[jj]-ptrmin)/(ptrmax-ptrmin)
                if abs(cvar)>1:
                    ellip.set_facecolor((0,0,0))
                else:
                    ellip.set_facecolor((abs(cvar),.5,.5))
                
                ax3.add_artist(ellip)
                
                #-----------plot data resistivity tensors---------------
                rheightd=rt.rhomin[jj]/rtr.rhomax.max()*rtsize
                rwidthd=rt.rhomax[jj]/rtr.rhomax.max()*rtsize
            
                rellipd=Ellipse((ewarr[jj],nsarr[jj]),width=rwidthd,
                               height=rheightd,angle=rt.rhoazimuth[jj])
                #color ellipse:
                cvar=(np.log10(rt.rhodet[jj])-rtmin)/(rtmax-rtmin)
                if cvar>.5:
                    if cvar>1:
                        rellipd.set_facecolor((0,0,1))
                    else:
                        rellipd.set_facecolor((1-abs(cvar),1-abs(cvar),1))
                else:
                    if cvar<-1:
                        rellipd.set_facecolor((1,0,0))
                    else:
                        rellipd.set_facecolor((1,1-abs(cvar),1-abs(cvar)))
                
                ax4.add_artist(rellipd)
                
                #----------plot response resistivity tensors---------------------
                rheightr=rtr.rhomin[jj]/rtr.rhomax.max()*rtsize
                rwidthr=rtr.rhomax[jj]/rtr.rhomax.max()*rtsize
            
                rellipr=Ellipse((ewarr[jj],nsarr[jj]),width=rwidthr,
                               height=rheightr,angle=rtr.rhoazimuth[jj])

                #color ellipse:
                cvar=(np.log10(rtr.rhodet[jj])-rtmin)/(rtmax-rtmin)
                if cvar>.5:
                    if cvar>1:
                        rellipr.set_facecolor((0,0,1))
                    else:
                        rellipr.set_facecolor((1-abs(cvar),1-abs(cvar),1))
                else:
                    if cvar<-1:
                        rellipr.set_facecolor((1,0,0))
                    else:
                        rellipr.set_facecolor((1,1-abs(cvar),1-abs(cvar)))
                
                ax5.add_artist(rellipr)
                
                #--------plot residual resistivity tensors-------------
                rheight=rtd.rhomin[jj]/rtd.rhomax.max()*rtrsize
                rwidth=rtd.rhomax[jj]/rtd.rhomax.max()*rtrsize
            
                rellip=Ellipse((ewarr[jj],nsarr[jj]),width=rwidth,
                               height=rheight,angle=rtd.azimuth[jj]-90)
                #color ellipse:
                cvar=(rtd.rhodet[jj]-rtrmin)/(rtrmax-rtrmin)
                if cvar<0:
                    if cvar<-1:
                        rellip.set_facecolor((0,0,1))
                    else:
                        rellip.set_facecolor((1-abs(cvar),1-abs(cvar),1))
                else:
                    if cvar>1:
                        rellip.set_facecolor((1,0,0))
                    else:
                        rellip.set_facecolor((1,1-abs(cvar),1-abs(cvar)))
                    
                ax6.add_artist(rellip)
                
            for aa,ax in enumerate([ax1,ax2,ax3,ax4,ax5,ax6]):
                ax.set_xlim(ewarr.min()-xpad,ewarr.max()+xpad)
                ax.set_ylim(nsarr.min()-xpad,nsarr.max()+xpad)
                ax.grid('on')
                if aa<3:
                    plt.setp(ax.get_xticklabels(),visible=False)
                if aa==0 or aa==3:
                    pass
                else:
                    plt.setp(ax.get_yticklabels(),visible=False)
                
                cbax=mcb.make_axes(ax,shrink=.9,pad=.05,orientation='vertical')
                if aa==0 or aa==1:
                    cbx=mcb.ColorbarBase(cbax[0],cmap=ptcmap,
                                     norm=Normalize(vmin=ptmin*180/np.pi,
                                                    vmax=ptmax*180/np.pi),
                                     orientation='vertical',format='%.2g')
                    
                    cbx.set_label('Phase (deg)',
                                  fontdict={'size':7,'weight':'bold'})
                if aa==2:
                    cbx=mcb.ColorbarBase(cbax[0],cmap=ptcmap2,
                                     norm=Normalize(vmin=ptrmin,
                                                    vmax=ptrmax),
                                     orientation='vertical',format='%.2g')
                    
                    cbx.set_label('$\Delta_{\Phi}$',
                                  fontdict={'size':7,'weight':'bold'})
                if aa==3 or aa==4:
                    cbx=mcb.ColorbarBase(cbax[0],cmap=rtcmapr,
                                     norm=Normalize(vmin=10**rtmin,
                                                    vmax=10**rtmax),
                                     orientation='vertical',format='%.2g')
                    
                    cbx.set_label('App. Res. ($\Omega \cdot$m)',
                                  fontdict={'size':7,'weight':'bold'})
                if aa==5:
                    cbx=mcb.ColorbarBase(cbax[0],cmap=rtcmap,
                                     norm=Normalize(vmin=rtrmin,
                                                    vmax=rtrmax),
                                     orientation='vertical',format='%.2g')
                    
                    cbx.set_label('$\Delta_{rho}$',
                                  fontdict={'size':7,'weight':'bold'})
                 
            plt.show()
        
        #----Plot Just the data------------------        
        else:
            if colormm==None:
                if ecolor=='phimin':
                    ptmin,ptmax=(pt.phimin.min()/(np.pi/2),
                                 pt.phimin.max()/(np.pi/2))
                elif ecolor=='beta':
                    ptmin,ptmax=(pt.beta.min(),pt.beta.max())
                    
                rtmin,rtmax=(np.log10(rt.rhodet.min()),
                             np.log10(rt.rhodet.max()))
            ax1=fig.add_subplot(1,2,1,aspect='equal')
            ax2=fig.add_subplot(1,2,2,aspect='equal')
            for jj in range(ns):
                #-----------plot data phase tensors---------------
                #check for nan in the array cause it messes with the max                
                pt.phimax=np.nan_to_num(pt.phimax)
                
                #scale the ellipse
                eheightd=pt.phimin[jj]/pt.phimax.max()*ptsize
                ewidthd=pt.phimax[jj]/pt.phimax.max()*ptsize
            
                #make the ellipse
                ellipd=Ellipse((ewarr[jj],nsarr[jj]),width=ewidthd,
                               height=eheightd,angle=pt.azimuth[jj])
                #color ellipse:
                if ecolor=='phimin':
                    cvar=(pt.phimin[jj]/(np.pi/2)-ptmin)/(ptmax-ptmin)
                    if abs(cvar)>1:
                        ellipd.set_facecolor((1,0,.1))
                    else:
                        ellipd.set_facecolor((1,1-abs(cvar),.1))
                if ecolor=='beta':
                    cvar=(abs(pt.beta[jj])-ptmin)/(ptmax-ptmin)
                    if abs(cvar)>1:
                        ellipd.set_facecolor((1,1,.1))
                    else:
                        ellipd.set_facecolor((1-cvars,1-cvars,1))
                
                ax1.add_artist(ellipd)
                
                #-----------plot data resistivity tensors---------------
                rt.rhomax=np.nan_to_num(rt.rhomax)
                rheightd=rt.rhomin[jj]/rt.rhomax.max()*rtsize
                rwidthd=rt.rhomax[jj]/rt.rhomax.max()*rtsize
            
                rellipd=Ellipse((ewarr[jj],nsarr[jj]),width=rwidthd,
                               height=rheightd,angle=rt.rhoazimuth[jj])
                #color ellipse:
                cvar=(np.log10(rt.rhodet[jj])-rtmin)/(rtmax-rtmin)
                if cvar>.5:
                    if cvar>1:
                        rellipd.set_facecolor((0,0,1))
                    else:
                        rellipd.set_facecolor((1-abs(cvar),1-abs(cvar),1))
                else:
                    if cvar<-1:
                        rellipd.set_facecolor((1,0,0))
                    else:
                        rellipd.set_facecolor((1,1-abs(cvar),1-abs(cvar)))
                
                ax2.add_artist(rellipd)
                
            for aa,ax in enumerate([ax1,ax2]):
                ax.set_xlim(ewarr.min()-xpad,ewarr.max()+xpad)
                ax.set_ylim(nsarr.min()-xpad,nsarr.max()+xpad)
                ax.grid('on')
                ax.set_xlabel('easting (km)',fontdict={'size':10,
                              'weight':'bold'})

                if aa==1:
                    plt.setp(ax.get_yticklabels(),visible=False)
                else:
                    ax.set_ylabel('northing (km)',fontdict={'size':10,
                              'weight':'bold'})
#                cbax=mcb.make_axes(ax,shrink=.8,pad=.15,orientation='horizontal',
#                               anchor=(.5,1))
                #l,b,w,h
#                cbax=fig.add_axes([.1,.95,.35,.05])
                if aa==0:
                    cbax=fig.add_axes([.12,.97,.31,.02])
                    cbx=mcb.ColorbarBase(cbax,cmap=ptcmap,
                                     norm=Normalize(vmin=ptmin*180/np.pi,
                                                    vmax=ptmax*180/np.pi),
                                     orientation='horizontal',format='%.2g')
                    
                    cbx.set_label('Phase (deg)',
                                  fontdict={'size':7,'weight':'bold'})
                if aa==1:
                    cbax=fig.add_axes([.59,.97,.31,.02])
                    cbx=mcb.ColorbarBase(cbax,cmap=rtcmapr,
                                     norm=Normalize(vmin=10**rtmin,
                                                    vmax=10**rtmax),
                                     orientation='horizontal',format='%.2g')
                    
                    cbx.set_label('App. Res. ($\Omega \cdot$m)',
                                  fontdict={'size':7,'weight':'bold'})
                    cbx.set_ticks((10**rtmin,10**rtmax))
            plt.show()
            

def readModelFile(mfile,ncol=7):
    """
    read in a model file as x-north, y-east, z-positive down
    """            
    
    mfid=file(mfile,'r')
    mlines=mfid.readlines()

    #get info at the beggining of file
    info=mlines[0].strip().split()
    infodict=dict([(info[0][1:],info[1]),(info[2],info[3]),(info[4],info[5])])
    
    #get lengths of things
    nx,ny,nz,nn=np.array(mlines[1].strip().split(),dtype=np.int)
    
    #make empty arrays to put stuff into
    xarr=np.zeros(nx)
    yarr=np.zeros(ny)
    zarr=np.zeros(nz)
    resarr=np.zeros((nx,ny,nz))
    
    mm=0
    nn=2
    while mm<nx:
        xline=mlines[nn].strip().split()
        for xx in xline:
            xarr[mm]=float(xx)
            mm+=1
        nn+=1
        
    mm=0
    while mm<ny:
        yline=mlines[nn].strip().split()
        for yy in yline:
            yarr[mm]=float(yy)
            mm+=1
        nn+=1
    
    mm=0
    while mm<nz:
        zline=mlines[nn].strip().split()
        for zz in zline:
            zarr[mm]=float(zz)
            mm+=1
        nn+=1
        
    #put the grids into coordinates relative to the center of the grid
    nsarr=xarr.copy()
    nsarr[:int(nx/2)]=-np.array([xarr[ii:int(nx/2)].sum() 
                                    for ii in range(int(nx/2))])
    nsarr[int(nx/2):]=np.array([xarr[int(nx/2):ii+1].sum() 
                            for ii in range(int(nx/2),nx)])-xarr[int(nx/2)]
                            
    ewarr=yarr.copy()
    ewarr[:int(ny/2)]=-np.array([yarr[ii:int(ny/2)].sum() 
                                    for ii in range(int(ny/2))])
    ewarr[int(ny/2):]=np.array([yarr[int(ny/2):ii+1].sum() 
                            for ii in range(int(ny/2),ny)])-yarr[int(ny/2)]
                            
    zdepth=np.array([zarr[0:ii+1].sum()-zarr[0] for ii in range(nz)])

    mm=0
    for kk in range(nz):
        for jj in range(ny):
            for ii in range(nx):
                resarr[(nx-1)-ii,jj,kk]=float(mlines[nn+mm].strip())
                mm+=1
    
    return nsarr,ewarr,zdepth,resarr,infodict, xarr, yarr, zarr
 

def plotDepthSlice(data_fn,model_fn,savepath=None,map_scale='km',ew_limits=None,
                   ns_limits=None,depth_index=None,fig_dimensions=[4,4],
                   dpi=300,font_size=7,climits=(0,4),cmap='jet_r',
                   plot_grid='n',cb_dict={}): 
                       
    """
    plot depth slices
    """
    
    #create a path to save figure to if it doesn't already exist
    if savepath!=None:
        if not os.path.exists(savepath):
            os.mkdir(savepath)
        
    #make map scale
    if map_scale=='km':
        dscale=1000.
    elif map_scale=='m':
        dscale=1.
    
    #read in data file to station locations
    period,zz,zzerr,ns,ew,slst=readDataFile(data_fn)
    
    #scale the station locations to the desired units
    ns/=dscale
    ew/=dscale
    
    #read in model file    
    x, y, z, resarr, idict, xg, yg, zg = readModelFile(model_fn)
    
    #scale the model grid to desired units
    x /= dscale
    y /= dscale
    z /= dscale

     
    #create an list of depth slices to plot
    if depth_index == None:
        zrange = range(z.shape[0])
    elif type(depth_index) is int:
        zrange = [depth_index]
    elif type(depth_index) is list:
        zrange = depth_index
    
    #set the limits of the plot
    if ew_limits == None:
        xlimits = (np.floor(ew.min()), np.ceil(ew.max()))
    else:
        xlimits = ew_limits
        
    if ns_limits == None:
        ylimits = (np.floor(ns.min()),np.ceil(ns.max()))
    else:
        ylimits = ns_limits
        
        
    #make a mesh grid of north and east
    north1, east1 = np.meshgrid(x,y)
    
    fdict = {'size':font_size+2, 'weight':'bold'}
    
    cblabeldict={-2:'$10^{-3}$',-1:'$10^{-1}$',0:'$10^{0}$',1:'$10^{1}$',
                 2:'$10^{2}$',3:'$10^{3}$',4:'$10^{4}$',5:'$10^{5}$',
                 6:'$10^{6}$',7:'$10^{7}$',8:'$10^{8}$'}
    
    
    plt.rcParams['font.size'] = font_size
    for ii in zrange: 
        fig = plt.figure(ii,figsize=fig_dimensions,dpi=dpi)
        plt.clf()
        ax1 = fig.add_subplot(1, 1, 1, aspect='equal')
        ax1.pcolormesh(east1, north1,
                       np.log10(np.rot90(resarr[:,:,ii],3)),
                       cmap=cmap,
                       vmin=climits[0],
                       vmax=climits[1])
                       
        #plot the stations
        for ee, nn in zip(ew,ns):
            ax1.text(ee, nn,'*', verticalalignment='center',
                     horizontalalignment='center',
                     fontdict={'size':5, 'weight':'bold'})

        #set axis properties
        ax1.set_xlim(xlimits)
        ax1.set_ylim(ylimits)
        ax1.xaxis.set_minor_locator(MultipleLocator(100*1./dscale))
        ax1.yaxis.set_minor_locator(MultipleLocator(100*1./dscale))
        ax1.set_ylabel('Northing ('+map_scale+')',fontdict=fdict)
        ax1.set_xlabel('Easting ('+map_scale+')',fontdict=fdict)
        ax1.set_title('Depth = {:.3f} '.format(z[ii])+'('+map_scale+')',
                      fontdict=fdict)
        
        #plot the grid if desired              
        if plot_grid == 'y':
            for xx in x:
                ax1.plot([y.min(),y.max()],[xx,xx], lw=.1, color='k')
            for yy in y:
                ax1.plot([yy,yy],[x.min(),x.max()], lw=.1, color='k')
        
        #plot the colorbar
        try:
            cb_dict['orientation']
        except KeyError:
            cb_dict['orientation']='horizontal'
        
        if cb_dict['orientation']=='horizontal':
            try:
                ax2 = fig.add_axes(cb_dict['position'])
            except KeyError:
                ax2 = fig.add_axes((ax1.axes.figbox.bounds[3]-.225,
                                    ax1.axes.figbox.bounds[1]+.05,.3,.025))
                                    
        elif cb_dict['orientation']=='vertical':
            try:
                ax2 = fig.add_axes(cb_dict['position'])
            except KeyError:
                ax2 = fig.add_axes((ax1.axes.figbox.bounds[2]-.15,
                                    ax1.axes.figbox.bounds[3]-.21,.025,.3))
        
        cb=mcb.ColorbarBase(ax2,cmap=cmap,
                        norm=Normalize(vmin=climits[0],vmax=climits[1]),
                        orientation=cb_dict['orientation'])
                            
        if cb_dict['orientation']=='horizontal':
            cb.ax.xaxis.set_label_position('top')
            cb.ax.xaxis.set_label_coords(.5,1.3)
            
            
        elif cb_dict['orientation']=='vertical':
            cb.ax.yaxis.set_label_position('right')
            cb.ax.yaxis.set_label_coords(1.25,.5)
            cb.ax.yaxis.tick_left()
            cb.ax.tick_params(axis='y',direction='in')
                            
        cb.set_label('Resistivity ($\Omega \cdot$m)',
                     fontdict={'size':font_size})
        cb.set_ticks(np.arange(climits[0],climits[1]+1))
        cb.set_ticklabels([cblabeldict[cc] 
                            for cc in np.arange(climits[0],climits[1]+1)])

        if savepath!=None:
            
            fig.savefig(os.path.join(savepath,
                        "Depth_{}_{:.4f}.png".format(ii,z[ii])),
                        dpi=dpi)
            fig.clear()
            plt.close()

        else:
            pass

           
        
def computeMemoryUsage(nx, ny, nz, n_stations, n_zelements, n_period):
    """
    compute the memory usage of a model
    
    Arguments:
    ----------
        **nx** : int
                 number of cells in N-S direction
                 
        **ny** : int
                 number of cells in E-W direction
                 
        **nz** : int
                 number of cells in vertical direction including air layers (7)
                 
        **n_stations** : int
                         number of stations
                         
        **n_zelements** : int
                          number of impedence tensor elements either 4 or 8
        
        **n_period** : int
                       number of periods to invert for
                       
    Returns:
    --------
        **mem_req** : float
                      approximate memory useage in GB
    """

    mem_req = 1.2*(8*(n_stations*n_period*n_zelements)**2+
                   8*(nx*ny*nz*n_stations*n_period*n_zelements))
    return mem_req*1E-9
                        
class WS3DModelManipulator(object):
    """
    will plot a model from wsinv3d or init file so the user can manipulate the 
    resistivity values relatively easily.  At the moment only plotted
    in map view.
    
    
    """

    def __init__(self, model_fn=None, init_fn=None, data_fn=None,
                 res_lst=None, mapscale='km', plot_yn='y', xlimits=None, 
                 ylimits=None, cbdict={}):
        
        self.model_fn = model_fn
        self.init_fn = init_fn
        self.data_fn = data_fn
        
        #station locations in relative coordinates read from data file
        self.station_x = None
        self.station_y = None
        
        #--> set map scale
        self.mapscale = mapscale
        
        self.m_width = 100
        self.m_height = 100
        
        #--> scale the map coordinates
        if self.mapscale=='km':
            self.dscale = 1000.
        if self.mapscale=='m':
            self.dscale = 1.
        
        #make a default resistivity list to change values
        if res_lst is None:
            self.res_lst = np.array([.3, 1, 10, 50, 100, 500, 1000, 5000],
                                   dtype=np.float)
        
        else:
            self.res_lst = res_lst        
        
        self.read_file()
   
        #make a dictionary of values to write to file.
        self.res_dict = dict([(res, ii) 
                              for ii,res in enumerate(self.res_lst,1)])
        

        self.res_value = self.res_lst[0]
        
        #--> set map limits
        self.xlimits = xlimits
        self.ylimits = ylimits
        
        self.cb_dict = cbdict

        self.font_size = 7
        self.dpi = 300
        self.fignum = 1
        self.figsize = [6,6]
        self.cmap = cm.jet_r
        self.depth_index = 0

        
        self.fdict = {'size':self.font_size+2, 'weight':'bold'}
    
        self.cblabeldict = {-5:'$10^{-5}$',
                            -4:'$10^{-4}$',
                           -3:'$10^{-3}$',
                           -2:'$10^{-2}$',
                           -1:'$10^{-1}$',
                            0:'$10^{0}$',
                            1:'$10^{1}$',
                            2:'$10^{2}$',
                            3:'$10^{3}$',
                            4:'$10^{4}$',
                            5:'$10^{5}$',
                            6:'$10^{6}$',
                            7:'$10^{7}$',
                            8:'$10^{8}$'}
        

        
        #plot on initialization
        self.plot_yn = plot_yn
        if self.plot_yn=='y':
            self.plot()
            
    def set_res_lst(self, res_lst):
        self.res_lst = res_lst
        #make a dictionary of values to write to file.
        self.res_dict = dict([(res, ii) 
                              for ii,res in enumerate(self.res_lst,1)]) 
        
    
    #---read files-------------------------------------------------------------    
    def read_file(self):
        """
        reads in initial file or model file and set attributes:
            -resmodel
            -northrid
            -eastrid
            -zgrid
            -res_lst if initial file
            
        """

        if self.model_fn is not None and self.init_fn is None:
            mtuple = readModelFile(self.model_fn)
            self.north = mtuple[0]
            self.east = mtuple[1]
            self.zg = mtuple[2]
            self.res = mtuple[3]
            self.north_nodes = mtuple[5]
            self.east_nodes = mtuple[6]
            self.z_nodes = mtuple[7]
            
            self.convert_res_to_model()
            
        elif self.init_fn is not None and self.model_fn is None:
            mtuple = readInit3D(self.init_fn)
            self.north = mtuple[0]
            self.east = mtuple[1]
            self.zg = mtuple[2]
            self.res = mtuple[5]
            self.res_lst = mtuple[3]
            self.north_nodes = mtuple[6]
            self.east_nodes = mtuple[7]
            self.z_nodes = mtuple[8]
            
            #need to convert index values to resistivity values
            rdict = dict([(ii,res) for ii,res in enumerate(self.res_lst,1)])
            
            for ii in range(len(self.res_lst)):
                self.res[np.where(self.res==ii+1)] = rdict[ii+1]
                
        elif self.init_fn is None and self.model_fn is None:
            print 'Need to input either an initial file or model file to plot'
        else:
            print 'Input just initial file or model file not both.'
            
        if self.data_fn is not None:
            dtuple = readDataFile(self.data_fn)
            self.station_x = dtuple[4]
            self.station_y = dtuple[3]
            
        self.m_height = np.median(self.north_nodes[5:-5])/self.dscale
        self.m_width = np.median(self.east_nodes[5:-5])/self.dscale
            
        #make a copy of original in case there are unwanted changes
        self.res_copy = self.res.copy()
            
            
            
    #---plot model-------------------------------------------------------------    
    def plot(self):
        """
        plots the model with:
            -a radio dial for depth slice 
            -radio dial for resistivity value
            
        """
        
        self.cmin = np.floor(np.log10(min(self.res_lst)))
        self.cmax = np.ceil(np.log10(max(self.res_lst)))
        
        #-->Plot properties
        plt.rcParams['font.size'] = self.font_size
        
        #need to add an extra row and column to east and north to make sure 
        #all is plotted see pcolor for details.
        plot_east = np.append(self.east, self.east[-1]*1.25)/self.dscale
        plot_north = np.append(self.north, self.north[-1]*1.25)/self.dscale
        
        #make a mesh grid for plotting
        #the 'ij' makes sure the resulting grid is in east, north
        self.eastgrid, self.northgrid = np.meshgrid(plot_east, 
                                                    plot_north,
                                                    indexing='ij')
        
        self.fig = plt.figure(self.fignum, figsize=self.figsize, dpi=self.dpi)
        self.ax1 = self.fig.add_subplot(1, 1, 1, aspect='equal')
        
        plot_res = np.log10(self.res[:,:,self.depth_index].T)
        
        self.mesh_plot = self.ax1.pcolormesh(self.eastgrid,
                                             self.northgrid, 
                                             plot_res,
                                             cmap=self.cmap,
                                             vmin=self.cmin,
                                             vmax=self.cmax)
                                             
        #on plus or minus change depth slice
        self.cid_depth = \
                    self.mesh_plot.figure.canvas.mpl_connect('key_press_event',
                                                        self._on_key_callback)
                                    
                       
        #plot the stations
        if self.station_x is not None:
            for ee, nn in zip(self.station_x, self.station_y):
                self.ax1.text(ee/self.dscale, nn/self.dscale,
                              '*',
                              verticalalignment='center',
                              horizontalalignment='center',
                              fontdict={'size':self.font_size-2,
                                        'weight':'bold'})

        #set axis properties
        if self.xlimits is not None:
            self.ax1.set_xlim(self.xlimits)
        else:
            self.ax1.set_xlim(xmin=self.east.min()/self.dscale, 
                              xmax=self.east.max()/self.dscale)
        
        if self.ylimits is not None:
            self.ax1.set_ylim(self.ylimits)
        else:
            self.ax1.set_ylim(ymin=self.north.min()/self.dscale,
                              ymax=self.north.max()/self.dscale)
            
        #self.ax1.xaxis.set_minor_locator(MultipleLocator(100*1./dscale))
        #self.ax1.yaxis.set_minor_locator(MultipleLocator(100*1./dscale))
        
        self.ax1.set_ylabel('Northing ('+self.mapscale+')',
                            fontdict=self.fdict)
        self.ax1.set_xlabel('Easting ('+self.mapscale+')',
                            fontdict=self.fdict)
        
        depth_title = self.zg[self.depth_index]/self.dscale
                                                        
        self.ax1.set_title('Depth = {:.3f} '.format(depth_title)+\
                           '('+self.mapscale+')',
                           fontdict=self.fdict)
        
        #plot the grid if desired              
        for xx in self.east:
            self.ax1.plot([xx/self.dscale, xx/self.dscale],
                          [self.north.min()/self.dscale, 
                           self.north.max()/self.dscale],
                           lw=.25,
                           color='k')

        for yy in self.north:
            self.ax1.plot([self.east.min()/self.dscale,
                           self.east.max()/self.dscale],
                           [yy/self.dscale, yy/self.dscale],
                           lw=.25,
                           color='k')
        
        #plot the colorbar
        self.ax2 = mcb.make_axes(self.ax1, orientation='vertical', shrink=.5)
        seg_cmap = cmap_discretize(self.cmap, len(self.res_lst))
        self.cb = mcb.ColorbarBase(self.ax2[0],cmap=seg_cmap,
                                   norm=colors.Normalize(vmin=self.cmin,
                                                         vmax=self.cmax))
                                                         
                            
        self.cb.set_label('Resistivity ($\Omega \cdot$m)',
                     fontdict={'size':self.font_size})
        self.cb.set_ticks(np.arange(self.cmin, self.cmax+1))
        self.cb.set_ticklabels([self.cblabeldict[cc] 
                            for cc in np.arange(self.cmin, self.cmax+1)])
                            
        #make a resistivity radio button
        resrb = self.fig.add_axes([.85,.1,.1,.15])
        reslabels = ['{0:.4g}'.format(res) for res in self.res_lst]
        self.radio_res = widgets.RadioButtons(resrb, reslabels,active=0)
        
        #make a rectangular selector
        self.rect_selector = widgets.RectangleSelector(self.ax1, 
                                                       self.rect_onselect,
                                                       drawtype='box',
                                                       useblit=True)

        
        plt.show()
        
        #needs to go after show()
        self.radio_res.on_clicked(self.set_res_value)


    def redraw_plot(self):
        """
        redraws the plot
        """
        
        self.ax1.cla()
        
        plot_res = np.log10(self.res[:,:,self.depth_index].T)
        
        self.mesh_plot = self.ax1.pcolormesh(self.eastgrid, self.northgrid, 
                                             plot_res,
                                             cmap=self.cmap,
                                             vmin=self.cmin,
                                             vmax=self.cmax)
                                             
         #plot the stations
        if self.station_x is not None:
            for ee,nn in zip(self.station_x, self.station_y):
                self.ax1.text(ee/self.dscale, nn/self.dscale,
                              '*',
                              verticalalignment='center',
                              horizontalalignment='center',
                              fontdict={'size':self.font_size-2,
                                        'weight':'bold'})

        #set axis properties
        if self.xlimits is not None:
            self.ax1.set_xlim(self.xlimits)
        else:
            self.ax1.set_xlim(xmin=self.east.min()/self.dscale, 
                              xmax=self.east.max()/self.dscale)
        
        if self.ylimits is not None:
            self.ax1.set_ylim(self.ylimits)
        else:
            self.ax1.set_ylim(ymin=self.north.min()/self.dscale,
                              ymax=self.north.max()/self.dscale)
            
        #self.ax1.xaxis.set_minor_locator(MultipleLocator(100*1./self.dscale))
        #self.ax1.yaxis.set_minor_locator(MultipleLocator(100*1./self.dscale))
        
        self.ax1.set_ylabel('Northing ('+self.mapscale+')',
                            fontdict=self.fdict)
        self.ax1.set_xlabel('Easting ('+self.mapscale+')',
                            fontdict=self.fdict)
        
        depth_title = self.zg[self.depth_index]/self.dscale
                                                        
        self.ax1.set_title('Depth = {:.3f} '.format(depth_title)+\
                           '('+self.mapscale+')',
                           fontdict=self.fdict)
                     
        #plot the grid if desired              
        for xx in self.east:
            self.ax1.plot([xx/self.dscale, xx/self.dscale],
                          [self.north.min()/self.dscale,
                           self.north.max()/self.dscale],
                           lw=.25,
                           color='k')

        for yy in self.north:
            self.ax1.plot([self.east.min()/self.dscale, 
                           self.east.max()/self.dscale],
                           [yy/self.dscale, yy/self.dscale],
                           lw=.25,
                           color='k')
        
        #be sure to redraw the canvas                  
        self.fig.canvas.draw()
        
    def set_res_value(self, label):
        self.res_value = float(label)
        print 'set resistivity to ', label
        print self.res_value
        
        
    def _on_key_callback(self,event):
        """
        on pressing a key do something
        
        """
        
        self.event_change_depth = event

        if self.event_change_depth.key=='=':
            self.depth_index += 1
            
            if self.depth_index>len(self.zg)-1:
                self.depth_index = len(self.zg)-1
                print 'already at deepest depth'
                
            print 'Plotting Depth {0:.3f}'.format(self.zg[self.depth_index]/\
                    self.dscale)+'('+self.mapscale+')'
            
            self.redraw_plot()

        elif self.event_change_depth.key=='-':
            self.depth_index -= 1
            
            if self.depth_index<0:
                self.depth_index = 0
                
            print 'Plotting Depth {0:.3f} '.format(self.zg[self.depth_index]/\
                    self.dscale)+'('+self.mapscale+')'
            
            self.redraw_plot()

        elif self.event_change_depth.key == 'q':
            self.event_change_depth.canvas.mpl_disconnect(self.cid_depth)
            plt.close(self.event_change_depth.canvas.figure)
            
        #copy the layer above
        elif self.event_change_depth.key == 'a':
            try:
                if self.depth_index == 0:
                    print 'No layers above'
                else:
                    self.res[:,:,self.depth_index] = \
                                              self.res[:,:,self.depth_index-1]
            except IndexError:
                print 'No layers above'
                
            self.redraw_plot()
        
        #copy the layer below
        elif self.event_change_depth.key == 'b':
            try:
                self.res[:,:,self.depth_index] = \
                                              self.res[:,:,self.depth_index+1]
            except IndexError:
                print 'No more layers below'
                
            self.redraw_plot() 
            
        #undo
        elif self.event_change_depth.key == 'u':
            self.res[self.ni0:self.ni1, self.ei0:self.ei1, self.depth_index] =\
            self.res_copy[self.ni0:self.ni1,self.ei0:self.ei1,self.depth_index]
            
            self.redraw_plot()
            
    def change_model_res(self, xchange, ychange):
        """
        change resistivity values of resistivity model
        
        """
        if type(xchange) is int and type(ychange) is int:
            self.res[ychange, xchange, self.depth_index] = self.res_value
        else:
            for xx in xchange:
                for yy in ychange:
                    self.res[yy, xx, self.depth_index] = self.res_value
        
        self.redraw_plot()            
           
    def rect_onselect(self, eclick, erelease):
        """
        on selecting a rectangle change the colors to the resistivity values
        """
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        
        xchange = self._get_east_index(x1, x2)
        ychange = self._get_north_index(y1, y2)
        
        #reset values of resistivity
        self.change_model_res(xchange, ychange)
        
        
    def _get_east_index(self, x1, x2):
        """
        get the index value of the points to be changed
        
        """
        print x1, x2
        if x1 < x2:
            xchange = np.where((self.east/self.dscale >= x1) & \
                               (self.east/self.dscale <= x2))[0]
            if len(xchange) == 0:
                xchange = np.where(self.east/self.dscale >= x1)[0][0]-1
                
                return [xchange]
                
        if x1 > x2:
            xchange = np.where((self.east/self.dscale <= x1) & \
                               (self.east/self.dscale >= x2))[0]
            if len(xchange) == 0:
                xchange = np.where(self.east/self.dscale >= x2)[0][0]-1
                return [xchange]

            
        #check the edges to see if the selection should include the square
        xchange = np.append(xchange, xchange[0]-1)
        xchange.sort()

        return xchange
                
    def _get_north_index(self, y1, y2):
        """
        get the index value of the points to be changed in north direction
        
        need to flip the index because the plot is flipped
        
        """
        
        if y1 < y2:
            ychange = np.where((self.north/self.dscale > y1) & \
                               (self.north/self.dscale < y2))[0]
            print 'y = ',ychange, len(ychange)
            if len(ychange) == 0:
                print ' north too small '
                ychange = np.where(self.north/self.dscale >= y1)[0][0]-1
                print ychange
                return [ychange]
                
        elif y1 > y2:
            ychange = np.where((self.north/self.dscale < y1) & \
                               (self.north/self.dscale > y2))[0]
            print 'y = ',ychange, len(ychange)
            if len(ychange) == 0:
                ychange = np.where(self.north/self.dscale >= y2)[0][0]-1
                return [ychange]
        
        ychange -= 1
        ychange = np.append(ychange, ychange[-1]+1)

        return ychange
        
            
    def convert_model_to_int(self):
        """
        convert the resistivity model that is in ohm-m to integer values
        corresponding to res_lst
        
        """
 
        self.res_model = np.ones_like(self.res)
        
        for key in self.res_dict.keys():
            self.res_model[np.where(self.res==key)] = self.res_dict[key]
            
    def convert_res_to_model(self):
        """
        converts an output model into an array of segmented valued according
        to res_lst.        
        
        """
        
        #make values in model resistivity array a value in res_lst
        resm = np.ones_like(self.res)
        resm[np.where(self.res<self.res_lst[0])] = \
                                            self.res_dict[self.res_lst[0]]
        resm[np.where(self.res)>self.res_lst[-1]] = \
                                            self.res_dict[self.res_lst[-1]]
        
        for zz in range(self.res.shape[2]):
            for yy in range(self.res.shape[1]):
                for xx in range(self.res.shape[0]):
                    for rr in range(len(self.res_lst)-1):
                        if self.res[xx,yy,zz]>=self.res_lst[rr] and \
                            self.res[xx,yy,zz]<=self.res_lst[rr+1]:
                            resm[xx,yy,zz] = self.res_dict[self.res_lst[rr]]
                            break
                        elif self.res[xx,yy,zz]<=self.res_lst[0]:
                            resm[xx,yy,zz] = self.res_dict[self.res_lst[0]]
                            break
                        elif self.res[xx,yy,zz]>=self.res_lst[-1]:
                            resm[xx,yy,zz] = self.res_dict[self.res_lst[-1]]
                            break
    
        self.res = resm
            
        
    def write_init_file(self, savepath, north_nodes=None, east_nodes=None,
                        z_nodes=None, title='Initial Model for wsinv3d'):
        """
        write an initial file for wsinv3d from the model created.
        """
        
        self.convert_model_to_int()
        
        #need to flip the resistivity model so that the first index is the 
        #northern most block in N-S
        self.res_model = self.res_model[::-1, :, :]
        
        try:
            init_new = writeInit3DFile(self.north_nodes, 
                                          self.east_nodes,
                                          self.z_nodes, 
                                          savepath, 
                                          reslst=self.res_lst,
                                          title=title,
                                          resmodel=self.res_model)
            return init_new
            
        except AttributeError:
            if north_nodes is not None:
                init_new = writeInit3DFile(north_nodes, 
                                              east_nodes,
                                              z_nodes, 
                                              savepath, 
                                              reslst=self.res_lst,
                                              title=title,
                                              resmodel=self.res_model)
                return init_new
            else:
                print 'Need to input the starting grid'
                                              
                

def cmap_discretize(cmap, N):
    """Return a discrete colormap from the continuous colormap cmap.
      
         cmap: colormap instance, eg. cm.jet. 
         N: number of colors.
     
     Example
         x = resize(arange(100), (5,100))
         djet = cmap_discretize(cm.jet, 5)
         imshow(x, cmap=djet)
    """

    colors_i = np.concatenate((np.linspace(0, 1., N), (0.,0.,0.,0.)))
    colors_rgba = cmap(colors_i)
    indices = np.linspace(0, 1., N+1)
    cdict = {}
    for ki,key in enumerate(('red','green','blue')):
        cdict[key] = [(indices[i], colors_rgba[i-1,ki], colors_rgba[i,ki])
                       for i in xrange(N+1)]
    # Return colormap object.
    return colors.LinearSegmentedColormap(cmap.name + "_%d"%N, cdict, 1024)

        
        
            
        

        
        
        
    
    
