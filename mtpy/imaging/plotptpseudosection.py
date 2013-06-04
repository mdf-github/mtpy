# -*- coding: utf-8 -*-
"""
Created on Thu May 30 18:10:55 2013

@author: jpeacock-pr
"""

#==============================================================================

import matplotlib.pyplot as plt
import numpy as np
import os
import matplotlib.colors as colors
import matplotlib.patches as patches
import matplotlib.colorbar as mcb
import mtpy.imaging.mtcolors as mtcl
import mtpy.imaging.mtplottools as mtpl

#==============================================================================

class PlotPhaseTensorPseudoSection(mtpl.MTEllipse, mtpl.MTArrows):
    """
    PlotPhaseTensorPseudoSection will plot the phase tensor ellipses in a 
    pseudo section format 
    
    
    Arguments:
    ----------
    
        **filenamelst** : list of strings
                          full paths to .edi files to plot
                          
        **z_object** : class mtpy.core.z.Z
                      object of mtpy.core.z.  If this is input be sure the
                      attribute z.frequency is filled.  *default* is None
                      
        **mt_object** : class mtpy.imaging.mtplot.MTplot
                        object of mtpy.imaging.mtplot.MTplot
                        *default* is None
                        
        **pt_object** : class mtpy.analysis.pt
                        phase tensor object of mtpy.analysis.pt.  If this is
                        input then the ._mt attribute is set to None cause
                        at the moment cannot tranform the phase tensor to z
                        *default* is None
        
        **ellipse_dict** : dictionary
                          dictionary of parameters for the phase tensor 
                          ellipses with keys:
                              * 'size' -> size of ellipse in points 
                                         *default* is 2
                              
                              * 'colorby' : [ 'phimin' | 'phimax' | 'skew' | 
                                              'skew_seg' | 'phidet' | 
                                              'ellipticity' ]
                                        
                                        - 'phimin' -> colors by minimum phase
                                        - 'phimax' -> colors by maximum phase
                                        - 'skew' -> colors by beta (skew)
                                        - 'skew_seg' -> colors by beta in 
                                                       discrete segments 
                                                       defined by the range
                                        - 'phidet' -> colors by determinant of
                                                     the phase tensor
                                        - 'ellipticity' -> colors by ellipticity
                                        *default* is 'phimin'
                                
                               * 'range' : tuple (min, max, step)
                                     Need to input at least the min and max
                                     and if using 'skew_seg' to plot
                                     discrete values input step as well
                                     *default* depends on 'colorby'
                                     
                          * 'cmap' : [ 'mt_yl2rd' | 'mt_bl2yl2rd' | 
                                      'mt_wh2bl' | 'mt_rd2bl' | 
                                      'mt_bl2wh2rd' | 'mt_seg_bl2wh2rd' |
                                      'mt_rd2gr2bl' ]
                                      
                                   - 'mt_yl2rd' -> yellow to red
                                   - 'mt_bl2yl2rd' -> blue to yellow to red
                                   - 'mt_wh2bl' -> white to blue
                                   - 'mt_rd2bl' -> red to blue
                                   - 'mt_bl2wh2rd' -> blue to white to red
                                   - 'mt_bl2gr2rd' -> blue to green to red
                                   - 'mt_rd2gr2bl' -> red to green to blue
                                   - 'mt_seg_bl2wh2rd' -> discrete blue to 
                                                         white to red
        
                                         
        
        **stretch** : float or tuple (xstretch, ystretch)
                        is a factor that scales the distance from one 
                        station to the next to make the plot readable.
                        *Default* is 200
                        
        **linedir** : [ 'ns' | 'ew' ]
                      predominant direction of profile line
                      * 'ns' -> North-South Line
                      * 'ew' -> East-West line
                      *Default* is 'ns'
        
        **stationid** : tuple or list 
                        start and stop of station name indicies.  
                        ex: for MT01dr stationid=(0,4) will be MT01
        
        **rotz** : float or np.ndarray
                   angle in degrees to rotate the data clockwise positive.
                   Can be an array of angle to individually rotate stations or
                   periods or both. 
                       - If rotating each station by a constant
                         angle the array needs to have a shape of 
                         (# of stations)
                        - If rotating by period needs to have shape 
                           # of periods
                        - If rotating both individually shape=(ns, nf)
                  *Default* is 0
        
        **title** : string
                    figure title
                    
        **dpi** : int 
                  dots per inch of the resolution. *default* is 300
                    
                       
        **fignum** : int
                     figure number.  *Default* is 1
        
        **plot_tipper** : [ 'yri' | 'yr' | 'yi' | 'n' ]
                        * 'yri' to plot induction both real and imaginary 
                           induction arrows 
                           
                        * 'yr' to plot just the real induction arrows
                        
                        * 'yi' to plot the imaginary induction arrows
                        
                        * 'n' to not plot them
                        
                        *Default* is 'n' 
                        
                        **Note: convention is to point towards a conductor but
                        can be changed in arrow_dict['direction']**
                         
        **arrow_dict** : dictionary for arrow properties
                        * 'size' : float
                                  multiplier to scale the arrow. *default* is 5
                        * 'head_length' : float
                                         length of the arrow head *default* is 
                                         1.5
                        * 'head_width' : float
                                        width of the arrow head *default* is 
                                        1.5
                        * 'lw' : float
                                line width of the arrow *default* is .5
                                
                        * 'color' : tuple (real, imaginary)
                                   color of the arrows for real and imaginary
                                   
                        * 'threshold': float
                                      threshold of which any arrow larger than
                                      this number will not be plotted, helps 
                                      clean up if the data is not good. 
                                      *default* is 1, note this is before 
                                      scaling by 'size'
                                      
                        * 'direction : [ 0 | 1 ]
                                     -0 for arrows to point toward a conductor
                                     -1 for arrow to point away from conductor
    
        **tscale** : [ 'period' | 'frequency' ]
        
                     * 'period'    -> plot vertical scale in period
                     
                     * 'frequency' -> plot vertical scale in frequency
                     
        **cb_dict** : dictionary to control the color bar
        
                      * 'orientation' : [ 'vertical' | 'horizontal' ]
                                       orientation of the color bar 
                                       *default* is vertical
                                       
                      * 'position' : tuple (x,y,dx,dy)
                                    - x -> lateral position of left hand corner 
                                          of the color bar in figure between 
                                          [0,1], 0 is left side
                                          
                                    - y -> vertical position of the bottom of 
                                          the color bar in figure between 
                                          [0,1], 0 is bottom side.
                                          
                                    - dx -> width of the color bar [0,1]
                                    
                                    - dy -> height of the color bar [0,1]
        **font_size** : float
                        size of the font that labels the plot, 2 will be added
                        to this number for the axis labels.
                        
        **plot_yn** : [ 'y' | 'n' ]
                      * 'y' to plot on creating an instance
                      
                      * 'n' to not plot on creating an instance
                      
        **xlim** : tuple(xmin, xmax)
                   min and max along the x-axis in relative distance of degrees
                   and multiplied by xstretch
                   
        **ylim** : tuple(ymin, ymax)
                   min and max period to plot, note that the scaling will be
                   done in the code.  So if you want to plot from (.1s, 100s)
                   input ylim=(.1,100)
    
    To get a list of .edi files that you want to plot -->
    :Example: ::
        
        >>> import mtpy.imaging.mtplottools as mtplot
        >>> import os
        >>> edipath = r"/home/EDIfiles"
        >>> edilst = [os.path.join(edipath,edi) for edi in os.listdir(edipath)
        >>> ...       if edi.find('.edi')>0]
    
    * If you want to plot minimum phase colored from blue to red in a range of
     20 to 70 degrees you can do it one of two ways--> 
    
    1)          
    :Example: ::
        
        >>> edict = {'range':(20,70), 'cmap':'mt_bl2gr2rd','colorby':'phimin'}
        >>> pt1 = mtplot.PlotPhaseTensorPseudoSection(edilst,ellipse_dict=edict)
     
    2)
    :Example: ::
        
        >>> pt1 = mtplot.PlotPhaseTensorPseudoSection(edilst, plot_yn='n')
        >>> pt1.ellipse_colorby = 'phimin'
        >>> pt1.ellipse_cmap = 'mt_bl2gr2rd'
        >>> pt1.ellipse_range = (20,70)
        >>> pt1.plot()
        
    * If you want to add real induction arrows that are scaled by 10 and point
     away from a conductor --> 
    :Example: ::
        
        >>> pt1.plot_tipper = 'yr'
        >>> pt1.arrow_size = 10
        >>> pt1.arrow_direction = -1
        >>> pt1.redraw_plot()
    
    * If you want to save the plot as a pdf with a generic name -->
    :Example: ::
        >>> pt1.save_figure(r"/home/PTFigures", file_format='pdf', dpi=300)
        File saved to '/home/PTFigures/PTPseudoSection.pdf'
        
    Attributes:
    -----------
        -arrow_color_imag     color of imaginary induction arrow
        -arrow_color_real     color of real induction arrow
        -arrow_direction      convention of arrows pointing to or away from 
                              conductors, see above.
        -arrow_head_length    length of arrow head in relative points
        -arrow_head_width     width of arrow head in relative points
        -arrow_lw             line width of arrows
        -arrow_size           scaling factor to multiple arrows by to be visible
        -arrow_threshold      threshold for plotting arrows, anything above 
                              this number will not be plotted.
        
        -ax                   matplotlib.axes instance for the main plot
        -ax2                  matplotlib.axes instance for the color bar
        -cb                   matplotlib.colors.ColorBar instance for color bar
        -cb_orientation       color bar orientation ('vertical' | 'horizontal')
        -cb_position          color bar position (x, y, dx, dy)
        
        -dpi                  dots-per-inch resolution
        
        -ellipse_cmap         ellipse color map, see above for options
        -ellipse_colorby      parameter to color ellipse by
        -ellipse_range        (min, max, step) values to color ellipses
        -ellipse_size         scaling factor to make ellipses visible
        
        -fig                  matplotlib.figure instance for the figure 
        -fignum               number of figure being plotted
        -figsize              size of figure in inches
        -font_size            font size of axes tick label, axes labels will be
                              font_size + 2
        
        -linedir              prominent direction of profile being plotted 
             
        -mt_lst               list of mtplot.MTplot instances containing all
                              the important information for each station
        -offsetlst            array of relative offsets of each station
        
        -plot_tipper          string to inform program to plot induction arrows
        -plot_yn              plot the pseudo section on instance creation
        
        -rot_z                rotates the data by this angle assuming North is
                              0 and angle measures clockwise
                              
        -stationid            index [min, max] to reaad station name
        -stationlst           list of stations plotted
        -title                title of figure
        -tscale               temporal scale of y-axis ('frequency' | 'period')
        
        -xlimits              limits on x-axis (xmin, xmax)
        -xstretch             scaling factor to stretch x offsets
        
        -ylimits              limits on y-axis (ymin, ymax)
        -ystep                step to set major ticks on y-axis
        -ystretch             scaling factor to strech axes in y direction
        
    Methods:
    --------

        -plot                 plots the pseudo section
        -redraw_plot          on call redraws the plot from scratch
        -save_figure          saves figure to a file of given format
        -update_plot          updates the plot while still active
        -writeTextFiles       writes parameters of the phase tensor and tipper
                              to text files.

    """
    
    
    def __init__(self, **kwargs):
        
        fn_lst = kwargs.pop('fn_lst', None)
        z_object_lst = kwargs.pop('z_object_lst', None)
        tipper_object_lst = kwargs.pop('tipper_object_lst', None)
        mt_object_lst = kwargs.pop('mt_object_lst', None)
        res_object_lst = kwargs.pop('res_object_lst', None)
        
        #----set attributes for the class-------------------------
        self.mt_lst = mtpl.get_mtlst(fn_lst=fn_lst, 
                                res_object_lst=res_object_lst,
                                z_object_lst=z_object_lst, 
                                tipper_object_lst=tipper_object_lst, 
                                mt_object_lst=mt_object_lst)
        
        #--> set the ellipse properties
        self._ellipse_dict = kwargs.pop('ellipse_dict', {})
        self._read_ellipse_dict()
            
        #--> set colorbar properties
        #set orientation to horizontal
        cb_dict = kwargs.pop('cb_dict', {})
        try:
            self.cb_orientation = cb_dict['orientation']
        except KeyError:
            self.cb_orientation = 'vertical'
        
        #set the position to middle outside the plot            
        try:
            self.cb_position = cb_dict['position']
        except KeyError:
            self.cb_position = None
            
        #set the stretching in each direction
        stretch = kwargs.pop('stretch', (50, 25))
        if type(stretch) == float or type(stretch) == int:
            self.xstretch = stretch
            self.ystretch = stretch
        else:
            self.xstretch = stretch[0]
            self.ystretch = stretch[1]
            
        #--> set plot properties
        self.fig_num = kwargs.pop('fig_num', 1)
        self.plot_num = kwargs.pop('plot_num', 1)
        self.plot_title = kwargs.pop('plot_title', None)
        self.fig_dpi = kwargs.pop('fig_dpi', 300)
        self.tscale = kwargs.pop('tscale', 'period')
        self.fig_size = kwargs.pop('fig_size', [6, 6])
        self.linedir = kwargs.pop('linedir', 'ew')
        self.font_size = kwargs.pop('font_size', 7)
        self.stationid = kwargs.pop('stationid', [0,4])
        self.ystep = kwargs.pop('ystep', 4)
        self.xlimits = kwargs.pop('xlimits', None)
        self.ylimits = kwargs.pop('ylimits', None)
        
        self._rot_z = kwargs.pop('rot_z', 0)
        if type(self._rot_z) is float or type(self._rot_z) is int:
            self._rot_z = np.array([self._rot_z]*len(self.mt_lst))
        
        #if the rotation angle is an array for rotation of different 
        #freq than repeat that rotation array to the len(mt_lst)
        elif type(self._rot_z) is np.ndarray:
            if self._rot_z.shape[0]  !=  len(self.mt_lst):
                self._rot_z = np.repeat(self._rot_z, len(self.mt_lst))
                
        else:
            pass
        
        #--> set induction arrow properties -------------------------------
        self.plot_tipper = kwargs.pop('plot_tipper', 'n')
        
        self._arrow_dict = kwargs.pop('arrow_dict', {})
        self._read_arrow_dict()
        
            
        #--> plot if desired
        self.plot_yn = kwargs.pop('plot_yn', 'y')
        if self.plot_yn == 'y':
            self.plot()
            
     #---need to rotate data on setting rotz
    def _set_rot_z(self, rot_z):
        """
        need to rotate data when setting z
        """
        
        #if rotation angle is an int or float make an array the length of 
        #mt_lst for plotting purposes
        if type(rot_z) is float or type(rot_z) is int:
            self._rot_z = np.array([rot_z]*len(self.mt_lst))
        
        #if the rotation angle is an array for rotation of different 
        #freq than repeat that rotation array to the len(mt_lst)
        elif type(rot_z) is np.ndarray:
            if rot_z.shape[0]!=len(self.mt_lst):
                self._rot_z = np.repeat(rot_z, len(self.mt_lst))
                
        else:
            pass
            
        for ii,mt in enumerate(self.mt_lst):
            mt.rot_z = rot_z[ii]
    def _get_rot_z(self):
        return self._rot_z
        
    rot_z = property(fget=_get_rot_z, fset=_set_rot_z, 
                     doc="""rotation angle(s)""")
        
    def plot(self):
        """
        plots the phase tensor pseudo section.  See class doc string for 
        more details.
        """
            
        plt.rcParams['font.size'] = self.font_size
        plt.rcParams['figure.subplot.left'] = .08
        plt.rcParams['figure.subplot.right'] = .98
        plt.rcParams['figure.subplot.bottom'] = .06
        plt.rcParams['figure.subplot.top'] = .96
        plt.rcParams['figure.subplot.wspace'] = .55
        plt.rcParams['figure.subplot.hspace'] = .70
        
        #create a plot instance
        self.fig = plt.figure(self.fig_num, self.fig_size, dpi=self.fig_dpi)
        self.ax = self.fig.add_subplot(1, 1, 1, aspect='equal')
        
        #create empty lists to put things into
        self.stationlst = []
        self.offsetlst = []
        minlst = []
        maxlst = []
        plot_periodlst = None
        
        #set local parameters with shorter names
        es = self.ellipse_size
        ck = self.ellipse_colorby
        cmap = self.ellipse_cmap
        ckmin = float(self.ellipse_range[0])
        ckmax = float(self.ellipse_range[1])
        try:
            ckstep = float(self.ellipse_range[2])
        except IndexError:
            ckstep = 3
                
        nseg = float((ckmax-ckmin)/(2*ckstep))

        if cmap == 'mt_seg_bl2wh2rd':
            bounds = np.arange(ckmin, ckmax+ckstep, ckstep)
        #plot phase tensor ellipses
        for ii, mt in enumerate(self.mt_lst):
            self.stationlst.append(
                              mt.station[self.stationid[0]:self.stationid[1]])
            
            #set the an arbitrary origin to compare distance to all other 
            #stations.
            if ii == 0:
                east0 = mt.lon
                north0 = mt.lat
                offset = 0.0
            else:
                east = mt.lon
                north = mt.lat
                if self.linedir == 'ew': 
                    if east0 < east:
                        offset = np.sqrt((east0-east)**2+(north0-north)**2)
                    elif east0 > east:
                        offset = -1*np.sqrt((east0-east)**2+(north0-north)**2)
                    else:
                        offset = 0
                elif self.linedir == 'ns':
                    if north0 < north:
                        offset = np.sqrt((east0-east)**2+(north0-north)**2)
                    elif north0 > north:
                        offset = -1*np.sqrt((east0-east)**2+(north0-north)**2)
                    else:
                        offset = 0
                        
            self.offsetlst.append(offset)
            
            #get phase tensor elements and flip so the top is small 
            #periods/high frequency
            pt = mt.get_PhaseTensor()
            
            periodlst = mt.period[::-1]
            phimax = pt.phimax[0][::-1]
            phimin = pt.phimin[0][::-1]
            azimuth = pt.azimuth[0][::-1]
        
            #if there are induction arrows, flip them as pt
            if self.plot_tipper.find('y') == 0:
                tip = mt.get_Tipper()
                if tip.mag_real is not None:
                    tmr = tip.mag_real[::-1]
                    tmi = tip.mag_imag[::-1]
                    tar = tip.ang_real[::-1]
                    tai = tip.ang_imag[::-1]
                else:
                    tmr = np.zeros(len(mt.period))
                    tmi = np.zeros(len(mt.period))
                    tar = np.zeros(len(mt.period))
                    tai = np.zeros(len(mt.period))
                    
                aheight = self.arrow_head_length 
                awidth = self.arrow_head_width
                alw = self.arrow_lw
                
            #get the properties to color the ellipses by
            if self.ellipse_colorby == 'phimin':
                colorarray = pt.phimin[0][::-1]
                
            elif self.ellipse_colorby == 'phimax':
                colorarray = pt.phimin[0][::-1]
                
            elif self.ellipse_colorby == 'phidet':
                colorarray = np.sqrt(abs(pt.det[::-1]))*(180/np.pi)
                
            elif self.ellipse_colorby == 'skew' or\
                 self.ellipse_colorby == 'skew_seg':
                colorarray = pt.beta[0][::-1]
                
            elif self.ellipse_colorby == 'ellipticity':
                colorarray = pt.ellipticity[::-1]
                
            else:
                raise NameError(self.ellipse_colorby+' is not supported')
            
            #get the number of periods
            n = len(periodlst)
            
            if ii == 0:
                plot_periodlst = periodlst
            
            else:
                if n > len(plot_periodlst):
                    plot_periodlst = periodlst
            
            #get min and max of the color array for scaling later
            minlst.append(min(colorarray))
            maxlst.append(max(colorarray))

            for jj, ff in enumerate(periodlst):
                
                #make sure the ellipses will be visable
                eheight = phimin[jj]/phimax[jj]*es
                ewidth = phimax[jj]/phimax[jj]*es
            
                #create an ellipse scaled by phimin and phimax and orient
                #the ellipse so that north is up and east is right
                #need to add 90 to do so instead of subtracting
                ellipd = patches.Ellipse((offset*self.xstretch,
                                          np.log10(ff)*self.ystretch),
                                            width=ewidth,
                                            height=eheight,
                                            angle=azimuth[jj]+90)
                                            
                #get ellipse color
                if cmap.find('seg')>0:
                    ellipd.set_facecolor(mtcl.get_plot_color(colorarray[jj],
                                                             self.ellipse_colorby,
                                                             cmap,
                                                             ckmin,
                                                             ckmax,
                                                             bounds=bounds))
                else:
                    ellipd.set_facecolor(mtcl.get_plot_color(colorarray[jj],
                                                             self.ellipse_colorby,
                                                             cmap,
                                                             ckmin,
                                                             ckmax))
                    
                # == =add the ellipse to the plot == ========
                self.ax.add_artist(ellipd)
                
                
                #--------- Add induction arrows if desired --------------------
                if self.plot_tipper.find('y') == 0:
                    
                    #--> plot real tipper
                    if self.plot_tipper == 'yri' or self.plot_tipper == 'yr':
                        txr = tmr[jj]*np.cos(tar[jj]*np.pi/180+\
                                             np.pi*self.arrow_direction)*\
                                             self.arrow_size
                        tyr = tmr[jj]*np.sin(tar[jj]*np.pi/180+\
                                             np.pi*self.arrow_direction)*\
                                             self.arrow_size
                        
                        maxlength = np.sqrt((txr/self.arrow_size)**2+\
                                            (tyr/self.arrow_size)**2)
                                            
                        if maxlength > self.arrow_threshold:
                            pass
                        else:
                            self.ax.arrow(offset*self.xstretch, 
                                          np.log10(ff)*self.ystretch, 
                                          txr,
                                          tyr,
                                          lw=alw,
                                          facecolor=self.arrow_color_real,
                                          edgecolor=self.arrow_color_real,
                                          length_includes_head=False,
                                          head_width=awidth,
                                          head_length=aheight)
                                      
                    #--> plot imaginary tipper
                    if self.plot_tipper == 'yri' or self.plot_tipper == 'yi':
                        txi = tmi[jj]*np.cos(tai[jj]*np.pi/180+\
                                             np.pi*self.arrow_direction)*\
                                             self.arrow_size
                        tyi = tmi[jj]*np.sin(tai[jj]*np.pi/180+\
                                             np.pi*self.arrow_direction)*\
                                             self.arrow_size
                        
                        maxlength = np.sqrt((txi/self.arrow_size)**2+\
                                            (tyi/self.arrow_size)**2)
                        if maxlength > self.arrow_threshold:
                            pass
                        else:
                            self.ax.arrow(offset*self.xstretch,
                                          np.log10(ff)*self.ystretch,
                                          txi,
                                          tyi,
                                          lw=alw,
                                          facecolor=self.arrow_color_imag,
                                          edgecolor=self.arrow_color_imag,
                                          length_includes_head=False,
                                          head_width=awidth,
                                          head_length=aheight)
        
        #--> Set plot parameters 
        self._plot_periodlst = plot_periodlst
        n = len(plot_periodlst)
        
        
        #calculate minimum period and maximum period with a stretch factor
        pmin = np.log10(plot_periodlst.min())*self.ystretch
        pmax = np.log10(plot_periodlst.max())*self.ystretch
               
        self.offsetlst = np.array(self.offsetlst)
        
        #set y-ticklabels
        if self.tscale == 'period':
            yticklabels = ['{0:>4}'.format('{0: .1e}'.format(plot_periodlst[ll])) 
                            for ll in np.arange(0, n, self.ystep)]+\
                        ['{0:>4}'.format('{0: .1e}'.format(plot_periodlst[-1]))]
            
            self.ax.set_ylabel('Period (s)',
                               fontsize=self.font_size,
                               fontweight='bold')
                               
        elif self.tscale == 'frequency':
            yticklabels = ['{0:>4}'.format('{0: .1e}'.format(1./plot_periodlst[ll])) 
                            for ll in np.arange(0, n, self.ystep)]+\
                            ['{0:>4}'.format('{0: .1e}'.format(1./plot_periodlst[-1]))]
            
            self.ax.set_ylabel('Frequency (Hz)',
                               fontsize=self.font_size,
                               fontweight='bold')
        #set x-axis label                       
        self.ax.set_xlabel('Station',
                           fontsize=self.font_size+2,
                           fontweight='bold')
         
        #--> set tick locations and labels
        #set y-axis major ticks
        self.ax.yaxis.set_ticks([np.log10(plot_periodlst[ll])*self.ystretch 
                             for ll in np.arange(0, n, self.ystep)])
        
        #set y-axis minor ticks                     
        self.ax.yaxis.set_ticks([np.log10(plot_periodlst[ll])*self.ystretch 
                             for ll in np.arange(0, n, 1)],minor=True)
        #set y-axis tick labels
        self.ax.set_yticklabels(yticklabels)
        
        #set x-axis ticks
        self.ax.set_xticks(self.offsetlst*self.xstretch)
        
        #set x-axis tick labels as station names
        self.ax.set_xticklabels(self.stationlst)
        
        #--> set x-limits
        if self.xlimits == None:
            self.ax.set_xlim(self.offsetlst.min()*self.xstretch-es*2,
                             self.offsetlst.max()*self.xstretch+es*2)
        else:
            self.ax.set_xlim(self.xlimits)
            
        #--> set y-limits
        if self.ylimits == None:
            self.ax.set_ylim(pmax+es*2, pmin-es*2)
        else:
            pmin = np.log10(self.ylimits[0])*self.ystretch
            pmax = np.log10(self.ylimits[1])*self.ystretch
            self.ax.set_ylim(pmax+es*2, pmin-es*2)
            
        #--> set title of the plot
        if self.plot_title == None:
            pass
        else:
            self.ax.set_title(self.plot_title, fontsize=self.font_size+2)
        
        #make a legend for the induction arrows
        if self.plot_tipper.find('y') == 0:
            if self.plot_tipper == 'yri':
                treal = self.ax.plot(np.arange(10)*.000005,
                                     np.arange(10)*.00005,
                                     color=self.arrow_color_real)
                timag = self.ax.plot(np.arange(10)*.000005,
                                     np.arange(10)*.00005,
                                     color=self.arrow_color_imag)
                self.ax.legend([treal[0], timag[0]],
                               ['Tipper_real','Tipper_imag'],
                               loc='lower right',
                               prop={'size':self.font_size-1,'weight':'bold'},
                               ncol=2,
                               markerscale=.5,
                               borderaxespad=.005,
                               borderpad=.25)
                          
            elif self.plot_tipper == 'yr':
                treal = self.ax.plot(np.arange(10)*.000005,
                                     np.arange(10)*.00005,
                                     color=self.arrow_color_real)
                self.ax.legend([treal[0]],
                               ['Tipper_real'],
                               loc='lower right',
                               prop={'size':self.font_size-1,'weight':'bold'},
                               ncol=2,
                               markerscale=.5,
                               borderaxespad=.005,
                               borderpad=.25)
                          
            elif self.plot_tipper == 'yi':
                timag = self.ax.plot(np.arange(10)*.000005,
                                     np.arange(10)*.00005,
                                     color=self.arrow_color_imag)
                self.ax.legend([timag[0]],
                               ['Tipper_imag'],
                               loc='lower right',
                               prop={'size':self.font_size-1,'weight':'bold'},
                               ncol=2,
                               markerscale=.5,
                               borderaxespad=.005,
                               borderpad=.25)
        
        #put a grid on the plot
        self.ax.grid(alpha=.25, which='both', color=(.25, .25, .25))
        
        #print out the min an max of the parameter plotted
        print '-'*25
        print ck+' min = {0:.2f}'.format(min(minlst))
        print ck+' max = {0:.2f}'.format(max(maxlst))
        print '-'*25

        #==> make a colorbar with appropriate colors
        if self.cb_position == None:
            self.ax2, kw = mcb.make_axes(self.ax,
                                         orientation=self.cb_orientation,
                                         shrink=.35)
        else:
            self.ax2 = self.fig.add_axes(self.cb_position)
        
        if cmap == 'mt_seg_bl2wh2rd':
            #make a color list
            self.clst = [(cc, cc, 1) 
                         for cc in np.arange(0, 1+1./(nseg), 1./(nseg))]+\
                        [(1, cc, cc) 
                         for cc in np.arange(1, -1./(nseg), -1./(nseg))]
            
            #make segmented colormap
            mt_seg_bl2wh2rd = colors.ListedColormap(self.clst)

            #make bounds so that the middle is white
            bounds = np.arange(ckmin-ckstep, ckmax+2*ckstep, ckstep)
            
            #normalize the colors
            norms = colors.BoundaryNorm(bounds, mt_seg_bl2wh2rd.N)
            
            #make the colorbar
            self.cb = mcb.ColorbarBase(self.ax2,
                                       cmap=mt_seg_bl2wh2rd,
                                       norm=norms,
                                       orientation=self.cb_orientation,
                                       ticks=bounds[1:-1])
        else:
            self.cb = mcb.ColorbarBase(self.ax2,
                                       cmap=mtcl.cmapdict[cmap],
                                       norm=colors.Normalize(vmin=ckmin,
                                                             vmax=ckmax),
                                       orientation=self.cb_orientation)

        #label the color bar accordingly
        self.cb.set_label(mtpl.ckdict[ck],
                          fontdict={'size':self.font_size,'weight':'bold'})
            
        #place the label in the correct location                   
        if self.cb_orientation == 'horizontal':
            self.cb.ax.xaxis.set_label_position('top')
            self.cb.ax.xaxis.set_label_coords(.5, 1.3)
            
            
        elif self.cb_orientation == 'vertical':
            self.cb.ax.yaxis.set_label_position('right')
            self.cb.ax.yaxis.set_label_coords(1.25, .5)
            self.cb.ax.yaxis.tick_left()
            self.cb.ax.tick_params(axis='y', direction='in')
        
        plt.show()
        
    def writeTextFiles(self, save_path=None, ptol=0.10):
        """
        This will write text files for all the phase tensor parameters
        """
        
        if save_path == None:
            try:
                svpath = os.path.dirname(self.mt_lst[0].fn)
            except TypeError:
                raise IOError('Need to input save_path, could not find a path')
        else:
            svpath = save_path
        
        #check to see if plot has been run if not run it
        try:
            plst = self._plot_periodlst

        except AttributeError:
            self.plot()
            plst = self._plot_periodlst
        
        if plst[0] > plst[-1]:
            plst = plst[::-1] 
            
        if self.tscale == 'frequency':
            plst = 1./plst
        
        #match station list with mt list
        slst = [mt for ss in self.stationlst for mt in self.mt_lst 
                 if os.path.basename(mt.fn).find(ss)>=0]
           
        ns = len(slst)+1
        nt = len(plst)+1
        
        #set some empty lists to put things into
        sklst = np.zeros((nt, ns), dtype='|S8')
        phiminlst = np.zeros((nt, ns), dtype='|S8')
        phimaxlst = np.zeros((nt, ns), dtype='|S8')
        elliplst = np.zeros((nt, ns), dtype='|S8')
        azimlst = np.zeros((nt, ns), dtype='|S8')
        tiplstr = np.zeros((nt, ns), dtype='|S8')
        tiplsti = np.zeros((nt, ns), dtype='|S8')
        tiplstraz = np.zeros((nt, ns), dtype='|S8')
        tiplstiaz = np.zeros((nt, ns), dtype='|S8')
        
         
        sklst[0, 0] = '{0:>8} '.format(self.tscale)
        phiminlst[0, 0] = '{0:>8} '.format(self.tscale)
        phimaxlst[0, 0] = '{0:>8} '.format(self.tscale)
        elliplst[0, 0] = '{0:>8} '.format(self.tscale)
        azimlst[0, 0] = '{0:>8} '.format(self.tscale)
        tiplstr[0, 0] = '{0:>8} '.format(self.tscale)
        tiplstraz[0, 0] = '{0:>8} '.format(self.tscale)
        tiplsti[0, 0] = '{0:>8} '.format(self.tscale)
        tiplstiaz[0, 0] = '{0:>8} '.format(self.tscale)           
        
        #get the period as the first column
        for tt, t1 in enumerate(plst, 1):
            sklst[tt, 0] = t1
            phiminlst[tt, 0] = t1
            phimaxlst[tt, 0] = t1
            elliplst[tt, 0] = t1
            azimlst[tt, 0] = t1
            tiplstr[tt, 0] = t1
            tiplstraz[tt, 0] = t1
            tiplsti[tt, 0] = t1
            tiplstiaz[tt, 0] = t1
            
        #fill out the rest of the values
        for kk, mt in enumerate(slst, 1):
            
            pt = mt.get_PhaseTensor()
            tip = mt.get_Tipper()
                
            if self.tscale == 'period':
                tlst = mt.period
                    
            elif self.tscale == 'frequency':
                tlst = mt.frequency
 
            try:
                stationstr = '{0:^8}'.format(mt.station[self.stationid[0]:\
                                                    self.stationid[1]])
            except AttributeError:
                stationstr = '{0:^8}'.format(mt.station)
            
            #-->  get station name as header in each file                                     
            sklst[0, kk] = stationstr
            phiminlst[0, kk] = stationstr
            phimaxlst[0, kk] = stationstr
            elliplst[0, kk] = stationstr
            azimlst[0, kk] = stationstr
            tiplstr[0, kk] = stationstr
            tiplstraz[0, kk] = stationstr
            tiplsti[0, kk] = stationstr
            tiplstiaz[0, kk] = stationstr
                                                
            # If the all periods match for the station and the plotting period         
            if tlst.all() == plst.all():
                if pt.pt is not None:
                    sklst[1:, kk] = pt.beta[0]
                    phiminlst[1:, kk] = pt.phimin[0]
                    phimaxlst[1:, kk] = pt.phimax[0]
                    elliplst[1:, kk] = pt.ellipticity[0]
                    azimlst[1:, kk] = pt.azimuth[0]
                if tip.mag_real is not None:
                    tiplstr[1:, kk] = tip.mag_real
                    tiplstraz[1:, kk] = tip.ang_real
                    tiplsti[1:, kk] = tip.mag_imag
                    tiplstiaz[1:, kk] = tip.ang_imag
                    
            # otherwise search the period list to find a cooresponding period
            else:   
                for mm, t1 in enumerate(plst):
                    #check to see if the periods match or are at least close in
                    #case there are frequency missing
                    t1_yn = False
                    if t1 == tlst[mm]:
                        t1_yn = True
                    elif tlst[mm] > t1*(1-ptol) and tlst[mm] < t1*(1+ptol):
                        t1_yn = True
                    
                    if t1_yn == True:
                        #add on the value to the present row
                        if pt.beta[0] is not None:
                            sklst[mm+1, kk] = pt.beta[0][mm]
                            phiminlst[mm+1, kk] = pt.phimin[0][mm]
                            phimaxlst[mm+1, kk] = pt.phimax[0][mm]
                            elliplst[mm+1, kk] = pt.ellipticity[0][mm]
                            azimlst[mm+1, kk] = pt.azimuth[0][mm]
                        
                        #add on the value to the present row
                        if tip.mag_real is not None:
                            tiplstr[mm+1, kk] = tip.mag_real[mm]
                            tiplstraz[mm+1, kk] = tip.ang_real[mm]
                            tiplsti[mm+1, kk] = tip.mag_imag[mm]
                            tiplstiaz[mm+1, kk] = tip.ang_imag[mm]
                    
                    elif t1_yn == False:
                        for ff, t2 in enumerate(tlst):
                            if t2 > t1*(1-ptol) and t2 < t1*(1+ptol):
                                #add on the value to the present row
                                if pt.beta[0] is not None:
                                    sklst[mm+1, kk] = pt.beta[0][ff]
                                    phiminlst[mm+1, kk] = pt.phimin[0][ff]
                                    phimaxlst[mm+1, kk] = pt.phimax[0][ff]
                                    elliplst[mm+1, kk] = pt.ellipticity[0][ff]
                                    azimlst[mm+1, kk] = pt.azimuth[0][ff]
                                
                                #add on the value to the present row
                                if tip.mag_real is not None:
                                    tiplstr[mm+1, kk] = tip.mag_real[ff]
                                    tiplstraz[mm+1, kk] = tip.ang_real[ff]
                                    tiplsti[mm+1, kk] = tip.mag_imag[ff]
                                    tiplstiaz[mm+1, kk] = tip.ang_imag[ff]
                                t1_yn = True
                                break
                            else:
                                t1_yn = False

        #write the arrays into lines properly formatted
        t1_kwargs = {'spacing':'{0:^8} ', 'value_format':'{0:.2e}', 
                     'append':False, 'add':False}
        t2_kwargs = {'spacing':'{0:^8}', 'value_format':'{0: .2f}', 
                     'append':False, 'add':False}
        #create empty lists to put the concatenated strings into
        sklines = []
        phiminlines = []
        phimaxlines = []
        elliplines = []
        azimlines = []
        tprlines = []
        tprazlines = []
        tpilines = []
        tpiazlines = []
        
        #if there are any blank strings set them as 0
        sklst[np.where(sklst=='')] = '0.0'
        phiminlst[np.where(phiminlst=='')] = '0.0'
        phimaxlst[np.where(phimaxlst=='')] = '0.0'
        elliplst[np.where(elliplst=='')] = '0.0'
        azimlst[np.where(azimlst=='')] = '0.0'
        tiplstr[np.where(tiplstr=='')] = '0.0'
        tiplstraz[np.where(tiplstraz=='')] = '0.0'
        tiplsti[np.where(tiplsti=='')] = '0.0'
        tiplstiaz[np.where(tiplstiaz=='')] = '0.0'
        
        for tt in range(nt):
            if tt == 0:
                skline = sklst[tt, 0]+' '
                pminline = phiminlst[tt, 0]+' '
                pmaxline = phimaxlst[tt, 0]+' '
                elliline = elliplst[tt, 0]+' '
                azline = azimlst[tt, 0]+' '
                tprline = tiplstr[tt, 0]+' '
                tprazline = tiplstraz[tt, 0]+' '
                tpiline = tiplsti[tt, 0]+' '
                tpiazline = tiplstiaz[tt, 0]+' '
                for ss in range(1, ns):
                    skline += sklst[tt, ss]
                    pminline += phiminlst[tt, ss]
                    pmaxline += phimaxlst[tt, ss]
                    elliline += elliplst[tt, ss]
                    azline += azimlst[tt, ss]
                    tprline += tiplstr[tt, ss]
                    tprazline += tiplstraz[tt, ss]
                    tpiline += tiplsti[tt, ss]
                    tpiazline += tiplstiaz[tt, ss]
            else:
                #get period or frequency
                skline = mtpl._make_value_str(float(sklst[tt, 0]), 
                                                   **t1_kwargs)
                pminline = mtpl._make_value_str(float(phiminlst[tt, 0]), 
                                                **t1_kwargs)
                pmaxline = mtpl._make_value_str(float(phimaxlst[tt, 0]),
                                                **t1_kwargs)
                elliline = mtpl._make_value_str(float(elliplst[tt, 0]), 
                                                **t1_kwargs)
                azline = mtpl._make_value_str(float(azimlst[tt, 0]), 
                                              **t1_kwargs)
                tprline = mtpl._make_value_str(float(tiplstr[tt, 0]), 
                                               **t1_kwargs)
                tprazline = mtpl._make_value_str(float(tiplstraz[tt, 0]), 
                                            **t1_kwargs)
                tpiline = mtpl._make_value_str(float(tiplsti[tt, 0]), 
                                               **t1_kwargs)
                tpiazline = mtpl._make_value_str(float(tiplstiaz[tt, 0]), 
                                                 **t1_kwargs)
                
                #get parameter values
                for ss in range(1, ns):
                    skline += mtpl._make_value_str(float(sklst[tt, ss]), 
                                                   **t2_kwargs)
                    pminline += mtpl._make_value_str(float(phiminlst[tt, ss]),
                                                **t2_kwargs)
                    pmaxline += mtpl._make_value_str(float(phimaxlst[tt, ss]),
                                                **t2_kwargs)
                    elliline += mtpl._make_value_str(float(elliplst[tt, ss]),
                                                **t2_kwargs)
                    azline += mtpl._make_value_str(float(azimlst[tt, ss]),
                                              **t2_kwargs)
                    tprline += mtpl._make_value_str(float(tiplstr[tt, ss]),
                                               **t2_kwargs)
                    tprazline += mtpl._make_value_str(float(tiplstraz[tt, ss]),
                                                 **t2_kwargs)
                    tpiline += mtpl._make_value_str(float(tiplsti[tt, ss]),
                                               **t2_kwargs)
                    tpiazline += mtpl._make_value_str(float(tiplstiaz[tt, ss]),
                                                 **t2_kwargs)
            
            # be sure to end the line after each period
            sklines.append(skline+'\n')
            phiminlines.append(pminline+'\n')
            phimaxlines.append(pmaxline+'\n')
            elliplines.append(elliline+'\n')
            azimlines.append(azline+'\n')
            tprlines.append(tprline+'\n')
            tprazlines.append(tprazline+'\n')
            tpilines.append(tpiline+'\n')
            tpiazlines.append(tpiazline+'\n')
        
        #write files
        skfid = file(os.path.join(svpath,'PseudoSection.skew'),'w')
        skfid.writelines(sklines)
        skfid.close()
        
        phiminfid = file(os.path.join(svpath,'PseudoSection.phimin'),'w')
        phiminfid.writelines(phiminlines)
        phiminfid.close()
        
        phimaxfid = file(os.path.join(svpath,'PseudoSection.phimax'), 
                         'w')
        phimaxfid.writelines(phimaxlines)
        phimaxfid.close()
        
        ellipfid = file(os.path.join(svpath,'PseudoSection.ellipticity'), 
                        'w')
        ellipfid.writelines(elliplines)
        ellipfid.close()
        
        azfid = file(os.path.join(svpath,'PseudoSection.azimuth'), 
                     'w')
        azfid.writelines(azimlines)
        azfid.close()
        
        tprfid = file(os.path.join(svpath,'PseudoSection.tipper_mag_real'), 
                      'w')
        tprfid.writelines(tprlines)
        tprfid.close()
        
        tprazfid = file(os.path.join(svpath,'PseudoSection.tipper_ang_real'),
                        'w')
        tprazfid.writelines(tprazlines)
        tprazfid.close()
        
        tpifid = file(os.path.join(svpath,'PseudoSection.tipper_mag_imag'),
                      'w')
        tpifid.writelines(tpilines)
        tpifid.close()
        
        tpiazfid = file(os.path.join(svpath,'PseudoSection.tipper_ang_imag'),
                        'w')
        tpiazfid.writelines(tpiazlines)
        tpiazfid.close()
    
    def update_plot(self):
        """
        update any parameters that where changed using the built-in draw from
        canvas.  
        
        Use this if you change an of the .fig or axes properties
        
        :Example: ::
            
            >>> # to change the grid lines to be on the major ticks and gray 
            >>> pt1.ax.grid(True, which='major', color=(.5,.5,.5))
            >>> pt1.update_plot()
        
        """

        self.fig.canvas.draw()
        
    def redraw_plot(self):
        """
        use this function if you updated some attributes and want to re-plot.
        
        :Example: ::
            
            >>> # change ellipse size and color map to be segmented for skew 
            >>> pt1.ellipse_size = 5
            >>> pt1.ellipse_colorby = 'beta_seg'
            >>> pt1.ellipse_cmap = 'mt_seg_bl2wh2rd'
            >>> pt1.ellipse_range = (-9, 9, 3)
            >>> pt1.redraw_plot()
        """
        
        plt.close(self.fig)
        self.plot()
        
    def __str__(self):
        """
        rewrite the string builtin to give a useful message
        """
        
        return "Plots pseudo section of phase tensor ellipses" 
        
    def save_figure(self, save_fn, file_format='pdf', orientation='portrait', 
                  fig_dpi=None, close_plot='y'):
        """
        save_plot will save the figure to save_fn.
        
        Arguments:
        -----------
        
            **save_fn** : string
                          full path to save figure to, can be input as
                          * directory path -> the directory path to save to
                            in which the file will be saved as 
                            save_fn/station_name_ResPhase.file_format
                            
                          * full path -> file will be save to the given 
                            path.  If you use this option then the format
                            will be assumed to be provided by the path
                            
            **file_format** : [ pdf | eps | jpg | png | svg ]
                              file type of saved figure pdf,svg,eps... 
                              
            **orientation** : [ landscape | portrait ]
                              orientation in which the file will be saved
                              *default* is portrait
                              
            **fig_dpi** : int
                          The resolution in dots-per-inch the file will be
                          saved.  If None then the dpi will be that at 
                          which the figure was made.  I don't think that 
                          it can be larger than dpi of the figure.
                          
            **close_plot** : [ y | n ]
                             * 'y' will close the plot after saving.
                             * 'n' will leave plot open
                          
        :Example: ::
            >>> # save plot as a jpg
            >>> pt1.save_plot(r'/home/MT/figures', file_format='jpg')
            
        """

        if fig_dpi == None:
            fig_dpi = self.fig_dpi
            
        if os.path.isdir(save_fn) == False:
            file_format = save_fn[-3:]
            self.fig.savefig(save_fn, dpi=fig_dpi, format=file_format,
                             orientation=orientation)
            plt.clf()
            plt.close(self.fig)
            
        else:
            save_fn = os.path.join(save_fn, 'PTPseudoSection.'+
                                   file_format)
            self.fig.savefig(save_fn, dpi=fig_dpi, format=file_format,
                             orientation=orientation)
        
        if close_plot == 'y':
            plt.clf()
            plt.close(self.fig)
        
        else:
            pass
        
        self.fig_fn = save_fn
        print 'Saved figure to: '+self.fig_fn