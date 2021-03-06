
        
    def plot(self):
        """
        plot 1 or more parameters in a model
        
        """
        n_axes = len(self.parameters)   
        
        sp = 1
        for parameter in self.parameters:
            plt.subplot(n_axes,1,sp)
            self.plot_parameter(parameter)
            sp += 1
        
        if self.save:
            if self.output_filename is None:
                self.construct_filename()
            plt.savefig(os.path.join(self.working_directory,self.output_filename))
                
            
    def plot_section(self):
        """
        plot 1d models along a profile
        
        """
        return

    
    def construct_filename(self):
        """
        create a filename to save file to
        
        """
        filename = os.path.basename(self.working_directory)
        filename += '_'.join(self.parameters)     
        self.output_filename = filename


class Plot_fit():
    
    def __init__(self, Fit, **input_parameters):
        """
        Fit = fit object from pek1dclasses
        imethod = interpolation method for contour map
        symbol = symbol to plot on maps
        cmap = colormap to use
        normalise_misfit = True/False = normalise misfit to 1 or not, useful if 
        plotting lots of stations at once
        normalise_x = normalise value on x axis of l curve
        label_points = whether or not to label points by penalty weight
        colorby = None or 'penalty_weight' 'log_penalty_weight' or 'misfit', 
        color points according to one of these properties, only implemented so 
        far for lcurve not lcurve contour map
        
        
        """
        self.Fit = Fit
        self.imethod = 'linear'
        self.symbol = 'o'
        self.fontsize = 8
        self.cmap = 'rainbow'
        self.normalise_misfit = False
        self.normalise_x = False
        self.label_points = True
        self.colorby = None
        
        for key in input_parameters.keys():
            setattr(self,key,input_parameters[key]) 

        
    def plot_lcurve_contourmap(self, draw_threshold = False,
                               xlim = None, ylim = None,
                               contour_step = None
                               ):
        """
        plot 'lcurve' contour map
        N  = number of levels to contour
        imethod = type of interpolation for numpy.griddata
                  options are 'nearest','linear', and 'cubic'
        symbol = symbol for plotting
        fontsize = numeric value
        draw_threshold = draw a black contour at a given percentage of the minimum rms error
                         e.g. 110 will draw a contour at 1.1 * minimum error value achieved
        
        """
        
        self.Fit.read_fit()
        a = self.Fit.penalty_anisotropy
        s = self.Fit.penalty_structure
        mis = self.Fit.misfit_mean
        aa = [str(round(i,1)) for i in self.Fit.weight_anisotropy]
        ss = [str(round(i,1)) for i in self.Fit.weight_structure]
           
        
        # grid the data to make contour plot
        # first, define points to grid
        points = np.vstack([s,a]).T
        # define points xi to grid onto
        xi = np.array(np.meshgrid(np.linspace(0.,max(s)),np.linspace(0.,max(a)))).T
#        print xi
        f1 = si.griddata(points,mis,xi,method = self.imethod)
        cmap = plt.get_cmap(self.cmap)
        
        if contour_step is not None:
            if contour_step < 1.:
                rounding = int(np.ceil(np.abs(np.log10(contour_step))))
            else:
                rounding = 0
            levels = np.arange(round(np.amin(self.Fit.misfit_mean),rounding),
                   round(np.amax(self.Fit.misfit_mean,rounding),
                   contour_step))
            plt.contour(xi[:,:,0],
                        xi[:,:,1],
                        f1,cmap=cmap,
                        levels=levels)
        else:
            plt.contour(xi[:,:,0],xi[:,:,1],f1,cmap=cmap)
        plt.colorbar()
        
        if draw_threshold:
            plt.contour(xi[:,:,0],xi[:,:,1],f1,
                        levels=[round(min(mis)*self.Fit.misfit_threshold,2)],
                                linewidths=[1.5],
                                colors='k')
