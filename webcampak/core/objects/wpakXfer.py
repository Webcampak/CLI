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

import os
from ..utils.wpakFile import File
from wpakDefault import Default


class Xfer(object):
    """ Builds an object used to describe a job"""

    def __init__(self, log, dir_schemas = None, xfer_filepath = None, archive_filepath = None):
        self.log = log
        self.__archive_filepath = archive_filepath
        self.__xfer_filepath = xfer_filepath
        self.__dir_schemas = dir_schemas

        self.default = Default(self.log, schema_filepath = self.__dir_schemas + 'xfer.json', object_filepath = self.__xfer_filepath, archive_filepath = self.__archive_filepath)

        # Init default xfer object
        self.__init_xfer = {}
        self.__xfer = self.__init_xfer

    @property
    def xfer(self):
        return self.__xfer

    @xfer.setter
    def xfer(self, xfer):
        self.__xfer = xfer

    def open(self, filepath):
        """Open a previously created xfer file and load its content into the object"""
        open_obj = self.default.open(filepath)
        if open_obj is None:
            self.xfer = self.__init_xfer
        else:
            self.xfer = open_obj

    def save(self):
        """Send an email object, effectively taking an object and writing it to a file in the queue directory"""
        self.default.save(self.xfer)

    def archive(self):
        """Append the content of the object into a jsonl file containing previous xfers"""
        self.default.archive(self.xfer)

    def load_last_xfer(self):
        """Get the last xfer line from the archive file"""
        if os.path.isfile(self.archive_filepath):
            self.xfer = File.get_jsonl_lastline(self.archive_filepath)
        else:
            self.xfer = self.__init_xfer