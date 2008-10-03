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

import os
from pprint import pprint
from datetime import datetime
import logging
from optparse import OptionParser

import twitter
from config import Config
from cache import ObjectsPersistance
import terminal_controller

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s")


class Clitter(object):
    def __init__(self):
        self.term = terminal_controller.TerminalController()
        self.verbose = False
        self.no_cache = False
        self.dump_http = False
        self.quiet = False
        self.show_ids = False
        self.shelve = ObjectsPersistance(os.path.expanduser("~/.clitter.db"))
        self.config = Config(os.path.expanduser("~/.clitter"))

    def __print(self, text):
        try:
            print text.encode('utf-8')
        except IOError:
            return

    def _print(self, text):
        if not self.quiet:
            self.__print(text)

    def print_data(self, text):
        self._print(self.term.render(u"${YELLOW}%s${NORMAL}" % text))

    def print_error(self, text):
        self._print(self.term.render(u"${RED}%s${NORMAL}" % text))

    def print_progress(self, text):
        self._print(self.term.render(u"${GREEN}%s${NORMAL}" % text))

    def print_timeline(self, timeline, print_names=False):
        # uglinessssss
        for status in timeline:
            date = self.process_date(status['created_at'])
            left = date
            if self.show_ids:
                left = "%s %s" % (status['id'], date)
            left = self.term.render(u"${YELLOW}%s${NORMAL}: " % left)

            if print_names:
                right = self.term.render("${CYAN}%s:${NORMAL} %s" % (status['user']['name'], status['text']))
            else:
                right = self.term.render(status['text'])
            self.__print("%s%s" % (left, right))

    def print_unexpected_json(self, data):
        self.__print("${RED}%s:${NORMAL}$" % "Unexpected json reply")
        pprint(data)

    def print_separator(self, caption):
        self._print(self.term.render("${YELLOW}====${NORMAL}%s${YELLOW}====${NORMAL}" % caption))

    def process_date(self, date):
        date = self.parse_date(date)
        return date.strftime(self.config['twitter.timeline_date_format'])

    def parse_date(self, date):
        return datetime.strptime(date, "%a %b %d %H:%M:%S +0000 %Y")

    def handle_args(self):
        parser = OptionParser(usage="%progname -r|-a|-f", version="0.1")
        parser.add_option('-r', '--rate-time-limit',
                          action='store_true',
                          help="Retrieve rate time limit.")
        parser.add_option('-a', '--add-status',
                          default="",
                          metavar="STATUS",
                          help="Update your status")
        parser.add_option('-u', '--fetch-user',
                          action='store_true', # dirty workaround?
                          help="Fetch user timeline")
        parser.add_option('-f', '--fetch-friends',
                          action='store_true', # dirty workaround?
                          help="Fetch friends timeline")
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
        parser.add_option('-q', '--quiet',
                          action='store_true',
                          help="Be quiet about progress")
        parser.add_option('--show-ids',
                           action='store_true',
                           dest="show_ids",
                           help="Print ids in timeline")
        parser.add_option('--dump-http',
                          action='store_true',
                          help="Print debug HTTP requests and responses")
        options, args = parser.parse_args()

        self.quiet = bool(options.quiet)
        self.verbose = bool(options.verbose)
        self.no_cache = bool(options.no_cache)
        self.show_ids = bool(options.show_ids)
        self.dump_http = bool(options.dump_http)

        http_logger = logging.getLogger('twitter.http')
        http_logger.setLevel(10 if self.dump_http else 0)

        if options.rate_time_limit:
            self.command_rate_limit_status()
        elif options.add_status:
            self.command_add(options.add_status)
        elif options.fetch_user:
            self.command_fetch_user_timeline(args[0] if args else None)
        elif options.fetch_friends:
            self.command_fetch_friends_timeline()
        elif options.destroy:
            self.command_destroy(options.destroy)

    def main(self):
        self.config.read()
        self.handle_args()

    def handle_api_response(self, api_callable, *args, **kwargs):
        try:
            retval = api_callable(*args, **kwargs)
        except twitter.TwitterTransportError, e:
            self.print_error(e)
            return None
        else:
            return retval

    def command_rate_limit_status(self):
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        self.print_progress("Retrieving rate limit status...")
        data = self.handle_api_response(api.get_rate_limit_status)
        if data:
            if "hourly_limit" in data and "remaining_hits" in data:
                self.print_data("Hits: %d/%d" % (data["remaining_hits"], data["hourly_limit"]))
            else:
                self.print_unexpected_json(data)

    def command_destroy(self, status_id):
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        self.print_progress("Deleting status...")
        data = self.handle_api_response(api.destroy, status_id)
        if data:
            if "id" in data:
                self.print_data("Destroyed status %d" % data["id"])
            else:
                self.print_unexpected_json(data)

    def command_fetch_friends_timeline(self):
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        self.print_progress("Fetching friends timeline")
        # pick up last entry
        json = []
        shelve_key = "friends_timeline"
        since_id = None
        prev_timeline = self.shelve.get(shelve_key)
        if prev_timeline:
            since_id = prev_timeline[0]['id']
        json = self.handle_api_response(api.get_friends_timeline, since_id=since_id)
        if json or prev_timeline:
            json = json or []
            prev_timeline = prev_timeline or []
            if prev_timeline:
                self.shelve.set(shelve_key, json + prev_timeline)
            else:
                self.shelve.set(shelve_key, json)

            if self.config['ui.separate_cached_entries']:
                self.print_separator("new entries")
            if json:
                self.print_timeline(json)
            else:
                self.print_error("No updates")
            if not self.no_cache:
                if self.config['ui.separate_cached_entries']:
                    self.print_separator("cached entries")
                self.print_timeline(prev_timeline, print_names=True)

    def command_fetch_user_timeline(self, screenname=''):
        if not screenname:
            screenname = self.config['twitter.username']
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        self.print_progress("Fetching statuses for id %s" % screenname)
        # pick up last entry
        json = []
        shelve_key = "user_timeline/%s" % screenname
        since_id = None
        prev_timeline = self.shelve.get(shelve_key)
        if prev_timeline:
            since_id = prev_timeline[0]['id']
        json = self.handle_api_response(api.get_user_timeline, screenname, since_id=since_id)
        if json or prev_timeline:
            json = json or []
            prev_timeline = prev_timeline or []
            if prev_timeline:
                self.shelve.set(shelve_key, json + prev_timeline)
            else:
                self.shelve.set(shelve_key, json)

            if self.config['ui.separate_cached_entries']:
                self.print_separator("new entries")
            if json:
                self.print_timeline(json)
            else:
                self.print_error("No updates")
            if not self.no_cache:
                if self.config['ui.separate_cached_entries']:
                    self.print_separator("cached entries")
                self.print_timeline(prev_timeline)

    def command_add(self, status):
        api = twitter.APIRequest(self.config['twitter.username'], self.config['twitter.password'])
        self.print_progress("Updating status ...")
        json = self.handle_api_response(api.update, status)
        if json:
            if json.has_key("id"):
                self.print_data("Updated your status, id is %d" % json["id"])
            else:
                self.print_unexpected_json(json)


if __name__ == '__main__':
    app = Clitter()
    app.main()
