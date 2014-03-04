#!/usr/bin/env python

import sys, os
from functools import partial
import cProfile
import pstats
import requests

ENDPOINT = os.environ['LUMO_ENDPOINT']

# GUNICORN
LIMIT_REQUEST_LINE = 4094
LIMIT_DIAG = 40
LIMIT_ACT = 20

# USER METADATA
N_USER = 100
GENERIC_OWNER_NAME = "loadtest"
GENERIC_OWNER_DOMAIN = "@lumoback.com"
GENERIC_PASSWD = "whatever"
GENERIC_SENSOR_ID = "deadbeef_"
GENERIC_METADATA = ('"bdate":"1970-2-15", "height":180, "weight":80,' +
                    '"gender":"male", "set_standing_desk":1,' +
                    '"fname":"Joe","lname":"Schmoe","app_rated":1')

# FIRMWARE
REVISION = '100001'
APP_VERSION = '2.0'

# STATS
METRICS = ('n_steps', 'n_sittime', 'n_standups', 'p_posture')
TLOCAL = '1372377300'
GRANULARITY = 'day'
PEER_GROUP = 'all'

# DIAG
N_DIAG = 500
DIAG_MSG = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# ACT
N_ACT = 1500
ACT = "W"
DELTA = 300
PCT = 5
#SENSOR_ID = "21e92c362a9a4404bab3be573b85ead7"
T_MIN = 1000000000

# AUXILIARY FUNCTIONS
def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def print_id(n):
    """ Display number with leading zeros
    """
    return "%03d" %n

def print_login(n):
    return GENERIC_OWNER_NAME + print_id(n) + GENERIC_OWNER_DOMAIN

def print_sensor_id(n):
    return GENERIC_SENSOR_ID + print_id(n)

def print_metadata(owner, passwd):
    return ('{"records":[' +
            '{"owner":"%(owner)s", "passwd":"%(passwd)s", '%locals() +
            '%(GENERIC_METADATA)s}]}' %globals())

def print_trash_diagnostic(n):
    return '{"diag":"%s %s"}' %(print_id(n), DIAG_MSG)

def print_diagnostics(diagnostics_id):
    day_diagnostics = (print_trash_diagnostic(i)
                       for i in diagnostics_id)
    return '{"records":[%s]}' %','.join(day_diagnostics)

def print_trash_activity(t, sensor_id):
    return ('{"act":"%(ACT)s","delta":%(DELTA)s,"pct":%(PCT)s,' %globals() +
            '"received_in_bg":true,' +
            '"sensor_id":"%(sensor_id)s","t":%(t)s,"tlocal":%(t)s}' %locals())

def print_activities(user, activity_times):
    day_activities = (print_trash_activity(t, user.sensor_id)
                      for t in activity_times)
    return '{"records":[%s]}' %','.join(day_activities)

def print_params(params):
    params = map('='.join, params.items())
    return '&'.join(params)

def print_url(route, params, endpoint=ENDPOINT):
    params = print_params(params)
    return endpoint + '?'.join((route, params))

def print_urls(route_function, n_users=10):
    return ','.join((print_url(*route_function(User(i)))
                     for i in range(1, n_users+1)))

def post(route, params, endpoint=ENDPOINT, verbose=True):
    response = requests.post(endpoint + route, params=params)
    if verbose:
        print response.ok, response.text
    return response

# ----------------------
# Go through the flow below for 100 users
# loadtest001@lumoback.com ... loadtest100@lumoback.com

class User:
    def __repr__(self):
        return str(self.__dict__)

    def __init__ (self, i):
        self.login = print_login(i)
        self.passwd = GENERIC_PASSWD
        self.sensor_id = print_sensor_id(i)
        self.metadata = print_metadata(self.login, self.passwd)
        self.revision = REVISION
        self.base_revision = REVISION
        self.app_version = APP_VERSION

# Use the same diagnostics/acitvity data every time

# To make a user/sensor:
# ----------------------
# retval = "OK:new_sensor_owned_insert" or 'OK:you_own_sensor_already'
def own_sensor(user, http_func=post):
    route = '/own'
    params = {'login':user.login,
              'passwd':user.passwd,
              'sensor_id':user.sensor_id}
    return http_func(route, params)

# To set the user metadata:
# --------------------------
# retval: "wrote metadata for %s"
def upload_metadata(user, http_func=post):
    route = '/upload'
    params = {'owner_metadata':user.metadata}
    return http_func(route, params)

# Typical flow of app request to the back end:
# ==============================================

