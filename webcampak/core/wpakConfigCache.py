#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2010-2016 Eurotechnia (support@webcampak.com)
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
from .wpakConfigObj import Config

class configCache(object):
    """ A very simple class used to cache source configuration and avoid re-reading from the same file too frequently
    
    Args:
        log: A class, the logging interface
        appConfig: A class, the app config interface
        config_dir: A string, filesystem location of the configuration directory
    	sourceId: Source ID of the source to capture
        
    Attributes:
        tbc
    """

    def __init__(self, parentClass):
        self.log = parentClass.log
        self.configCache = {}

    def loadSourceConfig(self, type, filepath, sourceId = None):
        """ Load the source configuration

        Args:
            type: Type of configuration file
            filepath: Full path of the configuration file
            sourceId: Source id of the configuration file, if None, means its config-general

        """
        self.log.debug("configCache.loadSourceConfig(): " + _("Start"))
        if sourceId == None:
            sourceId = 0

        self.configCache[sourceId] = {}
        self.configCache[sourceId][type] = Config(self.log, filepath)
        return self.configCache[sourceId][type]

    def getSourceConfig(self, type, sourceId = None):
        """Get source config previously loaded"""
        self.log.debug("configCache.getSourceConfig(): " + _("Start"))
        if sourceId == None:
            sourceId = 0

        return self.configCache[sourceId][type]


