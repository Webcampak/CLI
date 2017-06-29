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

import dateutil.parser
from wpakDefault import Default


class Capture(object):
    """ Builds an object used to record capture details"""

    def __init__(self, log, dir_schemas = None, capture_filepath = None, archive_filepath = None):
        self.log = log
        self.__archive_filepath = archive_filepath
        self.__capture_filepath = capture_filepath
        self.__dir_schemas = dir_schemas

        self.default = Default(self.log, schema_filepath = self.__dir_schemas + 'capture.json', object_filepath = self.__capture_filepath, archive_filepath = self.__archive_filepath)

        # Init default capture object
        self.__init_capture = {
            'storedJpgSize': 0
            , 'storedRawSize': 0
            , 'storedRawSize': 0
            , 'totalCaptureSize': 0
            , 'scriptStartDate': None
            , 'scriptEndDate': None
            , 'scriptRuntime': None
            , 'processedPicturesCount': 0
            , 'captureSuccess': None
            , 'captureDate': None
        }
        self.__capture = self.__init_capture

    @property
    def capture(self):
        return self.__capture

    @capture.setter
    def capture(self, capture):
        self.__capture = capture

    def get_capture_date(self):
        if self.capture['captureDate'] is not None:
            return dateutil.parser.parse(self.capture['captureDate'])
        else:
            return None

    def open(self, filepath):
        """Open a previously created capture file and load its content into the object"""
        open_obj = self.default.open(filepath)
        if open_obj is None:
            self.capture = self.__init_alert
        else:
            self.capture = open_obj

    def save(self):
        """Send an email object, effectively taking an object and writing it to a file in the queue directory"""
        self.default.save(self.capture)

    def archive(self):
        """Append the content of the object into a jsonl file containing previous captures"""
        self.default.archive(self.capture)
