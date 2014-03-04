#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
import colorbrewer

WORKDIR = '/Users/ricardo/lumo/loadtest/beeswithmachineguns'
CSV_DIR = 'csv_files'
FIGS_DIR = 'figs2'
EXTENSION = '2.csv'
FIG_FORMAT = 'pdf'
ROUTES = ['own',
          'upload_owner_metadata',
          'checklogin',
          'download_owner_metadata',
          'get_commands',
          'check_firmware',
          'stats_aggregate',
          'stats_lumo_goals',
          'upload_device_diagnostics',
          'upload_activities']
#
X_LABEL = 'b_p'
Y_LABEL = 'b_p / resp_time'
LABELS = ('$50\%$', '$90\%$')
# The number of servers (bees) to start
SERVERS = 4
# The number of total connections to make to the target
NUMBER = 10000
# The number of concurrent connections to make to the target
CONCURRENT = [10, 25, 50, 75, 100, 150, 200, 250, 350, 500]
#[10, 50, 100, 250, 500]
#
PERCENTILES = [49, 89]

_dir = '/'.join((WORKDIR, CSV_DIR))
data = np.array([[c/SERVERS*SERVERS*1000 / np.loadtxt(
    '/'.join((_dir, route, ('s%dn%dc%d.%s' %
                            (SERVERS, np.log10(NUMBER), c, EXTENSION)))),
    delimiter=',', skiprows=1)[PERCENTILES,1]
               for c in CONCURRENT] for route in ROUTES])

x = np.array(CONCURRENT)/SERVERS*SERVERS

# auxiliary function
def save_fig(prefix, suffix):
    _dir = '/'.join((WORKDIR, FIGS_DIR))
    plt.xlabel(X_LABEL)
    plt.ylabel(Y_LABEL)
    plt.title(suffix)
    fname = '-'.join((prefix, suffix))
    fname = '/'.join((_dir, fname))
    fname = '.'.join((fname, FIG_FORMAT))
    plt.savefig(fname)
    plt.close()

# one plot for each route/endpoint
for y, route in zip(data, ROUTES):
    # line plot
    fig = plt.figure()
    plt.plot(x, y)
    plt.legend(LABELS, loc=0)
    save_fig('plot', route)

    # bar plot
    fig = plt.figure()
    width = 6
    plt.bar(x, y.T[1], width, color='r', label=LABELS[1])
    plt.bar(x, y.T[0] - y.T[1], width, y.T[1], color='g', label=LABELS[0])
    plt.legend(loc=0)
    save_fig('bar', route)

# all routes in one plot
colormap = np.array(colorbrewer.Paired[10])/255.
for y, label in zip(data.T, LABELS):
    fig = plt.figure(figsize=(16, 8.95))
    lines = plt.plot(x, y)
    [l.set_color(color) for l,color in zip(lines, colormap)]
    plt.legend(ROUTES)
    save_fig('plot-all_routes', label)

# bar chart
width = 1.2
n_bars = len(ROUTES)
bar_xoffset = n_bars/2.
fig = plt.figure(figsize=(16, 8.95))
[plt.bar(x + (i-bar_xoffset)*width, y.T[1], width, color='r')
 for i, y in enumerate(data)]
[plt.bar(x + (i-bar_xoffset)*width, y.T[0] - y.T[1], width, y.T[1], color='g')
 for i, y in enumerate(data)]
save_fig('bar-all_routes', '50_and_90')