#        plt.gca().set_aspect('equal')
        plt.scatter(s,a,c='k',marker=self.symbol,lw=0)
        

                
        if xlim is None:
            xlim = plt.xlim()
        if ylim is None:
            ylim = plt.ylim()
        plt.xlim(xlim)
        plt.ylim(ylim)
            
        for i in range(len(aa)):
            if (s[i] < xlim[-1]) and (a[i] < ylim[-1]):
                plt.text(s[i],a[i],','.join([ss[i],aa[i]]),fontsize=self.fontsize)
        plt.xlabel('structure penalty')
        plt.ylabel('anisotropy penalty')   

    
    def plot_lcurve(self,parameter,fixed_value):
        """
        plot an l curve for structure or anisotropy, fixing the other to
        fixed_value
        
        """
        fixed_value=float(fixed_value)        
        
        self.Fit.read_fit()
        a = self.Fit.penalty_anisotropy
        s = self.Fit.penalty_structure
        mis = self.Fit.misfit_mean
        aa = self.Fit.weight_anisotropy
        ss = self.Fit.weight_structure
#        print aa
#        print ss
        
        if parameter == 'anisotropy':
            c = np.abs(ss-fixed_value)<0.001
            x = a[c]
            lx = aa[c]
        else:
            c = np.abs(aa-fixed_value)<0.001
            x = s[c]
            lx = ss[c]          
        y = mis[c]
        

        if self.normalise_misfit:
            y = 1.*y/np.amin(y)
        if self.normalise_x:
            x = 1.*x/np.amin(x)
            
    
        if self.colorby == 'misfit':
            c = mis
        elif self.colorby == 'log_penalty_weight':
            c = np.log10(lx)
        elif self.colorby == 'penalty_weight':
            c = lx
        else:
            c = 'k'

        plt.scatter(x,y,c=c,
                    s=40,
                    linewidth=0.0,
                    cmap=self.cmap,
                    edgecolor='white',
                    marker=self.symbol,
                    label=self.Fit.station)
        
        if self.labels:
            for i in range(len(lx)):
                plt.text(x[i],y[i],str(round(lx[i],1)))

        self.ax = plt.gca()
      

class Plot_responses():
    """
    plot model responses and/or input data
    inherits a Response and Data class    
    
    """
    
    def __init__(self, Data, Response, **input_parameters):

        self.Data = Data
        self.Response = Response
        self.working_directory = self.Response.working_directory
        self.modelno = 0
        self.save = True
        self.output_filename = None

        for key in input_parameters.keys():
            setattr(self,key,input_parameters[key])
                     

    def plot_responses(self,datafile,modelno=0,adjust_phase = True):
        """
                
        
        """
        
        if not hasattr(self.Data,'resistivity'):
            self.read_datafile(datafile)
        if not hasattr(self.Response,'resistivity'):
            self.read_respfile()
            
        T = 1./self.freq
        r = self.Data.resistivity
        re = self.Data.resistivity_err
        p = self.Data.phase
        pe = self.Data.phase_err
        rmod = self.Response.resistivity[self.modelno]
        pmod = self.Response.phase[self.modelno]
        
        if adjust_phase:
            p[p<0] += 180
            pmod[pmod<0] += 180
        
        ii = 1
        fig = plt.figure()
        fig.text(0.5,0.95,self.Data.datafile[:-4])
        
        for mode,err,model in [[r,re,rmod],[p,pe,pmod]]:
            for sequence in [[[0,1],[1,0]],[[0,0],[1,1]]]:
                ax = plt.subplot(2,2,ii)
                ax.set_color_cycle(['b','r'])
                for i,j in sequence:
                    plt.errorbar(T,mode[:,i,j],err[:,i,j],fmt='--')
                    plt.plot(T,model[:,i,j],'k--')
                    plt.xscale('log')
                if ii <= 2:
                    plt.yscale('log')
                plt.grid()
                ii += 1

      
         
         
