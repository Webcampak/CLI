#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2010-2012 Infracom & Eurotechnia (support@webcampak.com)
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
import sys
import yaml

from configobj import ConfigObj


# This class is used to set or get values from configobj functions
class Config:
    def __init__(self, log, filePath):
        self.filePath = filePath
        self.log = log
        if os.path.splitext(filePath)[1] == '.yml':
            self.configType = 'YML'
            with open(filePath, 'r') as ymlfile:
                self.currentConfig = yaml.load(ymlfile)
        elif os.path.splitext(filePath)[1] == '.cfg' or os.path.splitext(filePath)[1] == '.txt':
            self.configType = 'INI'
            self.currentConfig = ConfigObj(self.filePath)
        else:
            self.log.error("Config.init(): Unable to identify config file format, exiting...")
            sys.exit()
        self.log.info("Config.init(): Loaded " + self.configType + " config file: " + filePath)

    # Function: getFullConfig
    # Description; Function used to get full configuration file
    # Return: configfile
    def getFullConfig(self):
        return self.currentConfig

    # Function: getConfig
    # Description; Function used to get configuration settings
    ## key: configuration key
    # Return: configuration value
    def getConfig(self, key):
        return self.currentConfig[key]

    # Function: setConfig
    # Description; Function used to set configuration settings
    ## key: configuration key
    ## value: configuration value
    # Return: Nothing
    def setConfig(self, key, value):
        self.currentConfig[key] = value
        # print "Ecriture desactivee: " + key + " = " + value
        self.currentConfig.write()

    # Function: setSensor
    # Description; Function used to record sensor value, it differs from configuration settings by using subsections
    ## section: sensors section (correspond to a capture)
    ## key: sensor key (Temperature, Luminosity)
    ## value: configuration value
    # Return: Nothing
    def setSensor(self, section, key, value):
        if value == "" and key == "":
            self.currentConfig[section] = {}
        else:
            self.currentConfig[section][key] = value
        self.currentConfig.write()

    # Function: getSensor
    # Description; Function used to get sensor value, it differs from configuration settings by using subsections
    ## section: sensors section (correspond to a capture)
    ## key: sensor key (Temperature, Luminosity)
    # Return: Nothing
    def getSensor(self, section, key):
        try:
            return self.currentConfig[section][key]
        except:
            return False

    # Function: getSensorFile
    # Description; Get all values of a sensor file
    # Return: An object containing all values
    def getSensorFile(self):
        try:
            return self.currentConfig
        except:
            return False

    # Function: setStat
    # Description; Function used to set stat values
    ## key: configuration key
    ## value: configuration value
    # Return: Nothing
    def setStat(self, key, value):
        self.currentConfig[key] = value
        # print "Ecriture desactivee: " + key + " = " + value
        self.currentConfig.write()

    # Function: getStat
    # Description; Function used to get stat values
    ## key: configuration key
    # Return: configuration value
    def getStat(self, key):
        try:
            return self.currentConfig[key]
        except:
            return 0
