import numpy as np
from uncertainties import unumpy as unp
import matplotlib as mpl
import math
# headless mode
mpl.use('Agg')
# fonts
mpl.rcParams['mathtext.fontset'] = 'custom'
mpl.rcParams['mathtext.rm'] = 'Bitstream Vera Sans'
mpl.rcParams['mathtext.it'] = 'Bitstream Vera Sans:italic'
mpl.rcParams['mathtext.bf'] = 'Bitstream Vera Sans:bold'
from matplotlib import pyplot as plt
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from matplotlib.offsetbox import AnchoredText
from pisa.utils.log import logging

class plotter(object):

    def __init__(self, outdir='.', stamp='PISA cake test', size=(8,8), fmt='pdf', log=True, label='# events', grid=True, ratio=False):
        self.outdir = outdir
        self.stamp = stamp
        self.fmt = fmt
        self.size = size
        self.fig = None
        self.log = log
        self.label = label
        self.grid = grid
        self.ratio = ratio

    # --- helper functions ---

    def init_fig(self,figsize=None):
        ''' clear/initialize figure '''
        if figsize is not None:
            size = figsize
        else:
            size = self.size
        if self.fig is not None:
            plt.clf()
            plt.close(self.fig)
        self.fig, self.axes = plt.subplots(1,1,figsize=size)
        self.fig.patch.set_facecolor('none')

    def add_stamp(self, text=None):
        ''' ad common stamp with text '''
        if text is not None:
            a_text = AnchoredText(self.stamp + '\n' + r'$%s$'%text, loc=2, frameon=False)
        else:
            a_text = AnchoredText(self.stamp, loc=2, frameon=False)
        plt.gca().add_artist(a_text)

    def add_leg(self):
        ''' initialize legend '''
        plt.gca().legend(loc='upper right',ncol=2, frameon=False,numpoints=1)

    def dump(self,fname):
        ''' dump figure to file'''
        plt.savefig(self.outdir+'/'+fname+'.'+self.fmt, dpi=150, edgecolor='none',facecolor=self.fig.get_facecolor())

    # --- 2d plots ---

    def plot_2d_single(self, mapset):
        ''' plot all maps in individual plots '''
        for map in mapset:
            self.init_fig()
            self.plot_2d_map(map)
            self.add_stamp(map.tex)
            self.dump(map.name)

    def plot_2d_array(self, mapset, n_rows=None, n_cols=None):
        ''' plot all maps in a single plot '''
        self.plot_array(mapset, 'plot_2d_map', n_rows=n_rows, n_cols=n_cols)
        self.dump('test2d')

    # --- 1d plots ---

    def plot_1d_single(self, mapset, plot_axis):
        ''' plot all maps in individual plots '''
        for map in mapset:
            self.init_fig()
            self.plot_1d_projection(map, plot_axis)
            self.add_stamp(map.tex)
            self.dump(map.name)

    def plot_1d_array(self, mapset, plot_axis, n_rows=None,
            n_cols=None):
        ''' plot 1d projections as an array '''
        self.plot_array(mapset, 'plot_1d_projection', plot_axis, n_rows=n_rows,
                n_cols=n_cols)
        self.dump('test1d')

    def plot_1d_all(self, mapset, plot_axis):
        ''' all one one canvas '''
        self.init_fig()
        for map in mapset:
            self.plot_1d_projection(map, plot_axis)
        self.add_stamp()
        self.add_leg()
        self.dump('all')

    def plot_1d_stack(self, mapset, plot_axis):
        ''' all maps stacked on top of each other '''
        self.init_fig()
        for i, map in enumerate(mapset):
            for j in range(i):
                map += mapset[j]
            self.plot_1d_projection(map, plot_axis)
        self.add_stamp()
        self.add_leg()
        self.dump('stack')

    def plot_1d_cmp(self, mapset0, mapset1, plot_axis):
        ''' 1d comparisons for two mapsets '''
        for map0, map1 in zip(mapset0, mapset1):
            self.init_fig()
            if self.ratio:
                ax1 = plt.subplot2grid((4,1), (0,0), rowspan=3)
                plt.setp(ax1.get_xticklabels(), visible=False)
            self.plot_1d_projection(map0, plot_axis, ptype='data')
            self.plot_1d_projection(map1, plot_axis)
            self.add_stamp()
            self.add_leg()
            if self.ratio:
                plt.subplot2grid((4,1), (3,0),sharex=ax1)
                self.plot_1d_ratio([map0, map1], plot_axis)
            self.dump('cmp_%s'%map0.name)

    # --- plotting core functions ---

    def plot_array(self, mapset, fun, *args, **kwargs):
        ''' wrapper funtion to exccute plotting function fun for every map in a set
        distributed over a grid '''
        n_rows = kwargs.pop('n_rows', None)
        n_cols = kwargs.pop('n_cols', None)
        ''' plot mapset in array using a function fun '''
        n = len(mapset)
        if n_rows is None and n_cols is None:
            # TODO: auto row/cols
            n_rows = math.floor(math.sqrt(n))
            while n % n_rows != 0:
               n_rows -= 1
            n_cols = n / n_rows
        assert( n <= n_cols * n_rows), 'you are trying to plot %s subplots on a grid with %s x %s cells'%(n, n_cols, n_rows)
        size = (n_cols*self.size[0], n_rows*self.size[1])
        self.init_fig(size)
        plt.tight_layout()
        h_margin = 1. / size[0]
        v_margin = 1. / size[1]
        self.fig.subplots_adjust(hspace=0.3, wspace=0.3, top=1-v_margin, bottom=v_margin, left=h_margin, right=1-h_margin)
        for i, map in enumerate(mapset):
            plt.subplot(n_rows,n_cols,i+1)
            getattr(self, fun)(map, *args)
            self.add_stamp(map.tex)

    def plot_2d_map(self, map):
        ''' plot map on current axis in 2d'''
        axis = plt.gca()
        bins = [map.binning[name] for name in map.binning.names]
        bin_edges = map.binning.bin_edges
        cmap = np.log10(map.hist) if self.log else map.hist
        extent = [np.min(bin_edges[0].m), np.max(bin_edges[0].m), np.min(bin_edges[1].m), np.max(bin_edges[1].m)]
        # needs to be flipped for imshow
        img = plt.imshow(cmap.T,origin='lower',interpolation='nearest',extent=extent,aspect='auto', cmap='rainbow')
        axis.set_xlabel(bins[0].label)
        axis.set_ylabel(bins[1].label)
        if bins[0].is_log:
            axis.set_xscale('log')
        if bins[1].is_log:
            axis.set_yscale('log')
        col_bar = plt.colorbar(format=r'$10^{%.1f}$') if self.log else plt.colorbar()
        if self.label:
            col_bar.set_label(self.label)
        
    def plot_1d_projection(self, map, plot_axis,ptype='hist', **kwargs):
        ''' plot map projected on plot_axis'''
        axis = plt.gca()
        plt_binning = map.binning[plot_axis]
        hist = self.project_1d(map, plot_axis)
        if ptype == 'hist':
            axis.hist(plt_binning.bin_centers, weights=unp.nominal_values(hist), bins=plt_binning.bin_edges, histtype='step', lw=1.5, label=r'$%s$'%map.tex, **kwargs)
            axis.bar(plt_binning.bin_edges.m[:-1],2*unp.std_devs(hist),
                    bottom=unp.nominal_values(hist)-unp.std_devs(hist),
                    width=plt_binning.bin_widths, alpha=0.25, linewidth=0)
        elif ptype == 'data':
            axis.errorbar(plt_binning.bin_centers.m,
                    unp.nominal_values(hist),yerr=unp.std_devs(hist), fmt='o', markersize='4', label=r'$%s$'%map.tex, **kwargs)
        axis.set_xlabel(plt_binning.label)
        if self.label:
            axis.set_ylabel(self.label)
        if plt_binning.is_log:
            axis.set_xscale('log')
        if self.log:
            axis.set_yscale('log')
        axis.set_xlim(plt_binning.bin_edges.m[0], plt_binning.bin_edges.m[-1])
        if self.grid:
            plt.grid(True, which="both", ls='-', alpha=0.2)

    def project_1d(self, map, plot_axis):
        ''' sum up a map along all axes except plot_axis '''
        hist = map.hist
        plt_axis_n = map.binning.names.index(plot_axis)
        for i in range(len(map.binning)):
            if i == plt_axis_n:
                continue
            hist = np.sum(map.hist, i)
        return hist

    def plot_1d_ratio(self, maps, plot_axis):
        ''' make a ratio plot for a 1d projection '''
        axis = plt.gca()
        map0 = maps[0]
        plt_binning = map0.binning[plot_axis]
        hist = self.project_1d(map0, plot_axis)
        hist0 = unp.nominal_values(hist)
        err0 = unp.std_devs(hist)

        axis.set_xlim(plt_binning.bin_edges.m[0], plt_binning.bin_edges.m[-1])
        maximum = 1.0
        minimum = 1.0
        for j,map in enumerate(maps):
            hist = self.project_1d(map, plot_axis)
            hist1 = unp.nominal_values(hist)
            err1 = unp.std_devs(hist)
            ratio = np.zeros_like(hist0)
            ratio_error = np.zeros_like(hist0)
            for i in range(len(hist0)):
                if hist1[i]==0 and hist0[i]==0:
                    ratio[i] = 1.
                    ratio_error[i] = 1.
                elif hist1[i]!=0 and hist0[i]==0:
                    logging.warning('deviding non 0 by 0 for ratio')
                    ratio[i] = 0.
                    ratio_error[i] = 1.
                else:
                    ratio[i] = hist1[i]/hist0[i]
                    ratio_error[i] = err1[i]/hist0[i]
                    minimum = min(minimum,ratio[i])
                    maximum = max(maximum,ratio[i])

            h,b,p = axis.hist(plt_binning.bin_centers, weights=ratio,
                    bins=plt_binning.bin_edges, histtype='step', lw=1.5,
                    label=r'$%s$'%map.tex)
            axis.bar(plt_binning.bin_edges.m[:-1],2*ratio_error, bottom=ratio-ratio_error,
                    width=plt_binning.bin_widths, alpha=0.25,
                    linewidth=0)

        if self.grid:
            plt.grid(True, which="both", ls='-', alpha=0.2)
        self.fig.subplots_adjust(hspace=0)
        axis.set_ylabel('ratio')
        axis.set_xlabel(plt_binning.label)
        # calculate nice scale:
        off = max(maximum-1, 1-minimum)
        axis.set_ylim(1 - 1.2 * off, 1 + 1.2 * off )