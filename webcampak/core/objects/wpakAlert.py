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
import jsonschema
from ..utils.wpakFile import File


class Alert(object):
    """ Builds an object used to record alert details"""

    def __init__(self, log, dir_schemas = None, alert_filepath = None, archive_filepath = None):
        self.log = log
        self.__archive_filepath = archive_filepath
        self.__alert_filepath = alert_filepath
        self.__dir_schemas = dir_schemas

        # Load schema into memory
        self.__schema = File.read_json(self.dir_schemas + 'alert.json')

        # Init default alert object
        self.__init_alert = {}
        self.__alert = self.__init_alert

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
    def alert(self):
        return self.__alert

    @alert.setter
    def alert(self, alert):
        self.__alert = alert

    @property
    def archive_filepath(self):
        return self.__archive_filepath

    @archive_filepath.setter
    def archive_filepath(self, archive_filepath):
        self.log.info("Capture.archive_filepath(): " + _("Setting Archive filename to: %(filepath)s") % {'filepath': archive_filepath})
        self.__archive_filepath = archive_filepath

    @property
    def alert_filepath(self):
        return self.__alert_filepath

    @alert_filepath.setter
    def alert_filepath(self, alert_filepath):
        self.log.info("Capture.archive_filepath(): " + _("Setting Alert filename to: %(filepath)s") % {'filepath': alert_filepath})
        self.__alert_filepath = alert_filepath


    def open(self, filepath):
        """Open a previously created alert file and load its content into the object"""
        try:
            object_content = file.read_json(filepath)
            jsonschema.validate(object_content, self.schema)
            self.alert = object_content
        except Exception as ex:
            self.log.error(
                "Capture.send(): " + _("Unable to read file: %(ca_fp)s") % {
                    'ca_fp': filepath})
            self.alert = self.__init_alert

    def save(self):
        """Send an email object, effectively taking an object and writing it to a file in the queue directory"""
        jsonschema.validate(self.alert, self.schema)
        if File.write_json(self.alert_filepath, self.alert) is True:
            self.log.info(
                "Capture.send(): " + _("Successfully added saved alert file to: %(ca_fp)s") % {
                    'ca_fp': self.alert_filepath})

    def archive(self):
        """Append the content of the object into a jsonl file containing previous alerts"""
        jsonschema.validate(self.alert, self.schema)
        if File.write_jsonl(self.archive_filepath, self.alert) is True:
            self.log.info(
                "Capture.send(): " + _("Successfully added alert to archive file: %(ca_fp)s") % {
                    'ca_fp': self.archive_filepath})

    def load_last_alert(self):
        """Get the last alert line from the archive file"""
        if os.path.isfile(self.archive_filepath):
            self.alert = File.get_jsonl_lastline(self.archive_filepath)
        else:
            self.alert = self.__init_alert