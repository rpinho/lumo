#!/usr/bin/env python
#!/usr/bin/python

import sys
import os
import operator
#from itertools import *
from pylab import *
import numpy.ma.mrecords as mrecords
from scipy import stats
from scipy.stats import kstest
from scikits import bootstrap
from sklearn import linear_model

# plotting labels
x_label = 'Normalized Days of Usage'
y_label = 'Metric Value'
_title = 'Metric Over Time'

# plotting parameters
figs_dir = 'figs/'
screen_size  = {'macbook': (16., 8.775), 'imac': (24., 13.775), None:None}
#figsize = screen_size['macbook']
figsize = (9., 7.)

# data file/table parameters
_dir = '/Users/ricardo/lumo/birmingham/marketing_study/data_pull_20131014/datasets/'

# convert string to floats
general_converters = {'gender': lambda s: s == 'm',
                      'local_date': datestr2num}
#                     'owner': unique_owners.index}

# auxiliary functions
def confidence_interval(
        data, statfunction=ma.mean, alpha=0.05, n_samples=10000,
        output='errorbar'):#'lowhigh'):
    return bootstrap.ci(data, statfunction, alpha, n_samples, output=output)

def ensure_dir_exists(_dir):
    if (not os.path.exists(_dir)):
        os.makedirs(_dir)

def get_headers(filename):
    # get headers/column names
    _file = open(filename)
    headers = _file.readline().split(',')
    _file.close()
    return headers

def add_general_converter(converters, filename, field):
    # get headers/column names
    headers = get_headers(filename)
    try:
        field_i = headers.index(field)
    except:
        pass#return converters
    else:
        converters[field_i] = general_converters[field]

def add_owner_converter(converters, filename, field='owner'):
    # get headers/column names
    headers = get_headers(filename)
    owner_i = headers.index(field)

    # get owners
    all_owners = loadtxt(
        filename, str, delimiter=',', skiprows=1, usecols=(owner_i,))
    unique_owners = unique(all_owners)#set()

    # convert string to floats
    converters[owner_i] = list(unique_owners).index
    return unique_owners

#fname = 'R-normalized-p_posture-st_f_owner_age_range(26, 35).csv'
def get_data_record(fname, logfile=None, fields=('gender', 'local_date')):

    filename = _dir + fname
    if '.csv' not in filename:
        filename += '.csv'

    converters = {}
    [add_general_converter(converters, filename, field) for field in fields]
    unique_owners = add_owner_converter(converters, filename)

    # read from csv
    data = genfromtxt(
        filename, delimiter=',', converters=converters, names=True,
        usemask=True)

    data = data.view(mrecords.mrecarray)

    data.unique_owners = unique_owners
    data.n_owners = len(unique_owners)
    set_owner_i(data)
    set_max_shared_days(data)

    output = ('n_owners: %s, n_days: %s, data.size: %s' %
              (data.n_owners, data.n_days, data.size))
    if logfile:
        print >> logfile, output
    else:
        print output

    return data


# where is owner i?
def set_owner_i(data):
    data.owner_i = array([where(data.owner == i)[0]
                          for i in range(data.n_owners)])

def set_max_shared_days(data):
    t_max = int(data.row_number.max())
    t = array([nonzero(data.row_number == t)[0].size for t in range(1, t_max)])
    data.n_days = nonzero(t == data.n_owners)[0][-1]

def get_threshold(data, bins=arange(0,1,.1)):
    return array([[data.metric_val[data.row_number == day] > threshold
                   for day in range(1, data.n_days+1)]
                  for threshold in bins])

def get_ythreshold(y, threshold):
    return y > threshold

def plot_threshold(y):
    # mean
    fig = figure()
    plot(y.mean(axis=2).T)

    # or regression
    fig = figure()
    y = array([linear_fit(x) for x in y])
    plot(y.T)

def linear_fit(
        y, logfile=None, i=0, _dir=figs_dir, fig=None, owners=[],
        color='k', _plotting=True, _save=True, figname=''):

    # reshape
    M, N = y.shape
    x = array(range(1,M+1) * N)#.reshape
    y = y.flatten()

    # linear regression
    #m, c = ma.polyfit(x[~y.mask], y[~y.mask], 1) # ma. is not working
    #print m, c

    # or
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        x[~y.mask], y[~y.mask])

    if not _plotting:
        print slope, intercept, r_value, r_value**2, p_value, std_err

    if p_value <= .05:
        output = ('percentile=%d, n_samples=%d, slope=%.2f, p_value=%.2g' %
                  (i, N, slope, p_value))
        if logfile:
            print >> logfile, _dir.split('/')[-2]
            print >> logfile, output
            print >> logfile, owners
        else:
            print output

    m, c = slope, intercept

    # or
    #A = vstack([x, ones(len(x))]).T
    #m, c = lstsq(A[~y.mask], y[~y.mask])[0]
    #print m, c

    # or
    #clf = linear_model.LinearRegression()
    #clf.fit(A[~y.mask], y[~y.mask])
    #m, c = clf.coef_[0], clf.intercept_
    #print m, c

    if _plotting:
        if not fig:
            fig = figure(figsize=figsize)

        # scatter data
        plot(x, y, '.', c=color, alpha=.5)

        # regression
        x = x[:M]
        y = m*x + c
        plot(x, y, c=color)

        # set_plot_kwargs
        xlabel(x_label)
        ylabel(y_label)
        title(('percentile=%d, n_samples=%d' %(i, N) +
               '\nslope=%.2g, intercept=%.2g, r_value=%.2g\n' %
               (slope, intercept, r_value) +
               'r^2=%.2g, p_value=%.2g, std_err=%.2g' %
               (r_value**2, p_value, std_err)))

        if _save:
            ensure_dir_exists(_dir)
            if not figname:
                figname = 'percentile=%d, n_samples=%d' %(i, N)
            savefig(_dir + figname + '.pdf')
            close()
    return y

