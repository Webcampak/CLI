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

import jsonschema
from ..utils.wpakFile import File

class Default(object):
    """ Builds an object used to send emails"""

    def __init__(self, log, schema_filepath = None, object_filepath = None, archive_filepath = None):
        self.log = log
        self.__schema_filepath = schema_filepath
        self.__object_filepath = object_filepath
        self.__archive_filepath = archive_filepath

        self.log.info("DefaultObj(): " + _("Setting Schema Filepath to: %(schema_filepath)s") % {'schema_filepath': self.schema_filepath})
        self.log.info("DefaultObj(): " + _("Setting Object Filepath to: %(object_filepath)s") % {'object_filepath': self.object_filepath})
        self.log.info("DefaultObj(): " + _("Setting Archive Filepath to: %(archive_filepath)s") % {'archive_filepath': self.archive_filepath})

        # Load schema into memory
        self.__schema = File.read_json(schema_filepath)

    @property
    def schema(self):
        return self.__schema

    @schema.setter
    def schema(self, schema):
        self.__schema = schema

    @property
    def schema_filepath(self):
        return self.__schema_filepath

    @schema_filepath.setter
    def schema_filepath(self, schema_filepath):
        self.__schema_filepath = schema_filepath

    @property
    def object_filepath(self):
        return self.__object_filepath

    @object_filepath.setter
    def object_filepath(self, object_filepath):
        self.__object_filepath = object_filepath

    @property
    def archive_filepath(self):
        return self.__archive_filepath

    @archive_filepath.setter
    def archive_filepath(self, archive_filepath):
        self.__archive_filepath = archive_filepath

    def save(self, received_object):
        """Save an object to the file defined in object_filepath"""
        jsonschema.validate(received_object, self.schema)
        if File.write_json(self.object_filepath, received_object) is True:
            self.log.info(
                "emailObj.send(): " + _("File successfully written to: %(object_filepath)s") % {
                    'object_filepath': self.object_filepath})

    def archive(self, received_object):
        """Append the content of the object into a jsonl file containing previous alerts"""
        jsonschema.validate(received_object, self.schema)
        if File.write_jsonl(self.archive_filepath, received_object) is True:
            self.log.info(
                "Capture.send(): " + _("Successfully added object to archive file: %(archive_filepath)s") % {
                    'archive_filepath': self.archive_filepath})

    def open(self, filepath):
        """Open a previously created object and load its content into a python object"""
        try:
            object_content = File.read_json(filepath)
            jsonschema.validate(object_content, self.schema)
            return object_content
        except Exception as ex:
            self.log.error(
                "Capture.send(): " + _("Unable to read file: %(ca_fp)s") % {
                    'ca_fp': filepath})
            return None
