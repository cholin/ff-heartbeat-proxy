#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import cgi
import json
import logging
import logging.handlers
import urllib2
import cgitb
import sys
import os

# globals
MAP_URL = 'http://openwifimap.net/map.html'
API_URLS = ['http://api.openwifimap.net/']
SERVERS = [('openwifimap.net','openwifimap')]
LOG_FILE = os.path.join('logs', 'mapconvert.log')

# enable debugging
cgitb.enable()

# logger
logging.basicConfig(format='\n%(asctime)s\n%(message)s\n')
logger = logging.getLogger('mapconvert')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.handlers.RotatingFileHandler(LOG_FILE,
                    maxBytes=100*1024, backupCount=3))
logger.addHandler(logging.StreamHandler(sys.stdout))

# parse parameters
form = cgi.FieldStorage()
data = {
   'script' : 'freifunk-heartbeat-proxy',
}

for k in form.keys():
    value = form[k].value.decode('utf-8', 'ignore')
    escaped = cgi.escape(value)

    if k == 'name':
        data['hostname'] = escaped
    elif k == 'lat':
        data['latitude']  = float(value)
    elif k == 'lon':
        data['longitude']  = float(value)
    elif k == 'neighbors':
        data['links'] = float(value)
    elif k == 'clients':
        data['clients'] = float(value)

# bring the data into the database
saved_to = []
if all(k in data for k in ['hostname', 'longitude', 'latitude']):
    data['type'] = 'node'
    data['updateInterval'] = 86400 # one day

    for api_url in API_URLS:
        # only update if present doc was also sent by freifunk-map-proxy
        try:
            oldreq = urllib2.urlopen(api_url+'/db/'+data['hostname'])
            if oldreq.getcode()==200:
                olddata = json.loads(oldreq.read())
                if olddata['script'] != data['script']:
                    continue
        except urllib2.HTTPError:
            pass

        req = urllib2.urlopen(api_url+'/update_node/'+data['hostname'], json.dumps(data))
        if req.getcode()==201:
            saved_to.append(api_url)

if len(saved_to) > 0:
    print('Content-Type: text/plain;charset=utf-8\n')

    # log and print them
    msg = '\n'.join([
        "REQUEST: " + os.environ['QUERY_STRING'],
        "SAVED IN: " + (','.join(saved_to) or '-'),
        "DATA: " + json.dumps(data, indent = 4),
        ""
    ])
    logger.debug(msg)

else:
    print('Location: %s\n' % MAP_URL)
