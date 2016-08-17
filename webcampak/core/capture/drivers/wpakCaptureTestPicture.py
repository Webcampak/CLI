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

class captureTestPicture(object):
    """ Use a test picture as a real picture for testing purposes
    
    Args:
        log: A class, the logging interface
        fileCaptureLog: A string, path to a jsonl file containing an archive of all capture objects for a specific day
    	
    Attributes:
        log: A class, the logging interface
        fileCaptureLog: A string, path to a jsonl file containing an archive of all capture objects for a specific day
        lastCapture: A dictionary, containing all values of the capture object        
    """     
    def __init__(self, captureClass):
        self.log = captureClass.log        
        self.captureClass = captureClass
        
        self.dirResources = self.captureClass.dirResources

        self.configSource = self.captureClass.configSource
        self.currentCaptureDetails = self.captureClass.currentCaptureDetails
                
        self.dirCurrentSourceTmp = self.captureClass.dirCurrentSourceTmp
        
        self.fileUtils = self.captureClass.fileUtils
        self.timeUtils = self.captureClass.timeUtils
        self.captureUtils = self.captureClass.captureUtils        
        
        self.pictureTransformations = self.captureClass.pictureTransformations
        
    # Function: Capture
    # Description; This function is used to capture a sample picture
    # Return: True of False
    def capture(self):
        self.log.info("captureTestPicture.capture(): " + _("Start picture acquisition"))
        self.currentCaptureDetails.setCaptureValue('captureDate', self.timeUtils.getCurrentSourceTime(self.configSource).isoformat())

        captureFilename = self.captureClass.getCaptureTime().strftime("%Y%m%d%H%M%S")   
        self.fileUtils.CheckFilepath(self.dirCurrentSourceTmp + captureFilename + ".jpg")

        self.log.info("captureTestPicture.capture(): " + _("Copy test file to temporary directory"))
        shutil.copy(self.dirResources + "watermark/sample-picture.jpg", self.dirCurrentSourceTmp + captureFilename + ".jpg")
        self.log.info("captureTestPicture.capture(): " + _("Temporary capture file: %(tempCaptureFile)s") % {'tempCaptureFile': self.dirCurrentSourceTmp + captureFilename + ".jpg"} )

        self.log.info("captureTestPicture.capture(): " + _("Applying random blur effect (just to be able to see the difference from one picture to another)"))
        self.pictureTransformations.setFilesourcePath(self.dirCurrentSourceTmp + captureFilename + ".jpg")
        self.pictureTransformations.setFiledestinationPath(self.dirCurrentSourceTmp + captureFilename + ".jpg")
        self.pictureTransformations.VirtualPixel(random.randrange(0,200))

        if self.captureUtils.verifyCapturedFile(self.dirCurrentSourceTmp + captureFilename + ".jpg"):
            return [self.dirCurrentSourceTmp + captureFilename + ".jpg"]
        else:
            self.log.error("captureTestPicture.triggerCapture(): " + _("Failed to capture from Camera"))
            if os.path.isfile(self.dirCurrentSourceTmp + captureFilename + ".jpg"):
                os.remove(self.dirCurrentSourceTmp + captureFilename + ".jpg")
            if os.path.isfile(self.dirCurrentSourceTmp + captureFilename + ".jpg"):
                os.remove(self.dirCurrentSourceTmp + captureFilename + ".jpg")
            return False            
