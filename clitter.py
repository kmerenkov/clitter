#!/usr/bin/env python
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

import sys
import twitter
from ConfigParser import RawConfigParser
import os
from pprint import pprint
from datetime import datetime
import terminal_controller
import shelve
from getpass import getpass
from optparse import OptionParser


usage = \
"""Usage:
      a <status>    - update your status
      d <id>        - destroy status by id
      fu [user_id]  - fetch user statuses by user_id
                      (if user_id is ommiitted, fetch your own statuses)
      r             - get rate_limit_status information
      --nocached    - don't print cached data
      -q --quiet    - print results only"""


class ObjectsPersistance(object):
    def __init__(self, filename):
        self.filename = filename
        self.shelve = None

    def open(self):
        self.shelve = shelve.open(self.filename)

    def get(self, name):
        self.open()
        if self.shelve.has_key(name):
            retval = self.shelve[name]
        else:
            retval = ''
        self.shelve.close()
        return retval

    def set(self, name, data):
        self.open()
        self.shelve[name] = data
        self.shelve.close()


class Config(object):
    def __init__(self, filename='~/.clitter'):
        self.filename = os.path.expanduser(filename)
        self.config = None
        self.params_ask = ['twitter.username', 'twitter.password']
        self.defaults = {
            'twitter.timeline_date_format': '%Y.%m.%d %H:%M:%S',
            'twitter.username': '',
            'twitter.password': '',
            }

    def __open_config(self):
        f = open(self.filename, 'w+')
        return f

    def read(self):
        self.config = RawConfigParser()
        if not self.config.read([self.filename]):
            f = self.__open_config()
            f.write('')
            f.close()
            self.read()

    def sync(self):
        f = self.__open_config()
        self.config.write(f)
        f.close()

    def __getitem__(self, item):
        section, name = item.split(".")
        if not all([section, name]):
            return None
        if self.config.has_section(section) and self.config.has_option(section, name):
            return self.config.get(section, name)
        else:
            if item in self.params_ask:
                if "password" in item:
                    val = getpass("Please enter %s: " % name)
                else:
                    val = raw_input("Please enter %s: " % name)
                if val:
                    self[item] = val
                    self.sync()
                    return val
            if item in self.defaults:
                return self.defaults[item]
            return None

    def __setitem__(self, item, value):
        section, name = item.split(".")
        if not all([section, name]):
            return None
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, name, value)


class Clitter(object):
    def __init__(self):
        self.term = terminal_controller.TerminalController()
        self.verbose = False
        self.no_cache = False
        self.quiet = False
        self.command = None
        self.shelve = ObjectsPersistance(os.path.expanduser("~/.clitter.db"))
        self.config = Config()

    def _print(self, text):
        if not self.quiet:
            print text

    def print_data(self, text):
        self._print(self.term.render(u"${YELLOW}%s${NORMAL}" % text))

    def print_error(self, text):
        self._print(self.term.render(u"${RED}%s${NORMAL}" % text))

    def print_progress(self, text):
        self._print(self.term.render(u"${GREEN}%s${NORMAL}" % text))

    def print_timeline(self, date, text):
        date = self.process_date(date)
        print self.term.render(u"${YELLOW}%s${NORMAL}: %s" % (date, text))

    def process_date(self, date):
        date = self.parse_date(date)
        return date.strftime(self.config['twitter.timeline_date_format'])

    def parse_date(self, date):
        return datetime.strptime(date, "%a %b %d %H:%M:%S +0000 %Y")

    def parse_args(self):
        parser = OptionParser(usage="%progname -r|-a|-f", version="0.1")
        parser.add_option('-r', '--rate-time-limit',
                          action='store_true',
                          help="Retrieve rate time limit.")
        parser.add_option('-a', '--add-status',
                          default="",
                          help="Update your status")
        parser.add_option('-f', '--fetch-user',
                          action='store_true', # dirty workaround?
                          help="Fetch user timeline")
        parser.add_option('-d', '--destroy',
                          default=0,
                          type="int",
                          help="Destroy status specified by id")
        parser.add_option('-v', '--verbose',
                          action='store_true',
                          help="Be verbose")
        parser.add_option('-n', '--no-cache',
                          action='store_true',
                          help="Don't print cached statuses")
        options, args = parser.parse_args()

        self.verbose = bool(options.verbose)
        self.no_cache = bool(options.no_cache)

        if options.rate_time_limit:
            self.command_rate_limit_status()
        elif options.add_status:
            self.command_add(options.add_status)
        elif options.fetch_user:
            if args:
                self.command_fetch_user_timeline(args[0])
            else:
                self.command_fetch_user_timeline()
        elif options.destroy:
            self.command_destroy(options.destroy)

    def main(self):
        self.config.read()
        self.parse_args()

    def command_rate_limit_status(self):
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        self.print_progress("Retrieving rate limit status...")
        json = api.get_rate_limit_status()
        if "hourly_limit" in json and "remaining_hits" in json:
            self.print_data("Hits: %d/%d" % (json["remaining_hits"], json["hourly_limit"]))
        else:
            self.print_error("Failed to retrieve rate limit status, response was:")
            pprint(json)

    def command_destroy(self, status_id):
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        self.print_progress("Deleting status...")
        json = api.destroy(status_id)
        if "id" in json:
            self.print_data("Destroyed status %d" % json["id"])
        else:
            self.print_error("Failed to destroy status %d, response was:" % int(status_id))
            pprint(json)

    def command_fetch_user_timeline(self, screenname=''):
        if not screenname:
            screenname = self.config['twitter.username']
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        self.print_progress("Fetching statuses for id %s" % screenname)
        # pick up last entry
        json = []
        since_id = None
        prev_timeline = self.shelve.get("user_timeline/%s" % screenname)
        if prev_timeline:
            since_id = prev_timeline[0]['id']
        json = api.get_user_timeline(screenname, since_id=since_id)
        if not self.no_cache:
            if prev_timeline and len(json):
                if json[0] != prev_timeline[0]:
                    json = json + prev_timeline
            if prev_timeline and not len(json):
                json = prev_timeline
        if isinstance(json, list):
            if prev_timeline:
                self.shelve.set("user_timeline/%s" % screenname, prev_timeline + json)
            else:
                self.shelve.set("user_timeline/%s" % screenname, json)
            # it is a list of dictionaries
            for status in json:
                self.print_timeline(status['created_at'], status['text'])
        else:
            self.print_error("Failed to fetch statuses, response was:")
            pprint(json)

    def command_add(self, status):
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        self.print_progress("Updating status ...")
        json = api.update(status)
        if json.has_key("id"):
            self.print_data("Updated your status, id is %d" % json["id"])
        else:
            self.print_error("Failed to update your status, response was:")
            pprint(json)


if __name__ == '__main__':
    app = Clitter()
    app.main()
