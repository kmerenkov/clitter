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


usage = \
"""Usage:
      a <status>    - update your status
      d <id>        - destroy status by id
      fu [user_id]  - fetch user statuses by user_id
                      (if user_id is ommiitted, fetch your own statuses)
      r             - get rate_limit_status information"""


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
                else:
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
        self.command = None
        self.shelve = ObjectsPersistance(os.path.expanduser("~/.clitter.db"))
        self.config = Config()

    def print_warning(self, text):
        print self.term.render("${YELLOW}%s${NORMAL}" % text)

    def print_error(self, text):
        print self.term.render("${RED}%s${NORMAL}" % text)

    def print_progress(self, text):
        print self.term.render("${GREEN}%s${NORMAL}" % text)

    def print_timeline(self, date, text):
        date = self.process_date(date)
        print self.term.render("${YELLOW}%s${NORMAL}: %s" % (date, text))

    def process_date(self, date):
        date = self.parse_date(date)
        return date.strftime(self.config['twitter.timeline_date_format'])

    def parse_date(self, date):
        return datetime.strptime(date, "%a %b %d %H:%M:%S +0000 %Y")

    def quit(self, status, print_usage=True):
        if print_usage:
            print usage
        sys.exit(status)

    def parse_args(self):
        def check_args(required):
            if len(sys.argv) < required:
                self.quit(1)
        check_args(2)
        if sys.argv[1] in ["a", "d"]:
            check_args(3)
        elif sys.argv[1] in ["fu", "r"]:
            pass
        else:
            self.quit(1)
        self.command = sys.argv[1]

    def main(self):
        self.parse_args()
        self.config.read()
        self.handle_command()

    def handle_command(self):
        if self.command == "a":
            self.command_add()
        elif self.command == "fu":
            self.command_fetch_user_timeline()
        elif self.command == "d":
            self.command_destroy()
        elif self.command == "r":
            self.command_rate_limit_status()
        else:
            assert "Unknown command %s" % self.command

    def command_rate_limit_status(self):
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        self.print_progress("Retrieving rate limit status...")
        json = api.get_rate_limit_status()
        if json.has_key("hourly_limit"):
            self.print_warning("Hits: %d/%d" % (json["remaining_hits"], json["hourly_limit"]))
        else:
            self.print_error("Failed to retrieve rate limit status, response was:")
            pprint(json)

    def command_destroy(self):
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        status_id = sys.argv[2]
        self.print_progress("Deleting status...")
        json = api.destroy(status_id)
        if json.has_key("id"):
            self.print_warning("Destroyed status %d" % json["id"])
        else:
            self.print_error("Failed to destroy status %d, response was:" % int(status_id))
            pprint(json)

    def command_fetch_user_timeline(self):
        if len(sys.argv) > 2:
            screenname = sys.argv[2]
        else:
            screenname = self.config['twitter.username']
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        self.print_progress("Fetching statuses for id %s" % screenname)
        # pick up last entry
        prev_timeline = self.shelve.get("user_timeline")
        since = None
        if prev_timeline:
            since = prev_timeline[0]['created_at']
        json = api.get_user_timeline(screenname, since=since)
        if prev_timeline and len(json):
            if json[0] != prev_timeline[0]:
                json = json+prev_timeline
        if prev_timeline and not len(json):
            json = prev_timeline
        if len(json):
            self.shelve.set("user_timeline", json)
            # it is a list of dictionaries
            for status in json:
                self.print_timeline(status['created_at'], status['text'])
        else:
            self.print_error("Failed to fetch statuses, response was:")
            pprint(json)

    def command_add(self):
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        status = sys.argv[2]
        self.print_progress("Updating status ...")
        json = api.update(status)
        if json.has_key("id"):
            self.print_warning("Updated your status, id is %d" % json["id"])
        else:
            self.print_error("Failed to update your status, response was:")
            pprint(json)


if __name__ == '__main__':
    app = Clitter()
    app.main()
