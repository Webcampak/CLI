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
import time

from wpakConfigObj import Config
from wpakFileUtils import fileUtils
from wpakPhidgets import phidgets

class phidgetsUtils(object):
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir
        
        self.configGeneral = parentClass.configGeneral
        self.configSource = parentClass.configSource

        self.dirBin = parentClass.dirBin        
        self.binPhidgets = self.dirBin + self.configGeneral.getConfig('cfgphidgetbin')
        
    def restartCamera(self):
        """Restart a gphoto camera based on configured ports"""
        self.log.debug("phidgetsUtils.restartCamera(): " + _("Start"))   
        if self.configGeneral.getConfig('cfgphidgetactivate') == "yes":
            phidgetPort = int(self.configSource.getConfig('cfgphidgetcameraport'))
            phidgetsClass = phidgets(self)
            outputValue = phidgetsClass.setOutputValue(phidgetPort, 0)
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget port set to:  %(outputValue)s)") % {'outputValue': str(outputValue)})
            if outputValue != 0:
                self.log.error("phidgetsUtils.restartCamera(): " + _("Error Unable to set port to 0"))
            time.sleep(5)   
            outputValue = phidgetsClass.setOutputValue(phidgetPort, 1)
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget port set to:  %(outputValue)s)") % {'outputValue': str(outputValue)})
            if outputValue != 1:
                self.log.error("phidgetsUtils.restartCamera(): " + _("Error Unable to set port to 1"))            
 

        