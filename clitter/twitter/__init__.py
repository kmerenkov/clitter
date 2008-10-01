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

import cjson as json
import http
from decorators import login_requied

twitter_statuses_prefix = 'http://twitter.com/statuses/'
twitter_account_prefix = 'http://twitter.com/account/'


class TwitterTransportError(Exception):
    def __init__(self, value):
        self.value = value


class APIRequest(object):
    def __init__(self, username='', password=''):
        self.username = username
        self.password = password

    def __get_json_or_error(self, data):
        if isinstance(data, tuple):
            raise TwitterTransportError("%s: %s" % (data[0], data[1]))
        return json.decode(data)

    def get_public_timeline(self):
        url = "%s%s" % (twitter_statuses_prefix, "public_timeline.json")
        got_data = http.GET(url, self.username, self.password)
        return self.__get_json_or_error(got_data)

    @login_requied
    def get_friends_timeline(self, since=None, since_id=None, count=None, page=None):
        """
        Returns the 20 most recent statuses posted by the authenticating user
        and that user's friends. This is the equivalent of /home on the Web.
        """
        url = "%s%s" % (twitter_statuses_prefix, "friends_timeline.json")
        got_data = http.GET(url, self.username, self.password)
        return self.__get_json_or_error(got_data)

    @login_requied
    def update(self, status, in_reply_to_status_id=None):
        """
        Updates the authenticating user's status. Requires the status parameter
        specified below.  Request must be a POST.
        """
        url = "%s%s" % (twitter_statuses_prefix, "update.json")
        got_data = http.POST(url, self.username, self.password, {'status': status})
        return self.__get_json_or_error(got_data)

    @login_requied
    def destroy(self, id):
        """
        Destroys the status specified by the required ID parameter.
        The authenticating user must be the author of the specified status.
        """
        url = "%s%s" % (twitter_statuses_prefix, "destroy/%s.json" % id)
        got_data = http.POST(url, self.username, self.password)
        return self.__get_json_or_error(got_data)

    @login_requied
    def get_user_timeline(self, user_id=None, count=None, since=None, since_id=None, page=None):
        """
        Returns the 20 most recent statuses posted from the authenticating user.
        It's also possible to request another user's timeline via the id
        parameter below. This is the equivalent of the Web /archive page for
        your own user, or the profile page for a third party.
        """
        url = "%s%s" % (twitter_statuses_prefix, "user_timeline.json")
        data = {}
        if user_id is not None:
            data['id'] = user_id
        else:
            data['id'] = self.username
        if since is not None:
            data['since'] = http.http_date(since)
        if since_id is not None:
            data['since_id'] = since_id
        got_data = http.GET(url, self.username, self.password, data)
        return self.__get_json_or_error(got_data)

    @login_requied
    def get_rate_limit_status(self):
        """
        Returns the remaining number of API requests available to the
        authenticating user before the API limit is reached for the current
        hour. Calls to rate_limit_status require authentication, but will not
        count against the rate limit.
        """
        url = "%s%s" % (twitter_account_prefix, "rate_limit_status.json")
        got_data = http.GET(url, self.username, self.password)
        return self.__get_json_or_error(got_data)

