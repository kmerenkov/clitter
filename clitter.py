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


usage = \
"""Usage:
      a <status>    - update your status
      d <id>        - destroy status by id
      fu [user_id]  - fetch user statuses by user_id
                      (if user_id is ommiitted, fetch your own statuses)"""

class Clitter(object):
    def __init__(self):
        self.term = terminal_controller.TerminalController()
        self.verbose = False
        self.command = None
        self.username = None
        self.password = None
        self.settings = {
            'timeline_date_format': '%Y.%m.%d %H:%M:%S'
            }

    def print_warning(self, text):
        print self.term.render("${YELLOW}%s${NORMAL}" % text)

    def print_error(self, text):
        print self.term.render("${RED}%s${NORMAL}" % text)

    def print_highlight(self, text):
        print self.term.render("${GREEN}%s${NORMAL}" % text)

    def print_timeline(self, date, text):
        date = self.process_date(date)
        print self.term.render("${YELLOW}%s${NORMAL}: %s" % (date, text))

    def process_date(self, date):
        date = self.parse_date(date)
        return date.strftime(self.settings['timeline_date_format'])

    def parse_date(self, date):
        return datetime.strptime(date, "%a %b %d %H:%M:%S +0000 %Y")

    def read_config(self):
        config = RawConfigParser()
        cfg_path = os.path.expanduser("~/.clitter")
        if not len(config.read([cfg_path])):
            self.print_error("Could not read config from: %s" % cfg_path)
            self.quit(1)
        username = config.get("auth", "username")
        password = config.get("auth", "password")
        self.username = username
        self.password = password

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
        elif sys.argv[1] in ["fu"]:
            pass
        else:
            self.quit(1)
        self.command = sys.argv[1]

    def main(self):
        self.parse_args()
        self.read_config()
        self.command = sys.argv[1]
        self.handle_command()

    def handle_command(self):
        if self.command == "a":
            self.command_add()
        elif self.command == "fu":
            self.command_fetch_user_timeline()
        elif self.command == "d":
            self.command_destroy()
        else:
            assert "Unknown command %s" % self.command

    def command_destroy(self):
        status_id = sys.argv[2]
        self.print_highlight("Deleting status...")
        api = twitter.APIRequest(self.username, self.password)
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
            screenname = self.username
        self.print_highlight("Fetching statuses for id %s" % screenname)
        api = twitter.APIRequest(self.username, self.password)
        json = api.get_user_timeline(screenname)
        if len(json):
            # it is a list of dictionaries
            for status in json:
                self.print_timeline(status['created_at'], status['text'])
        else:
            self.print_error("Failed to fetch statuses, response was:")
            pprint(json)

    def command_add(self):
        status = sys.argv[2]
        self.print_highlight("Updating status ...")
        api = twitter.APIRequest(self.username, self.password)
        json = api.update(status)
        if json.has_key("id"):
            self.print_warning("Updated your status, id is %d" % json["id"])
        else:
            self.print_error("Failed to update your status, response was:")
            pprint(json)


if __name__ == '__main__':
    app = Clitter()
    app.main()