class Plot_map():
    """
    class dealing with plotting results in map format, from multiple 
    1d models
    
    """
    def __init__(self,aniso_depth_file,**input_parameters):
        self.levels = None
        self.n_levels = 10
        self.escale = 0.001
        self.anisotropy_threshold = [1.,100]
        self.cmap = 'jet_r'
        self.scaleby = 'resmin'
        self.anisotropy_display_factor = 0.75
        self.xlim = None
        self.ylim = None
        self.plot_cbar=True
        self.cbar_ax = [0.8,0.1,0.08,0.8]
        self.imethod = 'linear'
        self.scalebar = True
        self.aniso_depth_file = aniso_depth_file
        self.aniso_depth_file_dict = dict(header_rows=1,
                                          scale='km')
        self.xyzfiles = None
        self.xyzfiles_dict = dict(header_rows=1,
                                  scale='km')
        self.xyzfile_titles = None
        self.additional_xy_data = {}
        self.plot_text = {}
        self.set_titles = True

        self.subplot_layout = 'vertical'
        self.wspace = 0.02
        self.hspace = 0.15
        self.fonttype = 'serif'
        self.figsize=(8,5)
        
        for key in input_parameters.keys():
            if hasattr(self,str.lower(key)):
                setattr(self,key,input_parameters[key]) 
            
        self.read_aniso_depth_data()
        if self.xyzfiles is not None:
            if type(self.xyzfiles) == str:
                self.xyzfiles = [self.xyzfiles]
            if self.xyzfile_titles is None:
                titles = []
                for f in self.xyzfiles:
                    titles.append(op.basename(f))
                self.xyzfile_titles = titles
            else:
                if type(self.xyzfile_titles) == str:
                    self.xyzfile_titles = [self.xyzfile_titles]
                while len(self.xyzfile_titles) < len(self.xyzfiles):
                    self.xyzfile_titles.append('')

        font0 = FontProperties()
        font = font0.copy()
        font.set_family(self.fonttype)
        self.font = font                   
                    
    def _update_axis_params(self,title='',labels='xy'):
        
        ax = plt.gca()


        xticks = ax.get_xticks()
        ax.set_xticklabels(['%6.2f'%t for t in xticks])
        if 'x' in labels:
            plt.xlabel('Longitude')
        else:
            ax.set_xticklabels([])
        if 'y' in labels:
            plt.ylabel('Latitude')
        else:
            ax.set_yticklabels([])
        if self.set_titles:
            plt.title(title)


    def read_aniso_depth_data(self):

        hr = self.aniso_depth_file_dict['header_rows']
        surface = np.loadtxt(self.aniso_depth_file,skiprows=hr)
        surface = surface[surface[:,4]/surface[:,3]>self.anisotropy_threshold[0]]
        x,y,z,resmin,resmax,strike = [surface[:,i] for i in range(len(surface[0]))]
        aniso = resmax/resmin
        
        for a,label in [[x,'x'],[y,'y'],[z,'z'],[resmin,'resmin'],
                        [resmax,'resmax'],[strike,'strike'],[aniso,'aniso']]:
            setattr(self,label,a)        

    def plot_aniso_depth_map(self):
        """
        """

        import matplotlib.patches as mpatches
                                   
        x,y,z,resmin = self.x,self.y,self.z,self.resmin
        resmax,strike,aniso = self.resmax,self.strike,self.aniso
        
        if self.levels is None:
            zmin,zmax = np.amin(self.z),np.amax(self.z)
            self.levels = np.linspace(zmin,zmax,self.n_levels)
        
        
        # reset anisotropy values greater than a threshold for plotting
        aniso[aniso>self.anisotropy_threshold[1]] = self.anisotropy_threshold[1]
        
        scale = self.aniso_depth_file_dict['scale']
        cbar = self.plot_cbar
        self.plot_cbar = False
        
        self.plot_interface(x,y,z,scale=scale)
        
        if len(self.xyzfiles) == 0:
            title = "Magnitude and depth of anisotropy\nfrom 1D anisotropic inversions"
            self._update_axis_params(title,'xy')

        
        if self.scaleby == 'resmin':
            scale = 1./resmin
        else:
            scale = aniso**self.anisotropy_display_factor

        x += np.sin(np.deg2rad(strike-180.))*scale*self.escale*0.5
        y += np.cos(np.deg2rad(strike-180.))*scale*self.escale*0.5

        # make rectangles
        recs = [mpatches.Rectangle(xy=np.array([x[i],y[i]]), 
                                   width = self.escale*scale[i],
                                   height = self.escale,
                                   angle=90-strike[i],
                                   lw=0.5) for i in range(len(x))]
        if self.scalebar:
            scalebar_size = round(max(scale))
            sxy = np.array([plt.xlim()[0]+0.01,plt.ylim()[-1]-0.025])
            
            recs.append(mpatches.Rectangle(xy=sxy, 
                                           width = self.escale*scalebar_size,
                                           height = self.escale,
                                           angle=0,
                                           lw=0.5))
            plt.text(sxy[0],sxy[1]+0.007,
            r'${\frac{\rho_{max}}{\rho_{min}}}=%1i$'%scalebar_size,
            fontsize=11)

        ax1 = plt.gca()
        
        for i,e in enumerate(recs):
            ax1.add_artist(e)
            e.set_facecolor('k')
         
        self.add_ax_text(1)
        self.add_xy_data(1)
            
        if cbar:
            self.add_cbar()
        self.cbar = cbar
        
    
    def plot_interface(self,x,y,z,scale='km'):
        """
        take xyz data, create a grid and make a contour plot
        
        """

        import pek1dplotting as p1dp
        
        z = p1dp.update_scale(z,scale)

        xi = np.array(np.meshgrid(np.linspace(min(x),max(x),20),np.linspace(min(y),max(y),50))).T
        
        zi = si.griddata(np.vstack([x,y]).T,
                         z,
                         xi,
                         method=self.imethod)
        
        cmap = plt.get_cmap(self.cmap)
        
        if self.levels is None:
            plt1 = plt.contourf(xi[:,:,0],xi[:,:,1],zi,cmap=cmap)
            self.levels = plt1.levels
        else:
            plt1 = plt.contourf(xi[:,:,0],xi[:,:,1],zi,
                                levels=self.levels,cmap=cmap)
        ax = plt.gca()
       
        ax.set_aspect('equal')
        
        if self.plot_cbar:
            self.add_cbar() 

        if self.xlim is not None:
            plt.xlim(self.xlim)
        if self.ylim is not None:
            plt.ylim(self.ylim)
            

        

        
    def plot_aniso_and_interfaces(self,plot_aniso=True):
        """
        plot a set of models and up to three interfaces for comparison.        
        
        """        
        import pek1dplotting as p1dp        
        
        if type(self.xyzfiles) == str:
            self.xyzfiles = [self.xyzfiles]
            
        if self.subplot_layout == 'vertical':
            s1,s2 = len(self.xyzfiles)+1,1
            sp_labels = ['y']*(len(self.xyzfiles)-1)+['xy']
            ad_labels = 'y'
            if not plot_aniso:
                s1 -= 1
        elif self.subplot_layout == 'horizontal':
            s2,s1 = len(self.xyzfiles)+1,1
            sp_labels = ['x']*(len(self.xyzfiles))
            ad_labels = 'xy'
            if not plot_aniso:
                s2 -= 1
                sp_labels[0] += 'y'