# (1) Check Login
# retval: "OK:password for login %s matches"
def check_login(user, http_func=post):
    route = '/checklogin'
    params = {'login':user.login,
              'passwd':user.passwd,
              'sensor_id':user.sensor_id}
    return http_func(route, params)

# (2) Get user metadata
# retval: '{"records":}
def download_metadata(user, http_func=post):
    route = '/download'
    params = {'type':'owner_metadata',
              'login':user.login,
              'passwd':user.passwd}
    return http_func(route, params)

# (3) Download commands
# response.text = '["LOGGING_OFF","ON","BPSM:1"]'
def get_commands(user, http_func=post):
    route = '/get_commands'
    params = {'login':user.login,
              'passwd':user.passwd}
    return http_func(route, params)

# (4) Check Firmware
# response.text = '{"NEW_FIRMWARE_REVISION": {"plugin":102195,"base":102127}}'
def check_firmware(user, http_func=post):
    route = '/check_firmware'
    params = {'login':user.login,
              'passwd':user.passwd,
              'revision':user.revision,
              'base_revision':user.base_revision,
              'app_version':user.app_version}
    return http_func(route, params)

# (5) Get average data for max cards, one for each of 4 cards (not for sleep)
# response.text = '{"val":26557.292453,"local_date":"2013-06-27"}' for e.g.
def stats_aggregate(user, metric, http_func=post):
    route = '/stats_aggregate'
    params = {'login':user.login,
              'passwd':user.passwd,
              'tlocal':TLOCAL,
              'granularity':GRANULARITY,
              'metric':metric,
              'peer_group':PEER_GROUP}
    return http_func(route, params)

# (6) Get personal goals
# response.text = {"val": 484.0, "local_date": "2013-06-27"}' for e.g.
def stats_lumo_goals(user, metric, http_func=post):
    route = '/stats_lumo_goals'
    params = {'login':user.login,
              'passwd':user.passwd,
              'tlocal':TLOCAL,
              'granularity':GRANULARITY,
              'metric':metric}
    return http_func(route, params)

# (7) Upload diagnostics for one day
# There are about 500 diagnostic messages per day:
# Lets use this to simulate:
# retval: 'inserted n records into json_landing_diag'
def device_diagnostics(diagnostics, http_func=post):
    route = '/upload'
    params = {'device_diagnostics':print_diagnostics(diagnostics)}
    return http_func(route, params)

# (8) Upload activities
# There are about 1500 activity messages for one day.
# Lets use this to simulate (note t increments by 300):
# retval: 'inserted n records into json_landing_act'
def upload_activities(
        user, activity_times, http_func=post):
    route = '/upload'
    params = {'activities':print_activities(user, activity_times)}
    return http_func(route, params)


# ----------------------

# To make a user/sensor:
def make_user(user, http_func=post):
    own_sensor(user, http_func)
    upload_metadata(user, http_func)

# To make a app requests to the back end:
def app(user, n_diag=N_DIAG, n_act=N_ACT, http_func=post,
        metrics=METRICS, t0=T_MIN, t_delta=DELTA):

    # handle gunicorn.limit_request_line
    all_diagnostics_id = range(n_diag)
    chunked_diagnostics_id = chunks(all_diagnostics_id, LIMIT_DIAG)
    all_activity_times = range(t0, t0 + n_act*t_delta, t_delta)
    chuncked_activity_times = chunks(all_activity_times, LIMIT_ACT)

    # Typical flow of app request to the back end:
    check_login(user, http_func)
    download_metadata(user, http_func)
    get_commands(user, http_func)
    check_firmware(user, http_func)
    [stats_aggregate(user, metric, http_func)
     for metric in metrics]
    [stats_lumo_goals(user, metric, http_func)
     for metric in metrics]
    [device_diagnostics(diagnostics_id, http_func)
     for diagnostics_id in chunked_diagnostics_id]
    [upload_activities(user, activity_times, http_func)
     for activity_times in chuncked_activity_times]

# ----------------------

def main(n_users, n_app_reqs, n_diag=N_DIAG, n_act=N_ACT, endpoint=ENDPOINT,
         verbose=False):

    http_func = partial(post, endpoint=endpoint, verbose=verbose)
    for i in range(1, n_users+1):
        user = User(i)
        make_user(user, http_func)
        for j in range(n_app_reqs):
            app(user, n_diag, n_act, http_func)

if __name__ == "__main__":
    cProfile.run('main(%s,%s)'%(sys.argv[1], sys.argv[2]), 'pstats.profile')
    p = pstats.Stats('pstats.profile').sort_stats('cumulative')
    p.print_stats(.2, 'loadtest.py')
