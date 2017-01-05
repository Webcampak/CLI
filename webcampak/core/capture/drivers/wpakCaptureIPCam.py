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
from datetime import tzinfo, timedelta, datetime
import shutil
import time
import re
from PIL import Image
from PIL.ExifTags import TAGS


class captureIPCam(object):
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir

        self.configPaths = parentClass.configPaths
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']
        self.dirCache = self.configPaths.getConfig('parameters')['dir_cache']
        self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']
        self.dirResources = self.configPaths.getConfig('parameters')['dir_resources']
        self.dirStats = self.configPaths.getConfig('parameters')['dir_stats']

        self.configGeneral = parentClass.configGeneral
        self.configSource = parentClass.configSource
        self.currentSourceId = parentClass.getSourceId()
        self.currentCaptureDetails = parentClass.currentCaptureDetails

        self.dirCurrentSourceTmp = self.dirSources + 'source' + self.currentSourceId + '/' + \
                                   self.configPaths.getConfig('parameters')['dir_source_tmp']
        self.dirCurrentSourcePictures = self.dirSources + 'source' + self.currentSourceId + '/' + \
                                        self.configPaths.getConfig('parameters')['dir_source_pictures']

        self.captureDate = parentClass.getCaptureTime().strftime("%Y%m%d%H%M%S")
        self.captureDay = parentClass.getCaptureTime().strftime("%Y%m%d")
        self.captureFilename = self.captureDate + ".jpg"

        parentClass.getCaptureTime()

        self.fileUtils = parentClass.fileUtils
        self.captureUtils = parentClass.captureUtils
        self.timeUtils = parentClass.timeUtils
        self.pictureTransformations = parentClass.pictureTransformations

    # Function: GetExifDate 
    # Description; Extract date from EXIF Metada and convert it into datetime
    # Return: timestamp 
    def GetExifDate(self, picture):
        self.log.debug(_("captureIPCam.GetExifDate(): Start"))
        try:
            img = Image.open(picture)
            if hasattr(img, '_getexif'):
                exifinfo = img._getexif()
            if exifinfo != None:
                for tag, value in exifinfo.items():
                    decoded = TAGS.get(tag, tag)
                    if decoded == "DateTimeDigitized":
                        # print "DECODED:" + str(decoded) + "VALUE" + str(value)
                        # 2012:05:20 10:46:37
                        cfgnow = datetime(*time.strptime(value, "%Y:%m:%d %H:%M:%S")[0:6])
                        return cfgnow
        except:
            return 0

    # Function: processFile
    # Description; This function is used to analyze and process a file
    # Return: Nothing
    def processFile(self, filePath):
        self.log.info("captureIPCam.processFile(): " + _("Start Capture"))
        self.log.info(
            "captureIPCam.processFile(): " + _("Processing: %(filePath)s, size %(fileSize)s") % {'filePath': filePath,
                                                                                                 'fileSize': os.path.getsize(
                                                                                                     filePath)})
        fileName, fileExtension = os.path.splitext(os.path.basename(filePath))
        if (fileExtension == '.jpg' or fileExtension == '.JPG') and os.path.getsize(filePath) > int(
                self.configSource.getConfig('cfgcaptureminisize')):
            self.log.info("captureIPCam.processFile(): " + _("File is a picture"))

            if self.configSource.getConfig('cfgsourcecamiptemplate') == "webcampak" or (
                    self.configSource.getConfig('cfgsourcewpaktype') == "rec" and self.configSource.getConfig(
                    'cfgsourcetype') == "wpak"):
                self.log.info("captureIPCam.processFile(): " + _(
                    "Determining picture date based on webcampak name template (YYYYMMDDHHMMSS.jpg)"))
                currentFileTime = self.timeUtils.getTimeFromFilename(fileName, self.configSource, "YYYYMMDDHHMMSS")
            elif self.configSource.getConfig('cfgsourcecamiptemplate') == "harbortronics":
                self.log.info("captureIPCam.processFile(): " + _("Determining picture date based on harbortonics naming convention"))
                currentFileTime = self.timeUtils.getTimeFromFilename(fileName, self.configSource, "YYYYMMDD_HHMMSS")
            elif self.configSource.getConfig('cfgsourcecamiptemplate') == "tplink":
                # 192.168.0.18_01_20170103153300_TIMING - Regex: ([0-9]{14})+
                self.log.info("captureIPCam.processFile(): " + _("Determining picture date based on TPLINK naming convention"))
                regex = r"([0-9]{14})+"
                extractedDatetime = re.findall(regex, fileName)
                currentFileTime = self.timeUtils.getTimeFromFilename(extractedDatetime[0], self.configSource, "YYYYMMDDHHMMSS")
            elif self.configSource.getConfig('cfgsourcecamiptemplate') == "exif":
                self.log.info("captureIPCam.processFile(): " + _("Determining picture date based on EXIF details"))
                currentFileTime = self.timeUtils.getTimeFromExif(filePath, self.configSource)
            elif self.configSource.getConfig('cfgsourcecamiptemplate') == "filedate":
                self.log.info("captureIPCam.processFile(): " + _("Determining picture date based on filesystem date"))
                currentFileTime = self.timeUtils.getTimeFromFiledate(filePath, self.configSource)
            if currentFileTime == False:
                self.log.info("captureIPCam.processFile(): " + _(
                    "Unable to get date based on configured method , looking into EXIF details"))
                currentFileTime = self.timeUtils.getTimeFromExif(filePath, self.configSource)
            if currentFileTime == False:
                self.log.info("captureIPCam.processFile(): " + _(
                    "Unable to get date based on configured method , looking into filesystem date"))
                currentFileTime = self.timeUtils.getTimeFromFiledate(filePath, self.configSource)
            if currentFileTime == False:
                self.log.info("captureIPCam.processFile(): " + _("Unable to get date, cancelling processing"))
                return None

            self.currentCaptureDetails.setCaptureValue('captureDate', currentFileTime.isoformat())
            self.captureFilename = currentFileTime.strftime("%Y%m%d%H%M%S")

            # Move file to root of tmp directory
            self.log.info(
                "captureIPCam.processFile(): " + _("Moving file to root of /tmp directory for consistent processing"))
            shutil.move(filePath, self.dirCurrentSourceTmp + self.captureFilename + ".jpg")
            if os.path.isfile(os.path.splitext(filePath)[0] + ".raw"):
                shutil.move(os.path.splitext(filePath)[0] + ".raw",
                            self.dirCurrentSourceTmp + self.captureFilename + ".raw")

            return self.dirCurrentSourceTmp + self.captureFilename + ".jpg"
        elif fileExtension == '.jsonl' and "sensors" in fileName:
            self.log.info(_("captureIPCam.processFile(): Processing a sensor file: %(filePath)s") % {'filePath': os.path.basename(filePath)})
            captureDirectory = fileName[:8]
            destinationSensorFilePath = self.dirCurrentSourcePictures + captureDirectory + "/" + fileName + ".jsonl"
            self.fileUtils.CheckFilepath(destinationSensorFilePath)
            shutil.copy(filePath, destinationSensorFilePath)
            os.chmod(destinationSensorFilePath, 0775)
            self.log.info("captureIPCam.processFile(): " + _("Sensor file copied to %(destinationSensorFilePath)s") % {'destinationSensorFilePath': str(destinationSensorFilePath)})
        else:
            self.log.info(_("captureIPCam.processFile(): %(filePath)s is not a picture or is too small") % {
                'filePath': os.path.basename(filePath)})
            return None

    # Function: Capture
    # Description; This function is used to capture a sample picture
    # Return: Nothing
    def capture(self):
        self.log.info(_("captureIPCam.capture(): Start Capture"))
        self.log.info("captureIPCam.capture(): " + _("Entering the process, template: %(Template)s") % {
            'Template': self.configSource.getConfig('cfgsourcecamiptemplate')})

        capturedFiles = []

        for firstLevelScanFile in sorted(os.listdir(self.dirCurrentSourceTmp), reverse=True):
            self.log.info("captureIPCam.capture(): " + _("Processing: %(firstLevelScanFile)s") % {
                'firstLevelScanFile': firstLevelScanFile})
            if os.path.isdir(self.dirCurrentSourceTmp + firstLevelScanFile) and firstLevelScanFile[:2] == "20":
                self.log.info("captureIPCam.capture(): " + _("%(firstLevelScanFile)s is a directory, scanning") % {
                    'firstLevelScanFile': firstLevelScanFile})
                for secondLevelScanFile in sorted(os.listdir(self.dirCurrentSourceTmp + firstLevelScanFile),
                                                  reverse=True):
                    self.log.info("captureIPCam.capture(): " + _("Processing %(secondLevelScanFile)s") % {
                        'secondLevelScanFile': firstLevelScanFile + "/" + secondLevelScanFile})
                    currentProcessedPictures = self.processFile(
                        self.dirCurrentSourceTmp + firstLevelScanFile + "/" + secondLevelScanFile)
                    if currentProcessedPictures != None:
                        capturedFiles.append(currentProcessedPictures)
            else:
                self.log.info("captureIPCam.capture(): " + _("%(firstLevelScanFile)s is a file") % {
                    'firstLevelScanFile': firstLevelScanFile})
                currentProcessedPictures = self.processFile(self.dirCurrentSourceTmp + firstLevelScanFile)
                if currentProcessedPictures != None:
                    capturedFiles.append(currentProcessedPictures)

        # if len(capturedFiles) == 0:
        #    return False
        # else:
        return capturedFiles