#        elif self.subplot_layout == 'grid':
#            s1 = int(np.ceil((len(self.xyzfiles)+1)**0.5))
#            s2 = s1
#            sp_labels = ['','xy','x']
#            ad_labels = 'y'
        
        

        # set self.cmap false for the time being, until all individual plots are done
        cbar = self.plot_cbar
        self.plot_cbar = False          
            
        header_rows,scale = [[d[at] for d in [self.aniso_depth_file_dict,
                             self.xyzfiles_dict]] for at in ['header_rows','scale']]
                                                 
        self.z = p1dp.update_scale(self.z,scale[0])
        zmin,zmax = np.amin(self.z),np.amax(self.z)
        
        for f in self.xyzfiles:
            z = p1dp.update_scale(np.loadtxt(f,skiprows=header_rows[1])[:,2],
                                  scale[1])
            if np.amin(z) < zmin:
                zmin = np.amin(z)
            if np.amax(z) > zmax:
                zmax = np.amax(z)
            
        self.levels = np.linspace(zmin,zmax,self.n_levels)
        
        x,y = self.x,self.y
#        if self.figsize is None:
#            ar = ((float(s1)/float(s2))*((np.amax(y) - np.amin(y))/(np.amax(x) - np.amin(x))))**0.9
#            self.figsize=(10,10*ar)
        plt.figure(figsize=self.figsize)
        

        plt.subplot(s1,s2,1)

        if plot_aniso:
            sp = range(2,len(self.xyzfiles)+2)
            self.plot_aniso_depth_map()
            title = "Magnitude and depth of anisotropy\nfrom 1D anisotropic inversions"
            self._update_axis_params(title,ad_labels)
        else:
            sp = range(1,len(self.xyzfiles)+1)
        
