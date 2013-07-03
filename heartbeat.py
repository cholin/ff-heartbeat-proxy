#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import cgi
import json
import logging
import logging.handlers
import urllib2
import cgitb
import couchdb
import sys
import os

from StringIO import StringIO
from lxml import etree
from lxml.cssselect import CSSSelector
from datetime import datetime

# globals
MAP_URL = 'http://openwifimap.net/map.html'
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
        data['latitude']  = float(value)
    elif k == 'neighbors':
        data[''] = float(value)
    elif k == 'clients':
        data[''] = float(value)

# bring the data into the database
saved_to = []
if all(k in data for k in ['hostname', 'longitude','latitude']):
    data['_id'] = data['hostname']

    for server, database in SERVERS:
        couch = couchdb.Server('http://%s' % server)
        db = couch[database]
        entry = db.get(data['_id'])
        if entry != None:
            data['_rev'] = entry['_rev']

        data['type'] = 'node'
        data['lastupdate'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        if db.save(data):
            saved_to.append("%s/%s" % (server, database))

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
