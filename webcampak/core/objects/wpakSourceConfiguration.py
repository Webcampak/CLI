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
import yaml
from ..utils.wpakFile import File
import jsonschema


class SourceConfiguration(object):
    """ Builds an object containing configuration of a source"""

    def __init__(self, log, cfg_filepath = None, config_paths = None):
        self.log = log
        self.config_paths = config_paths

        self.__schema_filepath = self.config_paths.getConfig('parameters')['dir_schemas'] + 'source-configuration.json'
        self.__cfg_filepath = cfg_filepath

        # Load schema into memory
        self.__schema = File.read_json(self.schema_filepath)

        # Load configuration into memory
        self.load()

        # Verify configuration loaded by default
        self.check_cfg()

    @property
    def source(self):
        return self.__source

    @source.setter
    def source(self, source):
        self.__source = source

    @property
    def cfg(self):
        return self.__cfg

    @cfg.setter
    def cfg(self, cfg):
        self.__cfg = cfg

    @property
    def cfg_filepath(self):
        return self.__cfg_filepath

    @cfg_filepath.setter
    def cfg_filepath(self, cfg_filepath):
        self.__cfg_filepath = cfg_filepath

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

    def load(self):
        """Load a source configuration into memory"""
        if os.path.isfile(self.cfg_filepath):
            self.log.info('SourceConfiguration.load(): Loading configuration from: ' + self.cfg_filepath)
            with open(self.cfg_filepath, 'r') as ymlfile:
                self.cfg = yaml.safe_load(ymlfile)
        else:
            self.log.info('SourceConfiguration.load(): Unable to load from configuration file: ' + self.cfg_filepath)
            self.cfg = {}
            return True

    def check_cfg(self):
        """Verify if configuration object is compliant with schema"""
        jsonschema.validate(self.cfg, self.schema)
        return True

    def get_capture_val(self, cfg_setting):
        """Lookup for a particular configuration setting in source configuration
            If the element does not exist, get the default value
            If default not found, return None
        """
        self.log.info('SourceConfiguration.get_capture_val(): Looking for configuration setting: ' + cfg_setting)
        # First look for value in source configuration
        cfg_value = self.find_value_cfg(cfg_setting, self.cfg['capture'])

        if cfg_value is None:
            # If value is not in source configuration, try to get its default value from schema
            cfg_value = self.find_default_value_schema(cfg_setting, self.schema['properties']['capture'])

        return cfg_value

    def find_value_cfg(self, cfg_setting, iter_dict):
        """Recursively loop through elements of a configuration dictionary to find a particular index"""
        cfg_value = None
        for key, value in iter_dict.items():
            if key == cfg_setting:
                return value
            elif isinstance(value, dict):
                cfg_value = self.find_value_cfg(cfg_setting, value)
        return cfg_value

    def find_default_value_schema(self, cfg_setting, iter_dict):
        """Recursively loop through elements of the schema to find the default value of a configuration setting"""
        cfg_value = None
        for key, value in iter_dict.items():
            if key == cfg_setting:
                return value['default']
            elif isinstance(value, dict):
                cfg_value = self.find_default_value_schema(cfg_setting, value)
        return cfg_value