#        plt.gca().set_xticklabels([])
        for s,ss in enumerate(sp):
            ax = plt.subplot(s1,s2,ss)
#            print self.xyzfiles[s]
            xyz = np.loadtxt(self.xyzfiles[s],skiprows=header_rows[1])
            x,y,z = [xyz[:,i] for i in range(3)]
            self.plot_interface(x,y,z,
                                scale=scale[1])
            self.add_xy_data(ss)
            self.add_ax_text(ss)
                    
            self._update_axis_params(title=self.xyzfile_titles[s],
                                     labels=sp_labels[s])
            if 'x' not in sp_labels[s]:
                ax.set_xticklabels([])
                plt.xlabel('')
            if 'y' not in sp_labels[s]:
                ax.set_yticklabels([])
                plt.ylabel('')

        self.plot_cbar = cbar
        bottom = self.cbar_ax[1]+self.cbar_ax[3]+0.05
        plt.subplots_adjust(wspace=self.wspace,
                            hspace=self.hspace,
                            bottom=bottom)

        if self.plot_cbar:
            self.add_cbar()

    def add_cbar(self):
        if self.cbar_ax[-2]/self.cbar_ax[-1] > 1.:
            cbo = 'horizontal'
        else:
            cbo = 'vertical'
        ax = plt.axes(self.cbar_ax)
        ax.set_visible(False)
        cbar = plt.colorbar(fraction=0.8,orientation=cbo)
        cbar.set_label("Depth (km)")
        cticks = range(int(self.levels[0]),int(self.levels[-1]+1))
        cbar.set_ticks(cticks)

    def add_xy_data(self,spn):
        
        if str(spn) in self.additional_xy_data.keys():
            for dd in self.additional_xy_data[str(spn)]:
                try:
                    zorder=dd[3]
                except:
                    zorder=10
                plt.plot(dd[0],dd[1],dd[2],zorder=zorder)
        
    def add_ax_text(self,spn):
        
        if str(spn) in self.plot_text.keys():
            for dd in self.plot_text[str(spn)]:
                for ii in range(len(dd[0])):
                    plt.text(dd[0][ii],dd[1][ii],dd[2][ii])
                


    def plot_location_map(self,
                          plot_names = True):
        """
        plot location map of all stations.        
        
        """
        return



