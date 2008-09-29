# -*- coding: utf-8 -*-

# Copyright (c) 2008, Konstantin Merenkov <kmerenkov@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY Konstantin Merenkov <kmerenkov@gmail.com> ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <copyright holder> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import urllib
import urllib2
from datetime import datetime


def http_data(data):
    processed_data = {}
    for k,v in data.iteritems():
        if v is not None:
            processed_data[k] = v
    str_data = "&".join(["%s=%s" % (k,v) for k,v in processed_data.iteritems()])
    return urllib.quote(str_data)

def make_request(url, username='', password='', data={}, method='GET'):
    str_data = http_data(data)
    if method == "GET":
        url = "%s?%s" % (url, str_data)
    print "%s %s" % (method, url)
    if username and password:
        http_handler = urllib2.HTTPBasicAuthHandler()
        http_handler.add_password(realm='Twitter API',
                                  uri=url,
                                  user=username,
                                  passwd=password)
    else:
        http_handler = urllib2.HTTPHandler()
    opener = urllib2.build_opener(http_handler)
    try:
        if method == 'GET':
            f = opener.open(url)
        else:
            f = opener.open(url, str_data)
        retdata  = f.read()
        f.close()
        return retdata
    except urllib2.HTTPError, e:
        print e
        retval = '{}'
    return retval

def GET(url, username='', password='', data={}):
    return make_request(url, username, password, data, 'GET')

def POST(url, username='', password='', data={}):
    return make_request(url, username, password, data, 'POST')

def http_date(date):
    # Tue%2C+27+Mar+2007+22%3A55%3A48+GMT
    parsed_date = datetime.strptime(date, "%a %b %d %H:%M:%S +0000 %Y")
    http_date = datetime.strftime(parsed_date, "%b, %d %a %Y %H:%M:%S GMT")
    return urllib.quote_plus(http_date)
