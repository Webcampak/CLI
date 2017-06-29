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
from wpakDefault import Default


class Sensors(object):
    """ Builds an object used to record sensors details"""

    def __init__(self, log, dir_schemas = None, sensors_filepath = None, archive_filepath = None):
        self.log = log
        self.__archive_filepath = archive_filepath
        self.__sensors_filepath = sensors_filepath
        self.__dir_schemas = dir_schemas

        self.default = Default(self.log, schema_filepath = self.__dir_schemas + 'sensors.json', object_filepath = self.__sensors_filepath, archive_filepath = self.__archive_filepath)

        # Init default sensors object
        self.__init_sensors = {
            'date': None
            , 'sensors': {}
        }
        self.__sensors = self.__init_sensors

    @property
    def sensors(self):
        return self.__sensors

    @sensors.setter
    def sensors(self, sensors):
        self.__sensors = sensors

    def open(self, filepath):
        """Open a previously created sensors file and load its content into the object"""
        open_obj = self.default.open(filepath)
        if open_obj is None:
            self.sensors = self.__init_alert
        else:
            self.sensors = open_obj

    def save(self):
        """Send an email object, effectively taking an object and writing it to a file in the queue directory"""
        self.default.save(self.sensors)

    def archive(self):
        """Append the content of the object into a jsonl file containing previous sensorss"""
        self.default.archive(self.sensors)