class Plot_profile():
    """

    """    
    
    
    def __init__(self,Model_suite,**input_parameters):
        
        self.Model_suite = Model_suite
        self.working_directory = Model_suite.working_directory
        self.parameters = [['minmax'],['aniso','strike']]
        self.titles = {'minmax':'Minimum and maximum resistivity, $\Omega m$',
                       'aniso':'Anisotropy in resistivity',# (maximum/minimum resistivity)
                       'strike':'Strike angle of minimum resistivity'}#, $^\circ$
        self.xlim = {'minmax':[0.1,1000],
                     'aniso':[0,20],
                     'strike':[0,180]}

        self.ylim = [6,0]
        self.modelno = Model_suite.modelno
        self.modeltype = 'model'
        self.rotation_angle = 0.
        
        
        self.station_listfile = None
        self.station_xyfile = None
        
        self.figsize = (6,6)
        self.plot_spacing = 0.1
        self.title_type = 'single'
        self.fonttype = 'sans-serif'
        self.label_fontsize = 8
        self.title_fontsize = 12
        self.linedict = dict(style='-',width=1,
                              colour=[['0.5','k']]*2)
        self.horizon_list = None
        self.horizon_zscale = 'km'
        self.horizon_linedict = dict(style=['-']*6,width=[2]*6,
                                     colour=['c','y','b','r','g','m'])
                                     
                                     
        self.subplot_dict = dict(wspace=0.1,bottom=0.25,hspace=0.4)
        
        # store inputs in the object to pass through to Plot_model object
        self.input_parameters = input_parameters

        # set attributes from keyword arguments          
        for key in input_parameters.keys():
            if hasattr(self,key):
                setattr(self,key,input_parameters[key])
                self.input_parameters[key] = input_parameters[key]

        font0 = FontProperties()
        font = font0.copy()
        font.set_family(self.fonttype)
        self.font = font
            
        self.working_directory = os.path.abspath(self.working_directory)

    def _set_axis_params(self,ax,parameter):
        
 
        xlim = self.xlim[parameter]

        plt.xlim(xlim)
        plt.ylim(self.ylim)
        plt.grid()
        ax.set_xticks(xlim)

#        ax.get_xticklabels()[0].set_horizontalalignment('left')
#        ax.get_xticklabels()[-1].set_horizontalalignment('right')
        for label in ax.get_xticklabels():
            label.set_fontsize(self.label_fontsize)
            label.set_rotation(90)
            label.set_verticalalignment('top')
            

        return plt.gca()
            
    def get_profile(self):
        """
        get location of profile by linear regression
        """
        if self.Model_suite.x is None:
            print "can't get profile, no x y locations"
            return
        
        x = self.Model_suite.x
        y = self.Model_suite.y
        
        self.profile = np.polyfit(x,y,1)
        


    def get_profile_origin(self):
        """
        get the origin of the profile in real world coordinates
        
        Author: Alison Kirkby (2013)
        """
        if not hasattr(self,'profile'):
            self.get_profile()
            
        x,y = self.Model_suite.x,self.Model_suite.y
        x1,y1 = x[0],y[0]
        [m,c1] = self.profile
        x0 = (y1+(1.0/m)*x1-c1)/(m+(1.0/m))
        y0 = m*x0+c1
        
        self.profile_origin = [x0,y0]        
 
       
    def get_station_distance(self):
        """
        project a well location onto the profile.
        stores the result in the setup variable well_locations.
        x,y = x,y locations of well
        
        Author: Alison Kirkby
        """
        distances = []
        
        x,y = self.Model_suite.x,self.Model_suite.y
        
        if not hasattr(self,'profile_origin'):
            self.get_profile_origin()

        x0,y0 = self.profile_origin
        
            
        # project drillhole location onto profile and get distance along profile
        [m,c1] = self.profile
        [x0,y0] = self.profile_origin
        xp = (y+(1.0/m)*x-c1)/(m+(1.0/m))
        yp = m*x+c1
        xp -= x0
        yp -= y0
        distances = (xp**2.+yp**2.)**(0.5)
            
        self.station_distances = distances
