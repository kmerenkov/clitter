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
# DISCLAIMED. IN NO EVENT SHALL Konstantin Merenkov <kmerenkov@gmail.com> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from getpass import getpass
from ConfigParser import RawConfigParser


class Config(object):
    def __init__(self, filename):
        self.filename = filename
        self.config = None
        self.params_ask = ['twitter.username', 'twitter.password']
        self.defaults = {
            'twitter.timeline_date_format': '%Y.%m.%d %H:%M:%S',
            'twitter.username': '',
            'twitter.password': '',
            'ui.separate_cached_entries': True
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
