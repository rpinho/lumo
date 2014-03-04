import numpy.ma.mrecords as mrecords

# table
_dir = ''
fname = _dir + 'st_user_statistics.csv'

# get headers/column names
_file = open(fname)
headers = _file.readline().split(',')

# get owners
owner_i = 7
all_owners = loadtxt(fname, str, delimiter=',', skiprows=1, usecols=(owner_i,))
unique_owners = list(set(all_owners))
print len(unique_owners)

# convert string to floats
date_i = 2
converters = {date_i: datestr2num, owner_i: unique_owners.index}

# read from csv
data = genfromtxt(
    fname, delimiter=',', converters=converters, names=True, usemask=True)

# headers again (redundant)
headers = data2.dtype.names

# sort by owner, date
data = sort(data, order=('owner', 'local_date'))

# sorted records array object
#data_rec = data.view(np.recarray)
data_rec = data.view(mrecords.mrecarray) # masked

# get (x, y) as (time, posture_score) for each user
# TODO: clean up this part in a more efficient way
n_owners = unique(data_rec.owner).size
owner_i = array([where(data_rec.owner == i)[0] for i in range(n_owners)])
post_t = array([(data_rec.local_date[i],
                 data_rec.p_posture_enum[i] / data_rec.p_posture_denom[i])
                for i in owner_i])
t, p = post_t.T

# let's filter to time > Juy 1st
start_date = '2013-08-28'#'2013-06-01'
end_date = '2013-10-02'#'2013-08-13'
#time_mask = [data_rec.local_date[i] > start_date for i in owner_i]
time_mask = [(data_rec.local_date[i] > datestr2num(start_date)) &
             (data_rec.local_date[i] < datestr2num(end_date))
             for i in owner_i]
#t_filtered = [x[mask] for x, mask in zip(t, time_mask)]
p_filtered = [x[mask] for x, mask in zip(p, time_mask)]

# all data flattened
all_postures = ma.masked_invalid(list(flatten(p_filtered)))

# difference between first and last points
diff = ma.masked_invalid([x[-1] - x[0] for x in p_filtered if len(x)>1])
