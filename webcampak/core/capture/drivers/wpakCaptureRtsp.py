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


class captureRtsp(object):
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir
        self.captureClass = parentClass

        self.configPaths = parentClass.configPaths
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']
        self.dirCache = self.configPaths.getConfig('parameters')['dir_cache']
        self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']
        self.dirResources = self.configPaths.getConfig('parameters')['dir_resources']

        self.configGeneral = parentClass.configGeneral
        self.configSource = parentClass.configSource
        self.currentSourceId = parentClass.getSourceId()
        self.currentCaptureDetails = parentClass.currentCaptureDetails

        self.dirCurrentSourceTmp = self.dirSources + 'source' + self.currentSourceId + '/' + \
                                   self.configPaths.getConfig('parameters')['dir_source_tmp']

        self.fileUtils = parentClass.fileUtils
        self.captureUtils = parentClass.captureUtils
        self.timeUtils = parentClass.timeUtils
        self.pictureTransformations = parentClass.pictureTransformations

    # Function: Capture
    # Description; This function is used to capture a picture
    # Return: Nothing
    def capture(self):
        self.log.debug("captureRtsp.capture(): " + _("Start"))
        self.log.info("captureTestPicture.capture(): " + _("Starting the capture process"))
        self.currentCaptureDetails.setCaptureValue('captureDate',
                                                   self.timeUtils.getCurrentSourceTime(self.configSource).isoformat())

        self.captureFilename = self.captureClass.getCaptureTime().strftime("%Y%m%d%H%M%S")
        self.fileUtils.CheckFilepath(self.dirCurrentSourceTmp + self.captureFilename + ".jpg")

        self.log.info("captureRtsp.capture(): " + _("Starting capture process, URL: %(URL)s ") % {
            'URL': self.configSource.getConfig('cfgsourcewebfileurl')})
        Command = "avconv -i " + self.configSource.getConfig(
            'cfgsourcewebfileurl') + " -ss 00:00:01.500 -f image2 -vframes 1 " + self.dirCurrentSourceTmp + self.captureFilename + ".jpg"

        self.log.info(
            "captureRtsp.capture(): " + _("Capture Command: %(captureCommand)s ") % {'captureCommand': Command})

        os.system(Command)
        FileSourceSize = 0
        if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".jpg"):
            FileSourceSize = os.path.getsize(self.dirCurrentSourceTmp + self.captureFilename + ".jpg")

        if FileSourceSize < int(self.configSource.getConfig('cfgcaptureminisize')):
            self.log.info("captureRtsp.capture(): " + _("Retrying capture process, URL: %(URL)s ") % {
                'URL': self.configSource.getConfig('cfgsourcewebfileurl')})
            os.system(Command)
            if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".jpg"):
                FileSourceSize = os.path.getsize(self.dirCurrentSourceTmp + self.captureFilename + ".jpg")
        if FileSourceSize < int(self.configSource.getConfig('cfgcaptureminisize')):
            return False
        else:
            if self.captureUtils.verifyCapturedFile(self.dirCurrentSourceTmp + self.captureFilename + ".jpg"):
                return [self.dirCurrentSourceTmp + self.captureFilename + ".jpg"]
            else:
                self.log.error("captureRtsp.triggerCapture(): " + _("Failed to capture from Camera"))
                if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".jpg"):
                    os.remove(self.dirCurrentSourceTmp + self.captureFilename + ".jpg")
                if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".raw"):
                    os.remove(self.dirCurrentSourceTmp + self.captureFilename + ".raw")
                return False
