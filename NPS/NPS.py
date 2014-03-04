from csv import DictReader
from operator import itemgetter
from urllib import urlopen
from numpy import *
from numpy.random import *
from pylab import *
from sklearn import preprocessing
from sklearn.feature_extraction import DictVectorizer
import pandas

CSV_FILE = 'NPS_2013-10-21-no_header.csv'
EXCEL_FILE = 'NPS_2013-10-21.xls'
HEADERS_FILE = 'fieldnames.txt'
LOCATION_FILE = 'location.csv' # with IP already converted to location
COMMENTS = 'additional comments\n' #'Open-Ended Response'
N_COL = 68
# multiple choice-type questions start at ind=11
INDICES = {'IP':(4,), 'email':(5,8), 'NPS':(9,), 'choose':11}
MAX_N_CLASSES = 7 # maximum number of categories to be considered

# auxiliary_functions
def add_random_noise(x, noise=0.2):
    return x + noise*rand() - .1

# TODO: try use panda for parsing
def get_data_frame(fname=EXCEL_FILE):
    """ requires pandas

    """
    return pandas.read_excel(fname, 'Sheet1')

def get_categorical_data_dict(fname=CSV_FILE, fieldnames=range(N_COL)):
    """ requires csv

    """
    # get categorical columns
    cols = get_classes_ind()
    valuesfor = itemgetter(*cols)
    # the 'U' flag is mandatory for Excel export. see:
    # http://stackoverflow.com/questions/6726953/open-the-file-in-universal-newline-mode-using-csv-module-django
    with open(fname, 'rU') as csvfile:
        reader = DictReader(csvfile, fieldnames)
        return array([dict(zip(cols, valuesfor(row))) for row in reader])

# NOTE: transforms to binary only
# TODO: implement categorical transform
def dict_vectorizer(fname=CSV_FILE):
    """ requires sklearn, numpy

    """
    data = get_categorical_data_dict(fname).view(recarray)
    vec = DictVectorizer()
    # not sure how to preprocess missing data using csv.DictReader()
    # so i'm doing this ad-hoc by hand
    ind = append(range(1,(60-11)*2,2), [99,100,102,103,104,105,106])
    data.binary = vec.fit_transform(data).toarray()[:,ind]
    data.names = array(vec.get_feature_names())[ind]
    return data

#def get_converters():
#    converters = {2: datestr2num,
#                  3: datestr2num,
#                  4: str, #IP
#                  5: str, #email
#                  8: str, #email
#                  63: parse_yes_or_no_question}
#    #str2bool = bool
#    choice_type_questions = range(11,22) + range(23,44) + range(45,62)
#    #free_coment_questions
#    converters.update(dict(zip(range(10,68), [bool]*1000)))

#**kwargs for genfromtxt()
#def get_kwargs():
#    return dict(delimiter=",",
#                #dtype=int,
#                #names="a,b,c",
#                #missing_values={0:"N/A", 'b':" ", 2:"???"},
#                filling_values=0)

# IP
# NOTE: SLOW! (live url requests)
# TODO: try different IP APIs to complete missing values
#       actually, use 'st_shipping_data' table from adminer_follow
#       or 'st_v_marketing_user_data' which already has owner metadata
def parse_IPs(
        fname=CSV_FILE, IP_i=INDICES['IP'], location_file=LOCATION_FILE):
    """ requires sklearn, urllib, numpy
    returns records.recarray

    """
    all_ips = loadtxt(fname, str, delimiter=',', usecols=IP_i)
    try:
        location = loadtxt(
            location_file, str, delimiter=', ', skiprows=1, unpack=True)
    except:
        responses = [urlopen(
            'http://api.hostip.info/get_html.php?ip=%s&position=true'%ip)
                     for ip in all_ips]
        country = parse_countries(responses)
        city, state = parse_cities(responses)
    else:
        country, city, state = location

    # records.recarray to hold categorical and binary data
    # delete missing values with tuple (0,) or (0,1)
    data = all_ips.view(recarray)
    data.country = label_encoding_binarization(country)#, (0,))
    data.city = label_encoding_binarization(city)#, (0,1))
    data.state = label_encoding_binarization(state)#, (0,))
    return data

def parse_countries(responses):
    countries = [r.next() for r in responses]
    countries = [country.lstrip('Country:').lstrip().rstrip('\n')
                 for country in countries]
    return array(countries)

def parse_cities(responses):
    cities_and_states = [r.next() for r in responses]
    cities_and_states = [city.lstrip('City:').lstrip().rstrip('\n').split(', ')
                         for city in cities_and_states]
    cities = []
    states = []
    for x in cities_and_states:
        city = x[0]
        # foreign cities don't have state info
        state = x[1] if len(x) > 1 else ''
        cities.append(city)
        states.append(state)
    return array(cities), array(states)

def parse_emails(fname=CSV_FILE, email_i=INDICES['email']):
    emails = loadtxt(fname, str, delimiter=',', usecols=email_i)
    return array([x + y for x, y in emails])

def get_nps_score(fname=CSV_FILE, NPS_i=INDICES['NPS']):
    nps = loadtxt(fname, int, delimiter=',', usecols=NPS_i)
    return nps, nonzero(nps > 8)[0].size - nonzero(nps < 7)[0].size

def get_n_classes(fname=CSV_FILE):
    data = loadtxt(fname, str, delimiter=',')
    return array([unique(x).size for x in data.T])

def get_classes_ind(threshold=MAX_N_CLASSES, start=INDICES['choose']):
    n_classes = get_n_classes()
    return nonzero(n_classes[start:] < threshold)[0] + start

def get_fieldnames(fname=HEADERS_FILE):
    with open(fname) as f:
        return f.readlines()

def get_fieldnames_ind():
    fieldnames = get_fieldnames()
    return zip(range(len(fieldnames)), fieldnames)

def get_free_comments_ind():
    fieldnames = get_fieldnames()
    return nonzero(array(fieldnames) == COMMENTS)[0]

# transforms array into recarray
def label_encoding_binarization(data, missing_values=(0,)):
    le = preprocessing.LabelEncoder()
    le.fit(data)
    data = data.view(recarray)
    data.names = le.classes_
    data.categorical = le.transform(data)
    lb = preprocessing.LabelBinarizer()
    data.binary = lb.fit_transform(data.categorical)
    return data

def read_parse_data(fname=CSV_FILE):
    data = loadtxt(fname, str, delimiter=',')
    data = data.view(recarray)
    data.names = get_fieldnames()
    data.location = parse_IPs(fname)
    data.email = parse_emails(fname)
    data.y, data.nps = get_nps_score(fname)
    data.choice = dict_vectorizer(fname)
    data.free_coments_ind = get_free_comments_ind()
    return data

def scatter_plot(data):
    """ example scatter plot

    """
    # x is categorical city data
    x = data.location.city.categorical
    # mask '(Unknown City?)' and '(Unknown city)'
    x = ma.array(x, mask=(x==0) | (x==1))
    x = map(add_random_noise, x)
    fig = figure()
    plot(x, data.y, '.', alpha=.5)
    return fig