#        for 


             
        
    def plot_parameter(self,#parameter,
                       twiny_offset=0.25,
                       new_figure = True,
                       plot_inmodel=True,
                       additional_data = None):
        """
        parameter = 'anisotropy', 'minmax', or 'strike' or list containing 
        several of these
        
        additional_data - additional data (e.g. resistivity logs)
        to plot on the figure. Provide as a list of 2D numpy arrays [depth, param]
        
        
        """
        
        nvplots = len(self.parameters)
        
        for nv in range(nvplots):
            for i in range(len(self.Model_suite.model_list)):
                Model = self.Model_suite.model_list[i]
                PM = Plot_model(Model,**self.input_parameters)
                PM.parameters = self.parameters[nv]
                if 'minmax' not in self.parameters[nv]:
                    PM.horizon_list = None
                plt.subplot(nvplots,
                            len(self.Model_suite.model_list),
                            nv*len(self.Model_suite.model_list)+i+1)

                axes = PM.plot_parameter(twiny_offset=twiny_offset,
                                         plot_inmodel=plot_inmodel,
                                         additional_data = additional_data)
    
                if additional_data is not None:
#                    print "plotting additional data"
                    plt.plot(additional_data[i][:,0],additional_data[i][:,1],lw=0.1)
                if i != 0:
                    axes[0][0].set_yticklabels([])
                for ax,p in axes:
                    ax.xaxis.label.set_color(p.get_color())
                    ax.tick_params(axis='x', colors=p.get_color())
                    ax.spines['bottom'].set_color(p.get_color())
                    if i == 0:
                        for label in ax.get_yticklabels():
                            label.set_fontproperties(self.font)
                            label.set_fontsize(self.label_fontsize)
                            ylab = plt.ylabel('Depth, km')
                            ylab.set_fontproperties(self.font)
                    if self.title_type == 'single':
                        if i == int(len(self.Model_suite.model_list)/2)-1:
#                        if i == 0:
                            if type(self.parameters[nv]) == list:
                                titlestring = ' and\n'.join([self.titles[p] for p in self.parameters[nv]])
                            else: titlestring = self.titles[self.parameters[nv]]
                            title = plt.xlabel(titlestring,ha='center',va='top',labelpad=0)
                            if len(self.parameters[nv]) > 1:
                                ax.xaxis.set_label_coords(0.5,-self.subplot_dict['hspace']-0.05)
#                                ax.xaxis.label.set_color('k')
                            title.set_fontproperties(self.font)
                            title.set_fontsize(self.title_fontsize)
    
#                    elif self.title_type == 'multiple':
#                        title = plt.title(self.titles[i])
#                    elif self.title_type == 'station':
#                        title = plt.title(self.Model_suite.model_list[i].station)
#                    title.set_fontproperties(self.font)
            plt.subplots_adjust(**self.subplot_dict)
        
    def plot_location_map(self):
        """
        plot location map of all stations with profile shown on map.        
        
        """
        
        if self.Model_suite.station_xyfile is None:
            print "can't get locations, no x y file"
            return
        
        if not hasattr(self,'profile_origin'):
            self.get_profile_origin()

        font0 = FontProperties()
        font = font0.copy()
        font.set_family('serif')        
            
        xy_all = np.genfromtxt(self.Model_suite.station_xyfile,invalid_raise=False)[:,1:]
        plt.plot(xy_all[:,0],xy_all[:,1],'.',c='0.5')
        
        m,c = self.profile
        x0,y0 = self.profile_origin
        
        if m > 1:
            y1 = max(self.Model_suite.y)
            x1 = (y1-c)/m
        else:
            x1 = max(self.Model_suite.x)
            y1 = m*x1 + c
        
        plt.plot([x0,x1],[y0,y1],'k')
        plt.plot(self.Model_suite.x,self.Model_suite.y,'k.')
        
        ax=plt.gca()
        for label in ax.get_yticklabels():
            label.set_fontproperties(font)
        for label in ax.get_xticklabels():
            label.set_fontproperties(font)        
        
