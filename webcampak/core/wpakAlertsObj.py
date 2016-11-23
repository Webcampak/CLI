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
import dateutil.parser
import jsonschema

from wpakFileUtils import fileUtils


class alertObj(object):
    """ Builds an object containing details about an alert
    
    Args:
        log: A class, the logging interface
        fileAlertsLog: A string, path to a jsonl file containing an archive of all capture objects for a specific day
    	
    Attributes:
        log: A class, the logging interface
        fileAlertsLog: A string, path to a jsonl file containing an archive of all capture objects for a specific day
        lastAlert: A dictionary, containing all values of the capture object
    """

    def __init__(self, log, fileAlertsLog=None):
        self.log = log
        self.fileAlertsLog = fileAlertsLog

        # Declare the schema used   
        # The schema is validate each time single values are set or the entire dictionary is loaded or set
        self.schema = {
            "$schema": "http://json-schema.org/draft-04/schema#"
            , "title": "alertObj"
            , "description": "Used to log details associated with a capture"
            , "type": "object"
            , "additionalProperties": False
            , "properties": {
                "sourceid": {"type": ["number", "null"], "description": "ID of the source"}
                , "status": {"type": ["string", "null"], "description": "Status of the alert (GOOD, ERROR, LATE)"}
                , "currentSourceTime": {"type": ["string", "null"], "description": "Current time for the source"}
                , "lastCaptureTime": {"type": ["string", "null"], "description": "Last time capture was done according to schedule"}
                , "nextCaptureTime": {"type": ["string", "null"], "description": "Next time a capture is scheduled"}
                , "secondsSinceLastCapture": {"type": ["number", "null"], "description": "Number of seconds between current source time and last schedule-based capture"}
                , "missedCapture": {"type": ["number", "null"], "description": "Number of missed captures as per the calendar"}
                , "incidentFile": {"type": ["string", "null"], "description": "Filename used to record the incident"}
            }
        }
        self.initAlert()

    # Getters and Setters
    def setAlertValue(self, index, value):
        self.lastAlert[index] = value
        jsonschema.validate(self.lastAlert, self.schema)

    def getAlertValue(self, index):
        if (self.lastAlert.has_key(index)):
            return self.lastAlert[index]
        else:
            return None

    def setAlert(self, lastAlert):
        jsonschema.validate(lastAlert, self.schema)
        self.lastAlert = lastAlert

    def getAlert(self):
        jsonschema.validate(self.lastAlert, self.schema)
        return self.lastAlert

    def setAlertFile(self, captureFile):
        self.log.info(
            "alertObj.setAlertFile(): " + _("Alert file set to: %(captureFile)s") % {'captureFile': captureFile})
        self.captureFile = captureFile

    def getAlertFile(self):
        return self.captureFile

    def initAlert(self):
        """Initialize the object values to 0 or None"""
        self.log.debug("alertObj.initAlert(): " + _("Start"))
        self.lastAlert = {}

    def getLastAlertTime(self):
        """Return the last capture date from the object"""
        self.log.debug("alertObj.getLastAlertTime(): " + _("Start"))
        try:
            lastAlertTime = dateutil.parser.parse(self.getAlertValue('captureDate'))
            self.log.info("alertObj.getLastAlertTime(): " + _("Last capture time: %(lastAlertTime)s") % {
                'lastAlertTime': lastAlertTime})
            return lastAlertTime
        except:
            return None

    def loadAlertFile(self):
        """Load the capture file into memory, if there was no previous capture, return an initialized version of the object"""
        self.log.debug("alertObj.loadAlertFile(): " + _("Start"))
        lastAlert = self.loadJsonFile(self.getAlertFile())
        if lastAlert != None:
            self.setAlert(lastAlert)
        else:
            self.initAlert()

    def writeAlertFile(self):
        """Write the content of the object into a capture file"""
        self.log.debug("alertObj.writeAlertFile(): " + _("Start"))
        if self.writeJsonFile(self.captureFile, self.getAlert()) == True:
            self.log.info(
                "alertObj.writeAlertFile(): " + _("Successfully saved last capture file to: %(captureFile)s") % {
                    'captureFile': str(self.captureFile)})
            return True
        else:
            self.log.error("alertObj.writeAlertFile(): " + _("Error saving last capture file"))
            return False

    def archiveAlertFile(self):
        """Append the content of the object into a log file containing previous captures"""
        self.log.debug("alertObj.archiveAlertFile(): " + _("Start"))
        if self.archiveJsonFile(self.fileAlertsLog, self.getAlert()) == True:
            self.log.info(
                "alertObj.archiveAlertFile(): " + _("Successfully archived capture file to: %(captureFile)s") % {
                    'captureFile': str(self.fileAlertsLog)})
            return True
        else:
            self.log.error("alertObj.archiveAlertFile(): " + _("Error saving last capture file"))
            return False

    def loadJsonFile(self, jsonFile):
        """Loads the content of a JSON file"""
        self.log.debug("alertObj.loadJsonFile(): " + _("Start"))
        if os.path.isfile(jsonFile):
            self.log.info(
                "alertObj.loadJsonFile(): " + _("Load JSON file into memory: %(jsonFile)s") % {'jsonFile': jsonFile})
            with open(jsonFile) as threadJsonFile:
                threadJson = json.load(threadJsonFile)
                return threadJson
        return None

    def writeJsonFile(self, jsonFile, jsonContent):
        """Write the content of a dictionary to a JSON file"""
        self.log.info("alertObj.writeJsonFile(): " + _("Writing to: %(jsonFile)s") % {'jsonFile': jsonFile})
        if fileUtils.CheckFilepath(jsonFile) != "":
            with open(jsonFile, "w") as threadJsonFile:
                threadJsonFile.write(json.dumps(jsonContent))
            return True
        return False

    def archiveJsonFile(self, jsonFile, jsonContent):
        """Append the content of a dictionary to a JSONL file"""
        self.log.info("alertObj.archiveJsonFile(): " + _("Writing to: %(jsonFile)s") % {'jsonFile': jsonFile})
        if fileUtils.CheckFilepath(jsonFile) != "":
            with open(jsonFile, "a+") as threadJsonFile:
                threadJsonFile.write(json.dumps(jsonContent) + '\n')
            return True
        return False
