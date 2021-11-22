#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2010-2017 Eurotechnia (support@webcampak.com)
# This file is part of the Webcampak project.
# Webcampak is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.

# Webcampak is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Webcampak.
# If not, see http://www.gnu.org/licenses/

from __future__ import absolute_import
from builtins import object
import os
from ..utils.wpakFile import File
from .wpakDefault import Default


class Alert(object):
    """ Builds an object used to record alert details"""

    def __init__(self, log, dir_schemas = None, alert_filepath = None, archive_filepath = None):
        self.log = log
        self.__archive_filepath = archive_filepath
        self.__alert_filepath = alert_filepath
        self.__dir_schemas = dir_schemas

        self.default = Default(self.log, schema_filepath = self.__dir_schemas + 'alert.json', object_filepath = self.__alert_filepath, archive_filepath = self.__archive_filepath)

        # Init default alert object
        self.__init_alert = {}
        self.__alert = self.__init_alert

        """Ensure the default object is compliant with the schema, mostly here to prevent errors during code updates"""
        self.default.verify(self.alert)

    @property
    def alert(self):
        return self.__alert

    @alert.setter
    def alert(self, alert):
        self.__alert = alert

    def open(self, filepath):
        """Open a previously created alert file and load its content into the object"""
        open_obj = self.default.open(filepath)
        if open_obj is None:
            self.alert = self.__init_alert
        else:
            self.alert = open_obj

    def save(self):
        """Send an email object, effectively taking an object and writing it to a file in the queue directory"""
        self.default.save(self.alert)

    def archive(self):
        """Append the content of the object into a jsonl file containing previous alerts"""
        self.default.archive(self.alert)

    def load_last_alert(self):
        """Get the last alert line from the archive file"""
        if os.path.isfile(self.archive_filepath):
            self.alert = File.get_jsonl_lastline(self.archive_filepath)
        else:
            self.alert = self.__init_alert