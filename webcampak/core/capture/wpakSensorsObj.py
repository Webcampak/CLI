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

import os
import json
import jsonschema

from ..wpakFileUtils import fileUtils


class sensorsObj(object):
    """ Builds an object containing details about a capture

    Args:
        log: A class, the logging interface
        fileSensorsLog: A string, path to a jsonl file containing an archive of all capture objects for a specific day

    Attributes:
        log: A class, the logging interface
        fileSensorsLog: A string, path to a jsonl file containing an archive of all capture objects for a specific day
        lastSensors: A dictionary, containing all values of the capture object
    """

    def __init__(self, log, fileSensorsLog=None):
        self.log = log
        self.fileSensorsLog = fileSensorsLog

        # Declare the schema used
        # The schema is validate each time single values are set or the entire dictionary is loaded or set
        self.schema = {
            "$schema": "http://json-schema.org/draft-04/schema#"
            , "title": "sensorsObj"
            , "description": "Used to log captured sensors value"
            , "type": "object"
            , "additionalProperties": False
            , "properties": {
                "date": {"type": ["string", "null"], "description": "Date of the capture"}
                , "interval": {"type": ["number", "null"], "description": "Capture interval configured for the source, in seconds"}
                , "sensors": {
                    "type": ["object", "null"]
                    , "description": "Sensor values captures on a phidget board"
                    , "patternProperties": {
                        "^(.)+": {
                            "type": "object"
                            , "properties": {
                                "description": {"type": "string", "description": "Description of the sensor"}
                                , "type": {"type": "string", "description": "Sensor Type"}
                                , "value": {"type": "number", "description": "Captured value after applying formula"}
                                ,
                                "valueRaw": {"type": "number", "description": "Captured value before applying formula"}
                            }
                        }
                    }
                }
            }
        }
        self.initSensors()

    # Getters and Setters
    def setSensorsValue(self, index, value):
        self.lastSensors[index] = value
        jsonschema.validate(self.lastSensors, self.schema)

    def getSensorsValue(self, index):
        if (self.lastSensors.has_key(index)):
            return self.lastSensors[index]
        else:
            return None

    def setSensors(self, lastSensors):
        jsonschema.validate(lastSensors, self.schema)
        self.lastSensors = lastSensors

    def getSensors(self):
        jsonschema.validate(self.lastSensors, self.schema)
        return self.lastSensors

    def initSensors(self):
        """Initialize the object values to 0 or None"""
        self.log.debug("sensorsObj.initSensors(): " + _("Start"))
        self.lastSensors = {}
        self.setSensorsValue('date', None)
        self.setSensorsValue('sensors', {})

    def archiveSensorsFile(self):
        """Append the content of the object into a log file containing previous captures"""
        self.log.debug("sensorsObj.archiveSensorsFile(): " + _("Start"))
        print self.getSensors()
        if self.archiveJsonFile(self.fileSensorsLog, self.getSensors()) == True:
            self.log.info(
                "sensorsObj.archiveSensorsFile(): " + _("Successfully archived sensor file to: %(captureFile)s") % {
                    'captureFile': str(self.fileSensorsLog)})
            return True
        else:
            self.log.error("sensorsObj.archiveSensorsFile(): " + _("Error saving last capture file"))
            return False

    def loadJsonFile(self, jsonFile):
        """Loads the content of a JSON file"""
        self.log.debug("sensorsObj.loadJsonFile(): " + _("Start"))
        if os.path.isfile(jsonFile):
            self.log.info(
                "sensorsObj.loadJsonFile(): " + _("Load JSON file into memory: %(jsonFile)s") % {'jsonFile': jsonFile})
            with open(jsonFile) as threadJsonFile:
                threadJson = json.load(threadJsonFile)
                return threadJson
        return None

    def writeJsonFile(self, jsonFile, jsonContent):
        """Write the content of a dictionary to a JSON file"""
        self.log.info("sensorsObj.writeJsonFile(): " + _("Writing to: %(jsonFile)s") % {'jsonFile': jsonFile})
        if fileUtils.CheckFilepath(jsonFile) != "":
            with open(jsonFile, "w") as threadJsonFile:
                threadJsonFile.write(json.dumps(jsonContent))
            return True
        return False

    def archiveJsonFile(self, jsonFile, jsonContent):
        """Append the content of a dictionary to a JSONL file"""
        self.log.info("sensorsObj.archiveJsonFile(): " + _("Writing to: %(jsonFile)s") % {'jsonFile': jsonFile})
        if fileUtils.CheckFilepath(jsonFile) != "":
            with open(jsonFile, "a+") as threadJsonFile:
                threadJsonFile.write(json.dumps(jsonContent) + '\n')
            return True
        return False
