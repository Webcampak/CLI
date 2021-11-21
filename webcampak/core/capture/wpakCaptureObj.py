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

from builtins import str
from builtins import object
import os
import json
import dateutil.parser
import jsonschema

from ..wpakFileUtils import fileUtils


class captureObj(object):
    """ Builds an object containing details about a capture
    
    Args:
        log: A class, the logging interface
        fileCaptureLog: A string, path to a jsonl file containing an archive of all capture objects for a specific day
    	
    Attributes:
        log: A class, the logging interface
        fileCaptureLog: A string, path to a jsonl file containing an archive of all capture objects for a specific day
        lastCapture: A dictionary, containing all values of the capture object
    """

    def __init__(self, log, fileCaptureLog=None):
        self.log = log
        self.fileCaptureLog = fileCaptureLog

        # Declare the schema used   
        # The schema is validate each time single values are set or the entire dictionary is loaded or set
        self.schema = {
            "$schema": "http://json-schema.org/draft-04/schema#"
            , "title": "captureObj"
            , "description": "Used to log details associated with a capture"
            , "type": "object"
            , "additionalProperties": False
            , "properties": {
                "storedJpgSize": {"type": "number", "description": "Size in bytes of the JPG file(s)"}
                , "storedRawSize": {"type": "number", "description": "Size in bytes of the RAW file(s)"}
                , "totalCaptureSize": {"type": "number",
                                       "description": "Size in bytes of all pictures captured (SUM storedJpgSize and storedRawSize)"}
                ,
                "scriptStartDate": {"type": ["string", "null"], "description": "Record when the capture script started"}
                , "scriptEndDate": {"type": ["string", "null"], "description": "Record when the capture script ended"}
                , "scriptRuntime": {"type": ["number", "null"], "description": "In miliseconds, record script runtime"}
                , "processedPicturesCount": {"type": "number",
                                             "description": "Number of pictures captued, in some situations multiple files might be processed in batch"}
                , "captureSuccess": {"type": ["boolean", "null"], "description": "Record if capture was successful"}
                , "captureDate": {"type": ["string", "null"], "description": "Date of the capture"}
            }
        }
        self.initCapture()

    # Getters and Setters
    def setCaptureValue(self, index, value):
        self.lastCapture[index] = value
        jsonschema.validate(self.lastCapture, self.schema)

    def getCaptureValue(self, index):
        if (index in self.lastCapture):
            return self.lastCapture[index]
        else:
            return None

    def setCapture(self, lastCapture):
        jsonschema.validate(lastCapture, self.schema)
        self.lastCapture = lastCapture

    def getCapture(self):
        jsonschema.validate(self.lastCapture, self.schema)
        return self.lastCapture

    def setCaptureFile(self, captureFile):
        self.log.info(
            "captureObj.setCaptureFile(): " + _("Capture file set to: %(captureFile)s") % {'captureFile': captureFile})
        self.captureFile = captureFile

    def getCaptureFile(self):
        return self.captureFile

    def initCapture(self):
        """Initialize the object values to 0 or None"""
        self.log.debug("captureObj.initCapture(): " + _("Start"))
        self.lastCapture = {}
        self.setCaptureValue('storedJpgSize', 0)
        self.setCaptureValue('storedRawSize', 0)
        self.setCaptureValue('totalCaptureSize', 0)
        self.setCaptureValue('scriptStartDate', None)
        self.setCaptureValue('scriptEndDate', None)
        self.setCaptureValue('scriptRuntime', None)
        self.setCaptureValue('processedPicturesCount', 0)
        self.setCaptureValue('captureSuccess', None)

    def getLastCaptureTime(self):
        """Return the last capture date from the object"""
        self.log.debug("captureObj.getLastCaptureTime(): " + _("Start"))
        try:
            lastCaptureTime = dateutil.parser.parse(self.getCaptureValue('captureDate'))
            self.log.info("captureObj.getLastCaptureTime(): " + _("Last capture time: %(lastCaptureTime)s") % {
                'lastCaptureTime': lastCaptureTime})
            return lastCaptureTime
        except:
            return None

    def loadCaptureFile(self):
        """Load the capture file into memory, if there was no previous capture, return an initialized version of the object"""
        self.log.debug("captureObj.loadCaptureFile(): " + _("Start"))
        lastCapture = self.loadJsonFile(self.getCaptureFile())
        if lastCapture != None:
            self.setCapture(lastCapture)
        else:
            self.initCapture()

    def writeCaptureFile(self):
        """Write the content of the object into a capture file"""
        self.log.debug("captureObj.writeCaptureFile(): " + _("Start"))
        if self.writeJsonFile(self.captureFile, self.getCapture()) == True:
            self.log.info(
                "captureObj.writeCaptureFile(): " + _("Successfully saved last capture file to: %(captureFile)s") % {
                    'captureFile': str(self.captureFile)})
            return True
        else:
            self.log.error("captureObj.writeCaptureFile(): " + _("Error saving last capture file"))
            return False

    def archiveCaptureFile(self):
        """Append the content of the object into a log file containing previous captures"""
        self.log.debug("captureObj.archiveCaptureFile(): " + _("Start"))
        if self.archiveJsonFile(self.fileCaptureLog, self.getCapture()) == True:
            self.log.info(
                "captureObj.archiveCaptureFile(): " + _("Successfully archived capture file to: %(captureFile)s") % {
                    'captureFile': str(self.fileCaptureLog)})
            return True
        else:
            self.log.error("captureObj.archiveCaptureFile(): " + _("Error saving last capture file"))
            return False

    def loadJsonFile(self, jsonFile):
        """Loads the content of a JSON file"""
        self.log.debug("captureObj.loadJsonFile(): " + _("Start"))
        if os.path.isfile(jsonFile):
            self.log.info(
                "captureObj.loadJsonFile(): " + _("Load JSON file into memory: %(jsonFile)s") % {'jsonFile': jsonFile})
            with open(jsonFile) as threadJsonFile:
                threadJson = json.load(threadJsonFile)
                return threadJson
        return None

    def writeJsonFile(self, jsonFile, jsonContent):
        """Write the content of a dictionary to a JSON file"""
        self.log.info("captureObj.writeJsonFile(): " + _("Writing to: %(jsonFile)s") % {'jsonFile': jsonFile})
        if fileUtils.CheckFilepath(jsonFile) != "":
            with open(jsonFile, "w") as threadJsonFile:
                threadJsonFile.write(json.dumps(jsonContent))
            return True
        return False

    def archiveJsonFile(self, jsonFile, jsonContent):
        """Append the content of a dictionary to a JSONL file"""
        self.log.info("captureObj.archiveJsonFile(): " + _("Writing to: %(jsonFile)s") % {'jsonFile': jsonFile})
        if fileUtils.CheckFilepath(jsonFile) != "":
            with open(jsonFile, "a+") as threadJsonFile:
                threadJsonFile.write(json.dumps(jsonContent) + '\n')
            return True
        return False
