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
import os, uuid, signal
from datetime import tzinfo, timedelta, datetime
from pytz import timezone
import shutil
import pytz
import json
import dateutil.parser
import zlib
import gzip
import gettext
import random
import jsonschema

from ..wpakFileUtils import fileUtils


class videoObj(object):
    """ Builds an object containing details about a video processing
    
    Args:
        log: A class, the logging interface
        fileVideoLog: A string, path to a jsonl file containing an archive of all video objects for a specific day
    	
    Attributes:
        log: A class, the logging interface
        fileVideoLog: A string, path to a jsonl file containing an archive of all video objects for a specific day
        lastVideo: A dictionary, containing all values of the video object        
    """

    def __init__(self, log, fileVideoLog=None):
        self.log = log
        self.fileVideoLog = fileVideoLog

        # Declare the schema used   
        # The schema is validate each time single values are set or the entire dictionary is loaded or set
        self.schema = {
            "$schema": "http://json-schema.org/draft-04/schema#"
            , "title": "videoObj"
            , "description": "Used to log details associated with a video"
            , "type": "object"
            , "additionalProperties": False
            , "properties": {
                "type": {"type": ["string", "null"],
                         "description": "Type of the video instance, usually daily, custom or postprod"}
                , "sourceFiles": {"type": ["number", "null"],
                                  "description": "Number of JPG files copied to the directory for processing"}
                , "scriptStartDate": {"type": ["string", "null"], "description": "Record when the video script started"}
                , "scriptEndDate": {"type": ["string", "null"], "description": "Record when the video script ended"}
                , "scriptRuntime": {"type": ["number", "null"], "description": "In miliseconds, record script runtime"}
                , "formats": {
                    "type": "array"
                    , "items": {
                        "type": "object"
                        , "properties": {
                            "name": {"type": "string",
                                     "description": "Name of the format (usually 1080p, 720p, 480p, custom)"}
                            , "avi": {"type": "number", "description": "Size of the created video"}
                            , "mp4": {"type": "number", "description": "Size of the created video"}
                            , "runtime": {"type": "number", "description": "Runtime to create the video"}
                        }
                    }
                }
            }
        }
        self.initVideo()

    # Getters and Setters
    def setVideoValue(self, index, value):
        self.lastVideo[index] = value
        jsonschema.validate(self.lastVideo, self.schema)

    def getVideoValue(self, index):
        if (index in self.lastVideo):
            return self.lastVideo[index]
        else:
            return None

    def setFormats(self, value):
        self.lastVideo['formats'] = value

    def addFormat(self, value):
        self.lastVideo['formats'].append(value)

    def getFormats(self):
        return self.lastVideo['formats']

    def setVideo(self, lastVideo):
        jsonschema.validate(lastVideo, self.schema)
        self.lastVideo = lastVideo

    def getVideo(self):
        jsonschema.validate(self.lastVideo, self.schema)
        return self.lastVideo

    def setVideoFile(self, videoFile):
        self.log.info("videoObj.setVideoFile(): " + _("Video file set to: %(videoFile)s") % {'videoFile': videoFile})
        self.videoFile = videoFile

    def getVideoFile(self):
        return self.videoFile

    def initVideo(self):
        """Initialize the object values to 0 or None"""
        self.log.debug("videoObj.initVideo(): " + _("Start"))
        self.lastVideo = {}
        self.lastVideo['scriptStartDate'] = None
        self.lastVideo['scriptEndDate'] = None
        self.lastVideo['scriptRuntime'] = None
        self.lastVideo['type'] = None
        self.lastVideo['formats'] = []

    def loadVideoFile(self):
        """Load the video file into memory, if there was no previous video, return an initialized version of the object"""
        self.log.debug("videoObj.loadVideoFile(): " + _("Start"))
        lastVideo = self.loadJsonFile(self.getVideoFile())
        if lastVideo != None:
            self.setVideo(lastVideo)
        else:
            self.initVideo()

    def writeVideoFile(self):
        """Write the content of the object into a video file"""
        self.log.debug("videoObj.writeVideoFile(): " + _("Start"))
        if self.writeJsonFile(self.videoFile, self.getVideo()) == True:
            self.log.info("videoObj.writeVideoFile(): " + _("Successfully saved last video file to: %(videoFile)s") % {
                'videoFile': str(self.videoFile)})
            return True
        else:
            self.log.error("videoObj.writeVideoFile(): " + _("Error saving last video file"))
            return False

    def archiveVideoFile(self):
        """Append the content of the object into a log file containing previous videos"""
        self.log.debug("videoObj.archiveVideoFile(): " + _("Start"))
        if self.archiveJsonFile(self.fileVideoLog, self.getVideo()) == True:
            self.log.info("videoObj.archiveVideoFile(): " + _("Successfully archived video file to: %(videoFile)s") % {
                'videoFile': str(self.fileVideoLog)})
            return True
        else:
            self.log.error("videoObj.archiveVideoFile(): " + _("Error saving last video file"))
            return False

    def loadJsonFile(self, jsonFile):
        """Loads the content of a JSON file"""
        self.log.debug("videoObj.loadJsonFile(): " + _("Start"))
        if os.path.isfile(jsonFile):
            self.log.info(
                "videoObj.loadJsonFile(): " + _("Load JSON file into memory: %(jsonFile)s") % {'jsonFile': jsonFile})
            with open(jsonFile) as threadJsonFile:
                threadJson = json.load(threadJsonFile)
                return threadJson
        return None

    def writeJsonFile(self, jsonFile, jsonContent):
        """Write the content of a dictionary to a JSON file"""
        self.log.info("videoObj.writeJsonFile(): " + _("Writing to: %(jsonFile)s") % {'jsonFile': jsonFile})
        if fileUtils.CheckFilepath(jsonFile) != "":
            with open(jsonFile, "w") as threadJsonFile:
                threadJsonFile.write(json.dumps(jsonContent))
            return True
        return False

    def archiveJsonFile(self, jsonFile, jsonContent):
        """Append the content of a dictionary to a JSONL file"""
        self.log.info("videoObj.archiveJsonFile(): " + _("Writing to: %(jsonFile)s") % {'jsonFile': jsonFile})
        if fileUtils.CheckFilepath(jsonFile) != "":
            with open(jsonFile, "a+") as threadJsonFile:
                threadJsonFile.write(json.dumps(jsonContent) + '\n')
            return True
        return False
