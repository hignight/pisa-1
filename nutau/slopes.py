from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import numpy as np
from numpy.polynomial.polynomial import polyval
from scipy.optimize import curve_fit
from scipy import interpolate

from pisa import ureg, Q_
from pisa.core.distribution_maker import DistributionMaker
from pisa.utils.fileio import from_file, to_file
from pisa.utils.log import set_verbosity
from pisa.utils.parse_config import parse_config
from pisa.utils.plotter import plotter
from pisa.core.map import MapSet

parser = ArgumentParser()
parser.add_argument('-t', '--template-settings', type=str,
                    metavar='configfile', required=True,
                    help='settings for the generation of templates')
parser.add_argument('-p', '--plot', action='store_true',
                    help='plot')
parser.add_argument('-v', action='count', default=None,
                    help='set verbosity level')
args = parser.parse_args()
set_verbosity(args.v)

degree = 2
force_through_nominal = False

if args.plot: 
    import matplotlib.pyplot as plt

template_maker_settings = from_file(args.template_settings)
template_maker_configurator = parse_config(template_maker_settings)
template_maker = DistributionMaker(template_maker_configurator)

path = '/Users/peller/PSU/cake/nutau/event_files/'
fname_s = 'events__deepcore__IC86__runs_12%s1-12%s3,14%s1-14%s3,16%s1-16%s3__proc_v5digit__'
fname_unjoined = 'unjoined.hdf5'
fname_joined = 'joined_G_nue_cc+nuebar_cc_G_numu_cc+numubar_cc_G_nutau_cc+nutaubar_cc_G_nuall_nc+nuallbar_nc.hdf5'

pname = 'dom_eff'
nominal = 1.0
runs = [('601', 0.88), ('603', 0.94), ('604', 0.97), ('605', 1.03), ('606', 1.06), ('608', 1.12)]

x_values = np.array(sorted([r[1] for r in runs] + [nominal]))

cscd = {}
trck = {}

# get templates
template = template_maker.get_outputs()
cscd[nominal] = sum([map.hist for map in template if map.name.endswith('cscd')])
trck[nominal] = sum([map.hist for map in template if map.name.endswith('trck')])

for run, value in runs:
    # adjust params
    param = template_maker.params['aeff_weight_file']
    param.value = path + fname_s%(tuple([run]*6)) + fname_unjoined
    param.set_nominal_to_current_value()
    template_maker.update_params(param)
    param = template_maker.params['reco_weight_file']
    param.value = path + fname_s%(tuple([run]*6)) + fname_joined
    param.set_nominal_to_current_value()
    template_maker.update_params(param)
    param = template_maker.params['pid_events']
    param.value = path + fname_s%(tuple([run]*6)) + fname_joined
    param.set_nominal_to_current_value()
    template_maker.update_params(param)
    # retreive maps
    template = template_maker.get_outputs()
    cscd[value] = sum([map.hist for map in template if map.name.endswith('cscd')])
    trck[value] = sum([map.hist for map in template if map.name.endswith('trck')])

cscd_array = []
trck_array = []
for x in x_values:
    cscd_array.append(cscd[x]/cscd[nominal])
    trck_array.append(trck[x]/trck[nominal])

cscd_array = np.array(cscd_array).transpose(1,2,0)
trck_array = np.array(trck_array).transpose(1,2,0)

cscd_slopes = np.ones_like(cscd[nominal])
nx, ny = cscd_slopes.shape
bins_x = np.arange(nx)
bins_y = np.arange(ny)

grid_x, grid_y = np.meshgrid(bins_x, bins_y)

grid_x = np.ravel(grid_x)
grid_y = np.ravel(grid_y)

# shift to get deltas
x_values -= nominal

# fix point poly definition
if force_through_nominal:
    fit_fun = lambda x, *p: polyval(x, [1.] + list(p))
else:
    fit_fun = lambda x, *p: polyval(x, list(p))

for i, j in np.ndindex(cscd_slopes.shape):
    y_values = cscd_array[i,j,:]
    popt, pcov = curve_fit(fit_fun, x_values,
            y_values, p0=np.ones(degree))
    cscd_slopes[i,j] = popt[0]
    if args.plot:
        fig_num = i + nx * j
        if fig_num == 0:
            fig = plt.figure(num=1, figsize=( 4*nx, 4*ny))
        subplot_idx = nx*(ny-1-j)+ i + 1
        plt.subplot(ny, nx, subplot_idx)
        plt.scatter(x_values, y_values, color='blue')
        f_values = fit_fun(x_values, *popt)
        fun_plot, = plt.plot(x_values, f_values,'k-')
        plt.ylim(np.min(cscd_array)*0.9, np.max(cscd_array)*1.1)
        if i > 0:
            plt.setp(plt.gca().get_yticklabels(), visible=False)
        if j > 0:
            plt.setp(plt.gca().get_xticklabels(), visible=False)

if args.plot:
    fig.subplots_adjust(hspace=0)
    fig.subplots_adjust(wspace=0)
    plt.show()
    plt.savefig('cscd.pdf')



#spline = interpolate.SmoothBivariateSpline(grid_x, grid_y,
#        np.ravel(cscd_slopes), kx=2, ky=2)
#smooth = spline(bins_x, bins_y)

#plt.imshow(smooth,interpolation='nearest')
