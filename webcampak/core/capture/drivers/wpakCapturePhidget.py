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

from ...wpakConfigObj import Config

class capturePhidget(object):
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir

        self.configPaths = parentClass.configPaths
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']
        self.dirCache = self.configPaths.getConfig('parameters')['dir_cache']
        self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']
        self.dirResources = self.configPaths.getConfig('parameters')['dir_resources']
        self.dir_bin = self.configPaths.getConfig('parameters')['dir_bin']                                                  
                                                            
        self.configGeneral = parentClass.configGeneral
        self.configSource = parentClass.configSource
        self.currentSourceId = parentClass.getSourceId()
        
        self.dirCurrentSourceTmp = self.dirSources + 'source' + self.currentSourceId +'/' + self.configPaths.getConfig('parameters')['dir_source_tmp']
        self.dirCurrentSourcePictures = self.dirSources + 'source' + self.currentSourceId +'/' + self.configPaths.getConfig('parameters')['dir_source_pictures']
        self.captureDate = parentClass.getCaptureTime().strftime("%Y%m%d%H%M%S")
        self.captureDay = parentClass.getCaptureTime().strftime("%Y%m%d")
        self.captureTimestamp = parentClass.getCaptureTime().strftime("%s")
        self.captureFilename = self.captureDate + ".txt"
        
        self.fileUtils = parentClass.fileUtils
        self.pictureTransformations = parentClass.pictureTransformations
        
    # Function: Capture
    # Description; This function is used to capture a sample picture
    # Return: Nothing
    def capture(self):
        self.log.info("capturePhidget.capture(): " + _("Start Capture"))
        self.fileUtils.CheckFilepath(self.dirCurrentSourcePictures + self.captureDay + "/" + self.configGeneral.getConfig('cfgphidgetcapturefile'))			
        Sensors = Config(self.log, self.dirCurrentSourcePictures + self.captureDay + "/" + self.configGeneral.getConfig('cfgphidgetcapturefile'))
        Sensors.setSensor(self.captureDate, "", "")
        Sensors.setSensor(self.captureDate, 'Timestamp', self.captureTimestamp)
        if self.configGeneral.getConfig('cfgphidgetactivate') == "yes":
            for ListSourceSensors in range(1,int(self.configSource.getConfig('cfgphidgetsensornb')) + 1):
                if self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] != "":
                    for ListPhidgetSensors in range(1,int(self.configGeneral.getConfig('cfgphidgetsensortypenb')) + 1):
                        if self.configGeneral.getConfig('cfgphidgetsensortype' + str(ListPhidgetSensors))[0] == self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] and self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] != "":
                            try:							
                                SensorValue = int(self.GetSensor(self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[1]))
                                PhidgetResult = round(eval(self.configGeneral.getConfig('cfgphidgetsensortype' + str(ListPhidgetSensors))[3]),1)
                                Sensors.setSensor(self.captureDate, str(self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0]), str(PhidgetResult))
                                self.log.info("capturePhidget.capture(): " + _("%(SensorType)s = %(PhidgetResult)s (source: %(SensorValue)s)") % {'SensorType': str(self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[2]), 'PhidgetResult': str(PhidgetResult), 'SensorValue': str(SensorValue)} )
                            except:
                                self.log.info("capturePhidget.capture(): " + _("Capture error"))
            if self.configSource.getConfig('cfgftpphidgetserverid') != "no" and os.path.isfile(self.dirCurrentSourcePictures + self.captureDay + "/" + self.configGeneral.getConfig('cfgphidgetcapturefile')): 
                FTPResult = FTPClass.FTPUpload(self.Cfgcurrentsource, self.configSource.getConfig('cfgftpphidgetserverid'), self.captureDay + "/", self.dirCurrentSourcePictures + self.captureDay + "/",  self.configGeneral.getConfig('cfgphidgetcapturefile'), self.Debug, self.configSource.getConfig('cfgftpphidgetserverretry'))

    # Function: GetSensor 
    # Description; This function get a sensor value
    # Return: Sensor value
    def GetSensor(self, Sensor):
        self.log.info("capturePhidget.GetSensor(): " + _("Start Capture"))
        if self.configGeneral.getConfig('cfgphidgetactivate') == "yes":
            #global PhidgetError
            #if os.path.isfile(self.Cfgphidgetbin) and PhidgetError == False:
            #print self.Cfgphidgetbin
            if os.path.isfile(self.dir_bin + self.configGeneral.getConfig('cfgphidgetbin')):
                #try:
                Command = "sudo " + self.dir_bin + self.configGeneral.getConfig('cfgphidgetbin') + ' getanalog ' + str(Sensor)
                import shlex, subprocess
                args = shlex.split(Command)
                p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                output, errors = p.communicate()
                if "ERREUR" in output:
                        PhidgetError = True
                #self.log.info(output)
                self.log.info(errors)
                SensorValue = output.strip()
                return SensorValue
                #except:
                #	self.log.info(_("Phidget: Missing device"))