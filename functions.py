from pylab import *
from itertools import *

# from http://docs.python.org/release/2.3.5/lib/itertools-example.html
def window(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result

# (max, min) moving window
def non_sliding_window(
        data, windows=range(1,30), window_func=array_split):
    fig = figure()
    for window in windows:
        all_max = ma.masked_invalid([[x.max()
                                      for x in window_func(user, window)]
                                     for user in data if len(user) > window])
        all_avg = ma.masked_invalid([[x.mean()
                                      for x in window_func(user, window)]
                                     for user in data if len(user) > window])
        all_mdn = ma.masked_invalid([[ma.median(x)
                                      for x in window_func(user, window)]
                                     for user in data if len(user) > window])
        all_min = ma.masked_invalid([[x.min()
                                      for x in window_func(user, window)]
                                     for user in data if len(user) > window])
        n_samples = ma.masked_invalid([[x.size
                                        for x in window_func(user, window)]
                                       for user in data if len(user) > window])
        plot(all_max.mean(axis=0), 'g')
        plot(all_avg.mean(axis=0), 'k')
        plot(all_mdn.mean(axis=0), 'k--')
        plot(all_min.mean(axis=0), 'r')
    return fig, n_samples

# TODO: not working.
# Cannot do mean(axis=0) or even cast to masked_array because
# different number of windows
def sliding_window(data, fig, w_size=2, window_func=window):

    all_max = ma.masked_invalid([[ma.masked_invalid(x).max()
                                  for x in window_func(user, window)]
                                 for user in data if len(user) > window])

    all_max = [
        ma.masked_invalid(list(window_func(user, w_size))).max(axis=1)
        for user in data if len(user) > w_size]

    all_mean = ma.masked_invalid([
        ma.masked_invalid(list(window_func(user, w_size))).mean(axis=1)
        for user in data if user.size > w_size])

    all_mdn = ma.masked_invalid([
        ma.median(ma.masked_invalid(list(window_func(user, w_size))), axis=1)
        for user in data if user.size > w_size])

    all_min = ma.masked_invalid([
        ma.masked_invalid(list(window_func(user, w_size))).min(axis=1)
        for user in data if user.size > w_size])

    plot(all_max.mean(axis=0), 'g')
    plot(all_avg.mean(axis=0), 'k')
    plot(all_mdn.mean(axis=0), 'k--')
    plot(all_min.mean(axis=0), 'r')
    return fig
