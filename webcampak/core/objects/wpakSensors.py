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


class Sensors(object):
    """ Builds an object used to record sensors details"""

    def __init__(self, log, dir_schemas = None, sensors_filepath = None, archive_filepath = None):
        self.log = log
        self.__archive_filepath = archive_filepath
        self.__sensors_filepath = sensors_filepath
        self.__dir_schemas = dir_schemas

        # Load schema into memory
        self.__schema = File.read_json(self.dir_schemas + 'sensors.json')

        # Init default sensors object
        self.__init_sensors = {
            'date': None
            , 'sensors': {}
        }
        self.__sensors = self.__init_sensors

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
    def sensors(self):
        return self.__sensors

    @sensors.setter
    def sensors(self, sensors):
        self.__sensors = sensors

    @property
    def archive_filepath(self):
        return self.__archive_filepath

    @archive_filepath.setter
    def archive_filepath(self, archive_filepath):
        self.log.info("sensors.archive_filepath(): " + _("Setting Archive filename to: %(filepath)s") % {'filepath': archive_filepath})
        self.__archive_filepath = archive_filepath

    @property
    def sensors_filepath(self):
        return self.__sensors_filepath

    @sensors_filepath.setter
    def sensors_filepath(self, sensors_filepath):
        self.log.info("sensors.archive_filepath(): " + _("Setting Sensors filename to: %(filepath)s") % {'filepath': sensors_filepath})
        self.__sensors_filepath = sensors_filepath

    def open(self, filepath):
        """Open a previously created sensors file and load its content into the object"""
        try:
            object_content = file.read_json(filepath)
            jsonschema.validate(object_content, self.schema)
            self.sensors = object_content
        except Exception as ex:
            self.log.error(
                "sensors.send(): " + _("Unable to read file: %(ca_fp)s") % {
                    'ca_fp': filepath})
            self.sensors = self.__init_sensors

    def save(self):
        """Send an email object, effectively taking an object and writing it to a file in the queue directory"""
        jsonschema.validate(self.sensors, self.schema)
        if File.write_json(self.sensors_filepath, self.sensors) is True:
            self.log.info(
                "sensors.send(): " + _("Successfully added saved sensors file to: %(ca_fp)s") % {
                    'ca_fp': self.sensors_filepath})

    def archive(self):
        """Append the content of the object into a jsonl file containing previous sensorss"""
        jsonschema.validate(self.sensors, self.schema)
        if File.write_jsonl(self.archive_filepath, self.sensors) is True:
            self.log.info(
                "sensors.send(): " + _("Successfully added sensors to archive file: %(ca_fp)s") % {
                    'ca_fp': self.archive_filepath})