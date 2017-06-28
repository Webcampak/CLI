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
import jsonschema
from ..utils.wpakFile import File


class Capture(object):
    """ Builds an object used to record capture details

    Args:
        log: A class, the logging interface

    Attributes:
        log: A class, the logging interface
    """

    def __init__(self, log, dir_schemas = None, capture_filepath = None, archive_filepath = None):
        self.log = log
        self.__archive_filepath = archive_filepath
        self.__capture_filepath = capture_filepath
        self.__dir_schemas = dir_schemas

        # Load schema into memory
        self.__schema = File.read_json(self.dir_schemas + 'capture.json')

        # Init default email object
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
    def schema(self):
        return self.__schema

    @schema.setter
    def schema(self, schema):
        self.__schema = schema

    @property
    def dir_schemas(self):
        return self.__dir_schemas

    @dir_schemas.setter
    def dir_schemas(self, dir_schemas):
        self.__dir_schemas = dir_schemas

    @property
    def capture(self):
        return self.__capture

    @capture.setter
    def capture(self, capture):
        self.__capture = capture

    @property
    def archive_filepath(self):
        return self.__archive_filepath

    @archive_filepath.setter
    def archive_filepath(self, archive_filepath):
        self.log.info("Capture.archive_filepath(): " + _("Setting Archive filename to: %(filepath)s") % {'filepath': archive_filepath})
        self.__archive_filepath = archive_filepath

    @property
    def capture_filepath(self):
        return self.__capture_filepath

    @capture_filepath.setter
    def capture_filepath(self, capture_filepath):
        self.log.info("Capture.archive_filepath(): " + _("Setting Capture filename to: %(filepath)s") % {'filepath': capture_filepath})
        self.__capture_filepath = capture_filepath

    def get_capture_date(self):
        if self.capture['captureDate'] is not None:
            return dateutil.parser.parse(self.capture['captureDate'])
        else:
            return None

    def open(self, filepath):
        """Open a previously created capture file and load its content into the object"""
        try:
            object_content = file.read_json(filepath)
            jsonschema.validate(object_content, self.schema)
            self.capture = object_content
        except Exception as ex:
            self.log.error(
                "Capture.send(): " + _("Unable to read file: %(ca_fp)s") % {
                    'ca_fp': filepath})
            self.capture = self.__init_capture

    def save(self):
        """Send an email object, effectively taking an object and writing it to a file in the queue directory"""
        jsonschema.validate(self.capture, self.schema)
        if File.write_json(self.capture_filepath, self.capture) is True:
            self.log.info(
                "Capture.send(): " + _("Successfully added saved capture file to: %(ca_fp)s") % {
                    'ca_fp': self.capture_filepath})

    def archive(self):
        """Append the content of the object into a jsonl file containing previous captures"""
        jsonschema.validate(self.capture, self.schema)
        if File.write_jsonl(self.archive_filepath, self.capture) is True:
            self.log.info(
                "Capture.send(): " + _("Successfully added capture to archive file: %(ca_fp)s") % {
                    'ca_fp': self.archive_filepath})