def get_y0(data):
    return [data.metric_val[owner][data.metric_val[owner].nonzero()[0][0]]
            for owner in data.owner_i]

def get_y_by_owner(data):
    y = [data.metric_val[owner][:data.n_days] for owner in data.owner_i]
    return ma.masked_invalid(y)

def normalize_y_by_y0(data):
    y = get_y_by_owner(data)
    y0 = reshape(get_y0(data), (data.n_owners, 1))
    return y-y0

def normalize_y_by_mean_std(data):
    y = get_y_by_owner(data)
    return ((y - y.mean(axis=1).reshape(len(y),1)) /
            y.std(axis=1).reshape(len(y),1))

def get_initial_bins(data):
    #t0 = [data.metric_val[owner].nonzero()[0][0] for owner in data.owner_i]
    y0 = get_y0(data)
    prc0 = [stats.percentileofscore(data.metric_val, i) for i in y0]
    return digitize(prc0, range(0,101,10))

# percentile 1: stats.mstats.scoreatpercentile(data.metric_val, 10) = 0.2
def get_initial_percentile(data, y=None):
    bins = get_initial_bins(data)
    if not any(y):
        y = get_y_by_owner(data)
    return [ma.masked_invalid([x for i, x in enumerate(y) if bins[i] == bin])
            for bin in range(1,10)]

    '''t0 = data.row_number == 1
    try:
         y = [stats.percentileofscore(data.metric_val, i)
              for i in data.metric_val[t0]]
    except:
        t1 = data.row_number == 2

#
_percentile = stats.mstats.scoreatpercentile
pct = array([[_percentile(data.metric_val[data.row_number == day], pct)
              for day in range(1, n_days+1)]
             for pct in range(0,101,10)])
'''
def plot_boxplot(y, _dir, _save=True):
    fig = figure(figsize=figsize)
    boxplot(list(y.T))
    xlabel(x_label)
    ylabel(y_label)
    _title = ', '.join(_dir.split('/')[1:-1])
    title(_title)
    if _save:
        ensure_dir_exists(_dir)
        savefig(_dir + 'boxplot.pdf')
    return fig#close()

'''
d = array([y[i][a_mask[i]][-1] - y[i][a_mask[i]][0] for i in o_i])
d = list(itertools.chain.from_iterable(d1))
d = ma.masked_invalid(d)
bootstrap.ci(d.compressed(), ma.mean)
'''

def main(fname, logfile):

    print >> logfile, '\n', fname

    save_dir = figs_dir + fname + '/'
    # create dir with fname to save figs
    ensure_dir_exists(save_dir)

    # read and parse data
    data = get_data_record(fname, logfile)

    # metric per owner, not normed
    _dir = save_dir + 'not_normed/'
    #print >> logfile, 'not_normed'
    y = get_y_by_owner(data)

    # boxplot
    fig = plot_boxplot(y, _dir, _save=False)

    # all data
    linear_fit(y.T, logfile, 0, _dir, fig, data.unique_owners)

    # conditioned initial percentiles
    y = get_initial_percentile(data)
    [linear_fit(x.T, logfile, i+1, _dir)
     for i, x in enumerate(y) if any(x)]

    # normed by initial posture
    _dir = save_dir + 'normed_by_initial/'
    #print >> logfile, 'normed_by_initial'
    y = normalize_y_by_y0(data)

    # boxplot
    fig = plot_boxplot(y, _dir, _save=False)

    # all data
    linear_fit(y.T, logfile, 0, _dir, fig, data.unique_owners)

    # conditioned initial percentiles
    y = get_initial_percentile(data, y)
    [linear_fit(x.T, logfile, i+1, _dir)
     for i, x in enumerate(y) if any(x)]

    # normalized by mean and scale
    _dir = save_dir + 'mean_normalized/'
    #print >> logfile, 'mean_normalized'
    y = normalize_y_by_mean_std(data)

    # boxplot
    fig = plot_boxplot(y, _dir, _save=False)

    # all data
    linear_fit(y.T, logfile, 0, _dir, fig, data.unique_owners)

    # conditioned initial percentiles
    y = get_initial_percentile(data, y)
    [linear_fit(x.T, logfile, i+1, _dir)
     for i, x in enumerate(y) if any(x)]

if __name__ == "__main__":
    name = sys.argv[1]

    # write some things to a log file
    logfile = open(name + '.log',  "a")
    print >> logfile, '\nprinting to log (from %s)' % name

    for fname in os.listdir(_dir):
        if name in fname:
            main(fname, logfile)

    logfile.close()
