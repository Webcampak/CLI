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
import shutil

from ..wpakCaptureObj import captureObj


class captureWpak(object):
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
        self.dirCurrentSourcePictures = self.dirSources + 'source' + self.currentSourceId + '/' + \
                                        self.configPaths.getConfig('parameters')['dir_source_pictures']
        self.dirCurrentSourceLive = self.dirSources + 'source' + self.currentSourceId + '/' + \
                                    self.configPaths.getConfig('parameters')['dir_source_live']

        # self.captureDate = parentClass.getCaptureTime().strftime("%Y%m%d%H%M%S")
        # self.captureClass.getCaptureFilename() = self.captureDate + ".jpg"

        self.fileUtils = parentClass.fileUtils
        self.captureUtils = parentClass.captureUtils
        self.timeUtils = parentClass.timeUtils
        self.pictureTransformations = parentClass.pictureTransformations

    # Function: Capture
    # Description; This function is used to capture a picture
    # Return: Nothing
    def capture(self):
        self.log.info("captureWpak.capture(): " + _("Start"))
        getFromSourceID = self.configSource.getConfig('cfgsourcewpakgetsourceid')
        if getFromSourceID == self.currentSourceId:
            self.log.error("captureWpak.capture(): " + _("A source cannot capture from itself"))
            return False
        elif (int(getFromSourceID) > 0):
            self.log.info(
                "captureWpak.capture(): " + _("Looking for JPG file into source %(getFromSourceID)s live directory") % {
                    'getFromSourceID': str(getFromSourceID)})
            dstSourceLiveDir = self.dirSources + 'source' + getFromSourceID + '/' + \
                               self.configPaths.getConfig('parameters')['dir_source_live']
            if os.path.isfile(dstSourceLiveDir + "last-capture.jpg"):
                # Get last capture date
                self.lastCaptureDetails = captureObj(self.log)
                self.lastCaptureDetails.setCaptureFile(dstSourceLiveDir + "last-capture.json")
                self.lastCaptureDetails.loadCaptureFile()
                remotePictureDate = self.lastCaptureDetails.getLastCaptureTime()
                self.captureClass.setCaptureTime(remotePictureDate)
                self.captureClass.setCaptureFilename(self.captureClass.getCaptureTime().strftime("%Y%m%d%H%M%S"))
                self.captureFilename = self.captureClass.getCaptureFilename()

                if self.captureUtils.getArchivedSize(self.captureFilename, "jpg") == 0:  # Only process the capture
                    self.currentCaptureDetails.setCaptureValue('captureDate',
                                                               self.captureClass.getCaptureTime().isoformat())

                    self.log.info("captureWpak.capture(): " + _(
                        "Copying file last-capture.jpg  from %(sourceLiveDirectory)s to %(Cfgtmpdir)s") % {
                                      'sourceLiveDirectory': dstSourceLiveDir, 'Cfgtmpdir': self.dirCurrentSourceTmp})
                    shutil.copy(dstSourceLiveDir + "last-capture.jpg",
                                self.dirCurrentSourceTmp + self.captureFilename + ".jpg")
                    if os.path.isfile(dstSourceLiveDir + "last-capture.raw") and self.configSource.getConfig(
                            'cfgprocessraw') == "yes":
                        self.log.info("captureWpak.capture(): " + _(
                            "Copying file last-capture.raw  from %(sourceLiveDirectory)s to %(Cfgtmpdir)s") % {
                                          'sourceLiveDirectory': dstSourceLiveDir,
                                          'Cfgtmpdir': self.dirCurrentSourceTmp})
                        shutil.copy(dstSourceLiveDir + "last-capture.raw",
                                    self.dirCurrentSourceTmp + self.captureFilename + ".raw")
                    else:
                        self.log.info("captureWpak.capture(): " + _(
                            "Raw processing is either disabled or last-capture.raw do not exist in %(sourceLiveDirectory)s live directory") % {
                                          'sourceLiveDirectory': dstSourceLiveDir})

                    if self.captureUtils.verifyCapturedFile(self.dirCurrentSourceTmp + self.captureFilename + ".jpg"):
                        return [self.dirCurrentSourceTmp + self.captureFilename + ".jpg"]
                    else:
                        self.log.error("captureWpak.triggerCapture(): " + _("Failed to capture from Camera"))
                        if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".jpg"):
                            os.remove(self.dirCurrentSourceTmp + self.captureFilename + ".jpg")
                        if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".raw"):
                            os.remove(self.dirCurrentSourceTmp + self.captureFilename + ".raw")
                        return False

                else:
                    self.log.error("captureWpak.capture(): " + _("File already captured: %(captureFilename)s") % {
                        'captureFilename': str(self.captureFilename + ".jpg")})
                    return False
            else:
                self.log.info("captureWpak.capture(): " + _(
                    "Error: last-capture.jpg file is missing in %(sourceLiveDirectory)s directory") % {
                                  'sourceLiveDirectory': dstSourceLiveDir})
                return False
        else:
            self.log.info("captureWpak.capture(): " + _("Source %(getFromSourceID)s is not a valid source") % {
                'getFromSourceID': str(getFromSourceID)})
            return False
