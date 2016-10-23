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
from datetime import datetime
import json
import jsonschema


class emailObj(object):
    """ Builds an object used to send emails
    
    Args:
        log: A class, the logging interface
    	
    Attributes:
        log: A class, the logging interface
    """

    def __init__(self, log, dirEmails, fileUtils):
        self.log = log
        self.dirEmails = dirEmails
        self.fileUtils = fileUtils

        self.emailObjFile = self.dirEmails + "queued/" + datetime.utcnow().strftime("%Y-%m-%d_%H%M%S_%f") + ".json"
        self.log.info(
            "emailObj(): " + _("Setting default filename to: %(emailObjFile)s") % {'emailObjFile': self.emailObjFile})

        # Declare the schema used   
        # The schema is validate each time single values are set or the entire dictionary is loaded or set
        """
        {
            "status": "queued",
            "hash": "4da2c5ea1cd913dda193f8d629d7399b",
            "content": {
                "FROM": {
                    "name": "Webcampak on behalf of Root Root",
                    "email": "root@webcampak.com"
                },
                "TO": {
                    "0": {
                        "email": "francois@webcampak.com"
                    }
                },
                "BCC": {
                    "0": {
                        "email": "francois@webcampak.com"
                    }
                },                
                "CC": null,
                "BODY": "Hello, <br><br>You'll find enclosed an interesting picture<br><br>Best Regards.",
                "SUBJECT": "Webcampak picture",
                "ATTACHMENTS": {
                    "0": {
                        "PATH": "/home/webcampak/webcampak/sources/source16/pictures/20160719/20160719040810.jpg",
                        "NAME": "20160719040810.jpg"
                    }
                }
            },
            "logs": {}
        }                
        """

        self.schema = {
            "$schema": "http://json-schema.org/draft-04/schema#"
            , "title": "emailObj"
            , "description": "Used to content of an email"
            , "type": "object"
            , "additionalProperties": False
            , "properties": {
                "status": {"type": "string", "description": "Status ot the email (queued, failed, sent)"}
                , "hash": {"type": ["string", "null"], "description": "Hash used to identify the email"}
                , "content": {
                    "type": "object"
                    , "description": "Size in bytes of all pictures captured (SUM storedJpgSize and storedRawSize)"
                    , "properties": {
                        "FROM": {
                            "type": "object"
                            , "properties": {
                                "name": {"type": "string", "description": "Full text name of the sender"}
                                , "email": {"type": "string", "description": "Email of the sender"}
                            }

                        }, "TO": {
                            "type": "array"
                            , "items": {
                                "type": "object"
                                , "properties": {
                                    "name": {"type": "string", "description": "Full text name of the sender"}
                                    , "email": {"type": "string", "description": "Email of the sender"}
                                }
                            }
                        }, "CC": {
                            "type": "array"
                            , "items": {
                                "type": "object"
                                , "properties": {
                                    "name": {"type": "string", "description": "Full text name of the sender"}
                                    , "email": {"type": "string", "description": "Email of the sender"}
                                }
                            }
                        }, "BCC": {
                            "type": "array"
                            , "items": {
                                "type": "object"
                                , "properties": {
                                    "name": {"type": "string", "description": "Full text name of the sender"}
                                    , "email": {"type": "string", "description": "Email of the sender"}
                                }
                            }
                        }
                        , "BODY": {"type": ["string", "null"], "description": "Body of the email"}
                        , "SUBJECT": {"type": ["string", "null"], "description": "Subject of the email"}
                        , "ATTACHMENTS": {
                            "type": "array"
                            , "items": {
                                "type": "object"
                                , "properties": {
                                    "PATH": {"type": "string", "description": "Full text name of the sender"}
                                    , "NAME": {"type": "string", "description": "Email of the sender"}
                                    , "WIDTH": {"type": "number",
                                                "description": "Width of the attachment, height will be calculated automatically"}
                                }
                            }
                        }
                    }
                }
                , "logs": {"type": "array", "items": {"type": "string"}}
            }
        }
        self.initEmail()

    def initEmail(self):
        """Initialize the object values to 0 or None"""
        self.log.debug("emailObj.initEmail(): " + _("Start"))
        self.emailObj = {}
        self.emailObj['status'] = 'queued'
        self.emailObj['hash'] = None
        self.emailObj['content'] = {}
        self.emailObj['content']['FROM'] = []
        self.emailObj['content']['TO'] = []
        self.emailObj['content']['CC'] = []
        self.emailObj['content']['BODY'] = None
        self.emailObj['content']['SUBJECT'] = None
        self.emailObj['content']['ATTACHMENTS'] = []
        self.emailObj['logs'] = []

    # Getters and Setters
    def setStatus(self, value):
        self.emailObj['status'] = value

    def getStatus(self):
        return self.emailObj['status']

    def setHash(self, value):
        self.emailObj['hash'] = value

    def getHash(self):
        return self.emailObj['hash']

    def setFrom(self, value):
        self.emailObj['content']['FROM'] = value

    def getFrom(self):
        return self.emailObj['content']['FROM']

    def setFromEmail(self, value):
        self.emailObj['content']['FROM']['email'] = value

    def getFromEmail(self):
        return self.emailObj['content']['FROM']['email']

    def setTo(self, value):
        self.emailObj['content']['TO'] = value

    def addTo(self, value):
        self.emailObj['content']['TO'].append(value)

    def getTo(self):
        return self.emailObj['content']['TO']

    def setCc(self, value):
        self.emailObj['content']['CC'] = value

    def addCc(self, value):
        self.emailObj['content']['CC'].append(value)

    def getCc(self):
        return self.emailObj['content']['CC']

    def setBcc(self, value):
        self.emailObj['content']['CC'] = value

    def addBcc(self, value):
        self.emailObj['content']['CC'].append(value)

    def getBcc(self):
        return self.emailObj['content']['CC']

    def setBody(self, value):
        self.emailObj['content']['BODY'] = value

    def getBody(self):
        return self.emailObj['content']['BODY']

    def setSubject(self, value):
        self.emailObj['content']['SUBJECT'] = value

    def getSubject(self):
        return self.emailObj['content']['SUBJECT']

    def setAttachments(self, value):
        self.emailObj['content']['ATTACHMENTS'] = value

    def addAttachment(self, value):
        self.emailObj['content']['ATTACHMENTS'].append(value)

    def getAttachments(self):
        return self.emailObj['content']['ATTACHMENTS']

    def setEmailObject(self, emailObj):
        jsonschema.validate(emailObj, self.schema)
        self.emailObj = emailObj

    def getEmailObject(self):
        jsonschema.validate(self.emailObj, self.schema)
        return self.emailObj

    def setEmailObjectFile(self, emailObjFile):
        self.log.info("emailObj.setEmailObjectFile(): " + _("Email Object file set to: %(emailObjFile)s") % {
            'emailObjFile': emailObjFile})
        self.emailObjFile = emailObjFile

    def getEmailObjectFile(self):
        return self.emailObjFile

    def loadEmailObjectFile(self):
        """Load the email object into memory, if the file does not exists returns a empty object"""
        self.log.debug("emailObj.loadEmailObjectFile(): " + _("Start"))
        lastCapture = self.loadJsonFile(self.getEmailObjectFile())
        if lastCapture != None:
            self.setCapture(lastCapture)
        else:
            self.initEmail()

    def writeEmailObjectFile(self):
        """Write the content of the object into a capture file"""
        self.log.debug("emailObj.writeEmailObjectFile(): " + _("Start"))
        if self.writeJsonFile(self.emailObjFile, self.getEmailObject()) == True:
            self.log.info(
                "emailObj.writeEmailObjectFile(): " + _("Successfully added email to queue, file: %(emailObjFile)s") % {
                    'emailObjFile': str(self.emailObjFile)})
            return True
        else:
            self.log.error("emailObj.writeEmailObjectFile(): " + _("Error adding email to queue"))
            return False

    def loadJsonFile(self, jsonFile):
        """Loads the content of a JSON file"""
        self.log.debug("emailObj.loadJsonFile(): " + _("Start"))
        if os.path.isfile(jsonFile):
            self.log.info(
                "emailObj.loadJsonFile(): " + _("Load JSON file into memory: %(jsonFile)s") % {'jsonFile': jsonFile})
            with open(jsonFile) as threadJsonFile:
                threadJson = json.load(threadJsonFile)
                return threadJson
        return None

    def writeJsonFile(self, jsonFile, jsonContent):
        """Write the content of a dictionary to a JSON file"""
        self.log.info("emailObj.writeJsonFile(): " + _("Writing to: %(jsonFile)s") % {'jsonFile': jsonFile})
        if self.fileUtils.CheckFilepath(jsonFile) != "":
            with open(jsonFile, "w") as threadJsonFile:
                threadJsonFile.write(json.dumps(jsonContent))
            return True
        return False
