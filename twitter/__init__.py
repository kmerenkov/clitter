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
import cjson
from datetime import datetime

twitter_statuses_prefix = 'http://twitter.com/statuses/'
twitter_account_prefix = 'http://twitter.com/account/'


def request_get(url):
    try:
        f = urllib2.urlopen(url)
        retval = f.read()
        f.close()
    except urllib2.HTTPError, e:
        print e
        retval = "{}"
    return retval

def request_post(url, username, password, data):
    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm='Twitter API',
                              uri=url,
                              user=username,
                              passwd=password)
    opener = urllib2.build_opener(auth_handler)
    try:
        f = opener.open(url, data)
        retval = f.read()
        f.close()
    except urllib2.HTTPError, e:
        print e
        retval = "{}"
    return retval


class NotAuthorizedError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class APIRequest(object):
    def __init__(self, username='', password=''):
        self.username = username
        self.password = password

    def http_date(self, date):
        # Tue%2C+27+Mar+2007+22%3A55%3A48+GMT
        parsed_date = datetime.strptime(date, "%a %b %d %H:%M:%S +0000 %Y")
        http_date = datetime.strftime(parsed_date, "%b, %d %a %Y %H:%M:%S GMT")
        return urllib.quote_plus(http_date)

    def get_public_timeline(self):
        url = "%s%s" % (twitter_statuses_prefix, "public_timeline.json")
        got_data = request_get(url)
        json = cjson.decode(got_data)
        return json

    def get_friends_timeline(self, since=None, since_id=None, count=None, page=None):
        """
        Returns the 20 most recent statuses posted by the authenticating user
        and that user's friends. This is the equivalent of /home on the Web.
        """
        if not all([self.username, self.password]):
            raise NotAuthorizedError("Both username and password required")
        url = "%s%s" % (twitter_statuses_prefix, "friends_timeline.json")
        got_data = request_get(url)
        json = cjson.decode(got_data)
        return json

    def update(self, status, in_reply_to_status_id=None):
        """
        Updates the authenticating user's status. Requires the status parameter
        specified below.  Request must be a POST.
        """
        if not all([self.username, self.password]):
            raise NotAuthorizedError("Both username and password required")
        url = "%s%s" % (twitter_statuses_prefix, "update.json")
        status = "status=%s" % urllib.quote(status)
        got_data = request_post(url, self.username, self.password, status)
        json = cjson.decode(got_data)
        return json

    def destroy(self, id):
        """
        Destroys the status specified by the required ID parameter.
        The authenticating user must be the author of the specified status.
        """
        if not all([self.username, self.password]):
            raise NotAuthorizedError("Both username and password required")
        url = "%s%s" % (twitter_statuses_prefix, "destroy/%s.json" % id)
        got_data = request_post(url, self.username, self.password, "")
        json = cjson.decode(got_data)
        return json

    def get_user_timeline(self, user_id=None, count=None, since=None, since_id=None, page=None):
        """
        Returns the 20 most recent statuses posted from the authenticating user.
        It's also possible to request another user's timeline via the id
        parameter below. This is the equivalent of the Web /archive page for
        your own user, or the profile page for a third party.
        """
        if not all([self.username, self.password]):
            raise NotAuthorizedError("Both username and password required")
        url = "%s%s" % (twitter_statuses_prefix, "user_timeline.json")
        options = ""
        if user_id is not None:
            user_id = "id=%s" % user_id
        else:
            user_id = "id=%s" % self.username
        if since is not None:
            since = "since=%s" % self.http_date(since)
        options = "&".join(filter(lambda x: x is not None, [user_id, since, count, since_id, page]))
        got_data = request_get("%s?%s" % (url, options))
        json = cjson.decode(got_data)
        return json

    def get_rate_limit_status(self):
        """
        Returns the remaining number of API requests available to the
        authenticating user before the API limit is reached for the current
        hour. Calls to rate_limit_status require authentication, but will not
        count against the rate limit.
        """
        url = "%s%s" % (twitter_account_prefix, "rate_limit_status.json")
        got_data = request_get(url)
        json = cjson.decode(got_data)
        return json

