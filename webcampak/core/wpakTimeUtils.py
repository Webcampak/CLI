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
import pytz
from dateutil import tz
import time
from PIL import Image
from PIL.ExifTags import TAGS

from wpakConfigObj import Config


#
class timeUtils:
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir
        self.configPaths = parentClass.configPaths

        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']

        self.configGeneral = parentClass.configGeneral

    # Getters and Setters        
    def getTimezone(self):
        return self.configGeneral.getConfig('cfgservertimezone')

    def getCurrentDate(self):
        return datetime.now(pytz.timezone(self.getTimezone()))

    def getCurrentDateIso(self):
        return self.getCurrentDate().isoformat()

    # We capture the current date and time, this value is used through the whole software
    # If capture is configured to be delayed there are two option, use script start date or capture date        
    def getCurrentSourceTime(self, sourceConfig):
        self.log.debug("timeUtils.getCurrentSourceTime(): " + _("Start"))
        cfgnowsource = datetime.utcnow()
        if sourceConfig.getConfig('cfgcapturetimezone') != "":  # Update the timezone from UTC to the source's timezone
            self.log.info("timeUtils.getCurrentSourceTime(): " + _("Source Timezone is: %(sourceTimezone)s") % {
                'sourceTimezone': sourceConfig.getConfig('cfgcapturetimezone')})
            sourceTimezone = tz.gettz(sourceConfig.getConfig('cfgcapturetimezone'))
            cfgnowsource = cfgnowsource.replace(tzinfo=tz.gettz('UTC'))
            cfgnowsource = cfgnowsource.astimezone(sourceTimezone)
        self.log.info("timeUtils.getCurrentSourceTime(): " + _("Current source time: %(cfgnowsource)s") % {
            'cfgnowsource': cfgnowsource.isoformat()})
        return cfgnowsource

    # Using a webcampak timestamp, capture the file date and time
    def getTimeFromFilename(self, fileName, sourceConfig, dateFormat):
        self.log.debug("timeUtils.getTimeFromFilename(): " + _("Start"))
        self.log.info(
            "timeUtils.getTimeFromFilename(): " + _("Extract time from: %(fileName)s") % {'fileName': fileName})
        try:
            if dateFormat == "YYYYMMDD_HHMMSS":
                fileTime = datetime.strptime(os.path.splitext(os.path.basename(fileName))[0], "%Y%m%d_%H%M%S")
            else:
                fileTime = datetime.strptime(os.path.splitext(os.path.basename(fileName))[0], "%Y%m%d%H%M%S")
            if sourceConfig.getConfig(
                    'cfgcapturetimezone') != "":  # Update the timezone from UTC to the source's timezone
                self.log.info("timeUtils.getTimeFromFilename(): " + _("Source timezone is: %(sourceTimezone)s") % {
                    'sourceTimezone': sourceConfig.getConfig('cfgcapturetimezone')})
                sourceTimezone = tz.gettz(sourceConfig.getConfig('cfgcapturetimezone'))
                fileTime = fileTime.replace(tzinfo=tz.gettz('UTC'))
                fileTime = fileTime.astimezone(sourceTimezone)
            self.log.info("timeUtils.getTimeFromFilename(): " + _("Picture date is: %(picDate)s") % {
                'picDate': fileTime.isoformat()})
            return fileTime
        except:
            return False

    # Using a webcampak timestamp, capture the file date and time
    def getTimeFromExif(self, filePath, sourceConfig):
        self.log.info("timeUtils.getTimeFromExif(): " + _("Start"))
        self.log.info(
            "timeUtils.getTimeFromExif(): " + _("Extract EXIF time from: %(filePath)s") % {'filePath': filePath})
        try:
            img = Image.open(filePath)
        except:
            self.log.info("timeUtils.getTimeFromExif(): " + _("Failed to open %(filePath)s as a picture") % {
                'filePath': filePath})
            return False

        if hasattr(img, '_getexif'):
            exifinfo = img._getexif()
        if exifinfo != None:
            for tag, value in exifinfo.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "DateTimeDigitized":
                    # print "DECODED:" + str(decoded) + "VALUE" + str(value)
                    # 2012:05:20 10:46:37
                    fileTime = datetime(*time.strptime(value, "%Y:%m:%d %H:%M:%S")[0:6])
                    if sourceConfig.getConfig(
                            'cfgcapturetimezone') != "":  # Update the timezone from UTC to the source's timezone
                        self.log.info("timeUtils.getTimeFromExif(): " + _("Source timezone is: %(sourceTimezone)s") % {
                            'sourceTimezone': sourceConfig.getConfig('cfgcapturetimezone')})
                        sourceTimezone = tz.gettz(sourceConfig.getConfig('cfgcapturetimezone'))
                        fileTime = fileTime.replace(tzinfo=tz.gettz('UTC'))
                        fileTime = fileTime.astimezone(sourceTimezone)
                    return fileTime
                    self.log.info("timeUtils.getTimeFromExif(): " + _("Picture date is: %(picDate)s") % {
                        'picDate': fileTime.isoformat()})
                    break;
        return False

    # Using a webcampak timestamp, capture the file date and time
    def getTimeFromFiledate(self, filePath, sourceConfig):
        self.log.info("timeUtils.getTimeFromFiledate(): " + _("Start"))
        self.log.info(
            "timeUtils.getTimeFromFiledate(): " + _("Extract time from: %(filePath)s") % {'filePath': filePath})
        try:
            fileTimeStamp = int(os.path.getmtime(filePath))
            fileTime = datetime.fromtimestamp(fileTimeStamp)
            if sourceConfig.getConfig(
                    'cfgcapturetimezone') != "":  # Update the timezone from UTC to the source's timezone
                self.log.info("timeUtils.getTimeFromFiledate(): " + _("Source timezone is: %(sourceTimezone)s") % {
                    'sourceTimezone': sourceConfig.getConfig('cfgcapturetimezone')})
                sourceTimezone = tz.gettz(sourceConfig.getConfig('cfgcapturetimezone'))
                fileTime = fileTime.replace(tzinfo=tz.gettz('UTC'))
                fileTime = fileTime.astimezone(sourceTimezone)
            self.log.info("timeUtils.getTimeFromFiledate(): " + _("Picture date is: %(picDate)s") % {
                'picDate': fileTime.isoformat()})
            return fileTime
        except:
            return False

