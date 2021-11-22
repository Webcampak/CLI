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

from __future__ import division
from future import standard_library

standard_library.install_aliases()
from builtins import str
from builtins import range
from builtins import object
from past.utils import old_div
import os
import shutil
import time
import socket
import urllib.request, urllib.parse, urllib.error
import platform
import re

from ..wpakConfigObj import Config


class captureUtils(object):
    """This class contains various utilities functions used during the capture process

    Args:
        captureClass: An instance of capture Class

    Attributes:
        log: A class, the logging interface
    """

    def __init__(self, captureClass):
        self.log = captureClass.log
        self.config_dir = captureClass.config_dir
        self.captureClass = captureClass

        self.dirLocale = self.captureClass.dirLocale

        self.configPaths = captureClass.configPaths
        self.dirEtc = self.configPaths.getConfig("parameters")["dir_etc"]
        self.dirSources = self.configPaths.getConfig("parameters")["dir_sources"]
        self.dirCache = self.configPaths.getConfig("parameters")["dir_cache"]
        self.dirWatermark = self.configPaths.getConfig("parameters")["dir_watermark"]
        self.dirXferQueue = (
            self.configPaths.getConfig("parameters")["dir_xfer"] + "queued/"
        )

        self.configGeneral = captureClass.configGeneral
        self.configSource = captureClass.configSource
        self.currentSourceId = captureClass.getSourceId()
        self.lastCaptureDetails = captureClass.lastCaptureDetails

        self.pictureTransformations = None
        self.fileUtils = captureClass.fileUtils
        self.timeUtils = captureClass.timeUtils
        self.transferUtils = captureClass.transferUtils
        self.FTPUtils = captureClass.FTPUtils

        self.dirCurrentSourceWatermarkDir = (
            self.dirSources
            + "source"
            + self.currentSourceId
            + "/"
            + self.configPaths.getConfig("parameters")["dir_source_watermark"]
        )
        self.dirCurrentSourceTmp = (
            self.dirSources
            + "source"
            + self.currentSourceId
            + "/"
            + self.configPaths.getConfig("parameters")["dir_source_tmp"]
        )
        self.dirCurrentSourceLive = (
            self.dirSources
            + "source"
            + self.currentSourceId
            + "/"
            + self.configPaths.getConfig("parameters")["dir_source_live"]
        )
        self.dirLive = self.configPaths.getConfig("parameters")["dir_source_live"]
        self.dirCurrentSourcePictures = (
            self.dirSources
            + "source"
            + self.currentSourceId
            + "/"
            + self.configPaths.getConfig("parameters")["dir_source_pictures"]
        )
        self.dirCurrentSource = self.dirSources + "source" + self.currentSourceId + "/"

    # Getters and Setters
    def setPictureTransformations(self, pictureTransformations):
        """Used to set pictures transformation class after captureutils init"""
        self.pictureTransformations = pictureTransformations

    def isWithinTimeframe(self):
        """Check if capture is within a pre-configured timeframe (within configuration file)
            Note that there is a different between a day number by strftime (0 = Sunday to 6 = Saturday)
                and numbering used by Webcampak (1 = Monday to 7 = Sunday). We are sticking to this number
                to make webcampak configuration through the config file easier to understand by most.
        Args:
            None

        Returns:
            Boolean: depending if capture request is (or not) within timeframe
        """
        self.log.debug("captureUtils.isWithinTimeframe(): Start")
        CurrentTime = int(self.captureClass.getCaptureTime().strftime("%H%M"))
        CurrentDay = int(self.captureClass.getCaptureTime().strftime("%w"))
        if CurrentDay == 0:  # We replace 0 by 7 to match Webcampak time
            CurrentDay = 7
        self.log.info(
            "captureUtils.isWithinTimeframe(): Current Day: %(CurrentDay)s - Current Time: %(CurrentTime)s"
            % {"CurrentDay": str(CurrentDay), "CurrentTime": str(CurrentTime)}
        )
        if (
            self.configSource.getConfig("cfgcroncalendar") == "no"
        ):  # Captures are allowed 24 / 7
            AllowCapture = True
        elif self.configSource.getConfig("cfgcronday" + str(CurrentDay))[0] == "yes":
            startTime = int(
                self.configSource.getConfig("cfgcronday" + str(CurrentDay))[1]
                + self.configSource.getConfig("cfgcronday" + str(CurrentDay))[2]
            )
            endTime = int(
                self.configSource.getConfig("cfgcronday" + str(CurrentDay))[3]
                + self.configSource.getConfig("cfgcronday" + str(CurrentDay))[4]
            )
            self.log.info(
                "captureUtils.isWithinTimeframe(): Capture allowed between: %(StartAllowed)s and: %(EndAllowed)s"
                % {"StartAllowed": str(startTime), "EndAllowed": str(endTime)}
            )
            if startTime == 0 and endTime == 0:
                AllowCapture = True
            elif startTime >= endTime:
                if (CurrentTime >= startTime and CurrentTime < 2400) or (
                    CurrentTime >= 0 and CurrentTime < endTime
                ):
                    AllowCapture = True
                else:
                    AllowCapture = False
            else:
                if CurrentTime == endTime:
                    AllowCapture = False
                elif CurrentTime >= startTime and CurrentTime < endTime:
                    AllowCapture = True
                else:
                    AllowCapture = False
        else:  # Capture not allowed this day
            self.log.info(
                "captureUtils.isWithinTimeframe(): Capture not allowed this day"
            )
            AllowCapture = False

        if AllowCapture == False:
            self.log.info(
                "captureUtils.isWithinTimeframe(): Outside pre-configured capture slot"
            )

        return AllowCapture

    def checkInterval(self):
        """Check if time since last capture is within a pre-configured range
        Args:
            None

        Returns:
            Boolean: True (capture allowed) or False (capture not allowed)
        """
        self.log.debug("captureUtils.checkInterval(): Start")
        LastCapture = self.lastCaptureDetails.getLastCaptureTime()
        if LastCapture != None:
            TimeSinceLastCapture = int(
                (self.captureClass.getScriptStartTime() - LastCapture).total_seconds()
                * 1000
            )
            self.log.info(
                "captureUtils.checkInterval(): Last capture %(TimeSinceLastCapture)s ms ago"
                % {"TimeSinceLastCapture": str(TimeSinceLastCapture)}
            )
            minimumCaptureValue = int(
                self.configSource.getConfig("cfgminimumcapturevalue")
            )
            if self.configSource.getConfig("cfgminimumcaptureinterval") == "minutes":
                minimumCaptureValue = minimumCaptureValue * 60
            self.log.info(
                "captureUtils.checkInterval(): Minimum capture interval: %(minimumCaptureValue)s ms"
                % {"minimumCaptureValue": str(minimumCaptureValue * 1000)}
            )
            if TimeSinceLastCapture >= (minimumCaptureValue * 1000):
                self.log.info("captureUtils.checkInterval(): Capture slot available")
                return True
            else:
                self.log.info(
                    "captureUtils.checkInterval(): Capture slot refused, not enough time since last capture"
                )
                return False
        else:
            self.log.info(
                "captureUtils.checkInterval(): Capture slot available, no previous capture"
            )
            return True

    def formatDateLegend(self, inputDate, outputPattern):
        """Function used format a date to be displayed (i.e. inserted as a legend)
        Args:
            inputDate: date object
            outputPattern: pattern to be used to represent the date, the pattern is actually a number (this should be optimized)

        Returns:
            String: date representation according to the selected pattern
        """
        if outputPattern == "1":
            return " " + inputDate.strftime("%d/%m/%Y - %Hh%M")
        elif outputPattern == "2":
            return " " + inputDate.strftime("%d/%m/%Y")
        elif outputPattern == "3":
            return " " + inputDate.strftime("%Hh%M")
        elif outputPattern == "4":
            return " " + inputDate.strftime("%A %d %B %Y - %Hh%M")
        elif outputPattern == "5":
            return " " + inputDate.strftime("%d %B %Y - %Hh%M")
        elif outputPattern == "6":  # US, 12h format
            return " " + inputDate.strftime("%m/%d/%Y - %Ih%M %p")
        elif outputPattern == "7":  # US, 24h format
            return " " + inputDate.strftime("%m/%d/%Y - %Hh%M")
        else:
            return ""

    def modifyPictures(self, createHotlink):
        """Apply modification to captured pictures, based on toggles in the configuration file:
            - Crop picture
            - Insert watermark
            - Insert text
            - Insert temperature (phidget only)
            - Insert luminosity (phidget only)
            - Resize picture
            - Create hotlink files and, if applicable, upload via FTP
            - Create sensors graph

        Args:
            createHotlink: A boolean, True of False to define if hotlink should be created

        Returns:
            None
        """
        self.log.debug("captureUtils.modifyPictures(): Start")
        if createHotlink == False:
            self.log.info(
                "captureUtils.modifyPictures(): Hotlink creation disabled for this picture"
            )

        if self.configSource.getConfig("cfgrotateactivate") == "yes":
            self.pictureTransformations.rotate(
                self.configSource.getConfig("cfgrotateangle")
            )
        else:
            self.log.info("captureUtils.modifyPictures(): Rotating disabled")

        if self.configSource.getConfig("cfgcropactivate") == "yes":
            self.pictureTransformations.crop(
                self.configSource.getConfig("cfgcropsizewidth"),
                self.configSource.getConfig("cfgcropsizeheight"),
                self.configSource.getConfig("cfgcropxpos"),
                self.configSource.getConfig("cfgcropypos"),
            )
        else:
            self.log.info("captureUtils.modifyPictures(): Cropping disabled")

        if self.configSource.getConfig("cfgpicwatermarkactivate") == "yes":
            watermarkFile = None
            if os.path.isfile(
                self.dirCurrentSourceWatermarkDir
                + self.configSource.getConfig("cfgpicwatermarkfile")
            ):
                watermarkFile = (
                    self.dirCurrentSourceWatermarkDir
                    + self.configSource.getConfig("cfgpicwatermarkfile")
                )
            elif os.path.isfile(
                self.dirWatermark + self.configSource.getConfig("cfgpicwatermarkfile")
            ):
                watermarkFile = self.dirWatermark + self.configSource.getConfig(
                    "cfgpicwatermarkfile"
                )
            if watermarkFile != None:
                self.pictureTransformations.Watermark(
                    self.configSource.getConfig("cfgpicwatermarkpositionx"),
                    self.configSource.getConfig("cfgpicwatermarkpositiony"),
                    self.configSource.getConfig("cfgpicwatermarkdissolve"),
                    watermarkFile,
                )
            else:
                self.log.info(
                    "captureUtils.modifyPictures(): Error: Unable to find watermark file:  %(watermarkFile)s"
                    % {
                        "watermarkFile": self.configSource.getConfig(
                            "cfgpicwatermarkfile"
                        )
                    }
                )
        else:
            self.log.info("captureUtils.modifyPictures(): Watermark disabled")

        if self.configSource.getConfig("cfgimagemagicktxt") == "yes":
            fileName = os.path.basename(self.pictureTransformations.getFilesourcePath())
            captureTime = self.timeUtils.getTimeFromFilename(
                fileName, self.configSource, "YYYYMMDDHHMMSS"
            )
            if captureTime == False:
                captureTime = self.captureClass.getCaptureTime()
            self.pictureTransformations.Text(
                self.configSource.getConfig("cfgimgtextfont"),
                self.configSource.getConfig("cfgimgtextsize"),
                self.configSource.getConfig("cfgimgtextgravity"),
                self.configSource.getConfig("cfgimgtextbasecolor"),
                self.configSource.getConfig("cfgimgtextbaseposition"),
                self.configSource.getConfig("cfgimgtext"),
                self.formatDateLegend(
                    captureTime, self.configSource.getConfig("cfgimgdateformat")
                ),
                self.configSource.getConfig("cfgimgtextovercolor"),
                self.configSource.getConfig("cfgimgtextoverposition"),
            )
        else:
            self.log.info("captureUtils.modifyPictures(): Legend disabled")

        # NEW SECTION TO MANAGE GRAPHS
        if self.configGeneral.getConfig("cfgphidgetactivate") == "yes":
            for ListSourceSensors in range(
                1, int(self.configSource.getConfig("cfgphidgetsensornb")) + 1
            ):
                if (
                    self.configSource.getConfig(
                        "cfgphidgetsensor" + str(ListSourceSensors)
                    )[0]
                    != ""
                    and self.configSource.getConfig(
                        "cfgphidgetsensorinsert" + str(ListSourceSensors)
                    )[0]
                    != "no"
                ):
                    self.log.info(
                        "captureUtils.modifyPictures(): Processing Sensor %(SensorNb)s"
                        % {"SensorNb": ListSourceSensors}
                    )
                    SensorsHistory = Config(
                        self.dirCurrentSourceTmp
                        + cfgdispday
                        + "/"
                        + self.configGeneral.getConfig("cfgphidgetcapturefile"),
                        None,
                    )
                    CurrentValue = SensorsHistory.getSensor(
                        cfgdispdate,
                        self.configSource.getConfig(
                            "cfgphidgetsensor" + str(ListSourceSensors)
                        )[0],
                    )
                    if CurrentValue == False:
                        SensorTable = []
                        for capturetime in SensorsHistory.getFullConfig():
                            SensorTable.append(int(capturetime))
                        SensorTable = np.array(
                            SensorTable
                        )  # Convert Python array to Numpy array
                        if len(SensorTable) > 0:
                            SensorNearestValue = self.SensorFindNearest(
                                SensorTable, int(cfgdispdate)
                            )
                            self.log.info(
                                "captureUtils.modifyPictures(): Sensor: Date %(cfgdispdate)s not found in sensor file, closest date is %(SensorNearestValue)s"
                                % {
                                    "cfgdispdate": cfgdispdate,
                                    "SensorNearestValue": str(SensorNearestValue),
                                }
                            )
                            CurrentValue = SensorsHistory.getSensor(
                                str(SensorNearestValue),
                                self.configSource.getConfig(
                                    "cfgphidgetsensor" + str(ListSourceSensors)
                                )[0],
                            )
                    if CurrentValue != False:
                        self.log.info(
                            "captureUtils.modifyPictures(): Sensor: Insert %(SensorType)s"
                            % {
                                "SensorType": self.configSource.getConfig(
                                    "cfgphidgetsensor" + str(ListSourceSensors)
                                )[0]
                            }
                        )
                        self.Graph.CreateSensorBar(
                            CurrentValue, ListSourceSensors, "", ""
                        )
                        if (
                            self.configSource.getConfig(
                                "cfgphidgetsensorinsert" + str(ListSourceSensors)
                            )[1]
                            != "no"
                        ):
                            import shlex, subprocess

                            Command = (
                                "convert "
                                + self.dirCurrentSourceTmp
                                + "Sensor"
                                + str(ListSourceSensors)
                                + ".png -resize "
                                + self.configSource.getConfig(
                                    "cfgphidgetsensorinsert" + str(ListSourceSensors)
                                )[1]
                                + " "
                                + self.dirCurrentSourceTmp
                                + "Sensor"
                                + str(ListSourceSensors)
                                + ".png"
                            )
                            args = shlex.split(Command)
                            p = subprocess.Popen(
                                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                            )
                            output, errors = p.communicate()
                        self.pictureTransformations.Watermark(
                            self.configSource.getConfig(
                                "cfgphidgetsensorinsert" + str(ListSourceSensors)
                            )[3],
                            self.configSource.getConfig(
                                "cfgphidgetsensorinsert" + str(ListSourceSensors)
                            )[4],
                            self.configSource.getConfig(
                                "cfgphidgetsensorinsert" + str(ListSourceSensors)
                            )[2],
                            self.dirCurrentSourceTmp
                            + "Sensor"
                            + str(ListSourceSensors)
                            + ".png",
                            self.dirCurrentSourceTmp + cfgfilename,
                        )
                else:
                    self.log.info(
                        "captureUtils.modifyPictures(): Sensor %(SensorNb)s disabled"
                        % {"SensorNb": ListSourceSensors}
                    )

        if self.configSource.getConfig("cfgarchivesize") != "":
            self.pictureTransformations.resize(
                self.configSource.getConfig("cfgarchivesize")
            )
        else:
            self.log.info("captureUtils.modifyPictures(): Resizing disabled")

    def archivePicture(self, captureFilename):
        """archivePicture capture within pictures directory
                - Copy captured filed into pictures directory (pictures/YYYYMMDD/YYYYMMDDHHMMSS.jpg)
        Args:
            captureFilename: filename of the picture in webcampak format (YYYYMMDDHHMMSS)

        Returns:
            None
        """
        self.log.debug("captureUtils.archivePicture(): Start")
        captureDirectory = captureFilename[:8]
        captureJpgFile = (
            self.dirCurrentSourcePictures
            + captureDirectory
            + "/"
            + captureFilename
            + ".jpg"
        )
        captureRawFile = (
            self.dirCurrentSourcePictures
            + "raw/"
            + captureDirectory
            + "/"
            + captureFilename
            + ".raw"
        )
        # Archiving the picture in its final destination
        self.log.info(
            "captureUtils.archivePicture(): Saving JPG picture to: %(captureJpgFile)s"
            % {"captureJpgFile": captureJpgFile}
        )
        self.fileUtils.CheckFilepath(captureJpgFile)
        shutil.copy(self.dirCurrentSourceTmp + captureFilename + ".jpg", captureJpgFile)
        os.chmod(captureJpgFile, 0o775)
        if os.path.isfile(self.dirCurrentSourceTmp + captureFilename + ".raw"):
            self.log.info(
                "captureUtils.archivePicture(): Copying RAW picture from: %(sourceRawFile)s to: %(captureRawFile)s"
                % {
                    "sourceRawFile": self.dirCurrentSourceTmp
                    + captureFilename
                    + ".raw",
                    "captureRawFile": captureRawFile,
                }
            )
            self.fileUtils.CheckFilepath(captureRawFile)
            shutil.copyfile(
                self.dirCurrentSourceTmp + captureFilename + ".raw", captureRawFile
            )
            os.chmod(captureRawFile, 0o775)
        if os.path.isfile(
            self.dirCurrentSourceTmp
            + "raw/"
            + captureDirectory
            + "/"
            + captureFilename
            + ".raw"
        ):
            self.log.info(
                "captureUtils.archivePicture(): Copying RAW picture from: %(sourceRawFile)s to: %(captureRawFile)s"
                % {
                    "sourceRawFile": self.dirCurrentSourceTmp
                    + "raw/"
                    + captureDirectory
                    + "/"
                    + captureFilename
                    + ".raw",
                    "captureRawFile": captureRawFile,
                }
            )
            self.fileUtils.CheckFilepath(captureRawFile)
            shutil.copyfile(
                self.dirCurrentSourceTmp
                + "raw/"
                + captureDirectory
                + "/"
                + captureFilename
                + ".raw",
                captureRawFile,
            )
            os.chmod(captureRawFile, 0o775)

    def getArchivedSize(self, captureFilename, fileType):
        """Return the size of the captured file
        Args:
            captureFilename: filename of the picture in webcampak format (YYYYMMDDHHMMSS)
            fileType: raw or jpg depending of file type
        Returns:
            Int: filesize
        """
        self.log.debug("captureUtils.getArchivedSize(): Start")
        captureDirectory = captureFilename[:8]
        if fileType == "jpg":
            if os.path.isfile(
                self.dirCurrentSourcePictures
                + captureDirectory
                + "/"
                + captureFilename
                + ".jpg"
            ):
                return os.path.getsize(
                    self.dirCurrentSourcePictures
                    + captureDirectory
                    + "/"
                    + captureFilename
                    + ".jpg"
                )
            else:
                return 0
        elif fileType == "raw":
            if os.path.isfile(
                self.dirCurrentSourcePictures
                + "raw/"
                + captureDirectory
                + "/"
                + captureFilename
                + ".raw"
            ):
                return os.path.getsize(
                    self.dirCurrentSourcePictures
                    + "raw/"
                    + captureDirectory
                    + "/"
                    + captureFilename
                    + ".raw"
                )
            else:
                return 0

    def createLivePicture(self, captureFilename):
        """Copy a picture from TMP directory into live directory as last-capture.jpg and/or last-capture.raw

        Args:
            captureFilename: a string, name of the picture, without extension in webcampak format (YYYYMMDDHHMMSS)

        """
        self.log.debug("captureUtils.createLivePicture(): Start")
        # Copying the picture into the live directory as last-capture.jpg and/or last-capture.raw
        self.log.info(
            "captureUtils.createLivePicture(): Copying full size JPG picture: %(jpgPicture)s to: %(jpgPictureLive)s"
            % {
                "jpgPicture": self.dirCurrentSourceTmp + captureFilename + ".jpg",
                "jpgPictureLive": self.dirCurrentSourceLive + "last-capture.jpg",
            }
        )
        self.fileUtils.CheckFilepath(self.dirCurrentSourceLive + "last-capture.jpg")
        shutil.copy(
            self.dirCurrentSourceTmp + captureFilename + ".jpg",
            self.dirCurrentSourceLive + "last-capture.jpg",
        )
        os.chmod(self.dirCurrentSourceLive + "last-capture.jpg", 0o775)
        if os.path.isfile(self.dirCurrentSourceTmp + captureFilename + ".raw"):
            self.log.info(
                "captureUtils.createLivePicture(): Copying full size RAW picture: %(rawPicture)s to: %(rawPictureLive)s"
                % {
                    "rawPicture": self.dirCurrentSourceTmp + captureFilename + ".raw",
                    "rawPictureLive": self.dirCurrentSourceLive + "last-capture.raw",
                }
            )
            shutil.copy(
                self.dirCurrentSourceTmp + captureFilename + ".raw",
                self.dirCurrentSourceLive + "last-capture.raw",
            )
            os.chmod(self.dirCurrentSourceLive + "last-capture.raw", 0o775)

    def generateHotlinks(self):
        """Create hotlink files and send it via FTP"""
        self.log.debug("captureUtils.generateHotlinks(): Start")
        for j in range(1, 5):
            hotlinkSize = self.configSource.getConfig("cfghotlinksize" + str(j))
            if hotlinkSize != "":
                hotlinkDestinationFile = (
                    self.dirCurrentSourceLive + "webcam-" + hotlinkSize + ".jpg"
                )
                self.log.info(
                    "captureUtils.generateHotlinks(): Hotlink File: %(hotlinkDestinationFile)s"
                    % {"hotlinkDestinationFile": hotlinkDestinationFile}
                )
                # previousDestinationFile = self.pictureTransformations.getFiledestinationPath()
                self.pictureTransformations.setFiledestinationPath(
                    hotlinkDestinationFile
                )
                self.pictureTransformations.resize(hotlinkSize)
                # self.pictureTransformations.setFiledestinationPath(previousDestinationFile)
                os.chmod(
                    self.dirCurrentSourceLive + "webcam-" + hotlinkSize + ".jpg", 0o775
                )
                if self.configSource.getConfig("cfgftphotlinkserverid") != "":
                    self.transferUtils.transferFile(
                        self.captureClass.getCaptureTime(),
                        self.dirCurrentSourceLive + "webcam-" + hotlinkSize + ".jpg",
                        "webcam-" + hotlinkSize + ".jpg",
                        self.configSource.getConfig("cfgftphotlinkserverid"),
                        self.configSource.getConfig("cfgftphotlinkserverretry"),
                    )
                    # self.transferFile(self.dirCurrentSourceLive + "webcam-" + hotlinkSize + ".jpg", "live/webcam-" + hotlinkSize + ".jpg", self.configSource.getConfig('cfgftphotlinkserverid'), self.configSource.getConfig('cfgftphotlinkserverretry'))
            else:
                self.log.info(
                    "captureUtils.generateHotlinks(): Hotlink: %(Hotlinkfile)s disabled"
                    % {"Hotlinkfile": str(j)}
                )

    def sendPicture(self, FTPServerId, FTPServerRetries, FTPSendRaw, captureFilename):
        """Send file to a remote destination

        Args:
            FTPServerId: If in the config-sourceXX-ftpservers.cfg file
            FTPServerRetries: Number of retries when sending this file
            FTPSendRaw: Should RAW file be sent by FTP
            captureFilename: Filename of the picture to copy

        """
        self.log.debug("captureUtils.sendPicture(): Start")
        if FTPServerId != "":
            captureDirectory = captureFilename[:8]
            jpgFileName = (
                self.dirCurrentSourcePictures
                + captureDirectory
                + "/"
                + captureFilename
                + ".jpg"
            )
            rawFileName = (
                self.dirCurrentSourcePictures
                + "raw/"
                + captureDirectory
                + "/"
                + captureFilename
                + ".raw"
            )
            if os.path.isfile(jpgFileName):
                self.log.info(
                    "captureUtils.sendPicture(): Preparing to send JPG file located in  %(jpgFileName)s"
                    % {"jpgFileName": jpgFileName}
                )
                self.transferUtils.transferFile(
                    self.captureClass.getCaptureTime(),
                    jpgFileName,
                    captureDirectory + "/" + captureFilename + ".jpg",
                    FTPServerId,
                    FTPServerRetries,
                )
                # self.transferFile(jpgFileName, "pictures/" + captureDirectory + "/" + captureFilename + ".jpg", FTPServerId, FTPServerRetries)

            if os.path.isfile(rawFileName) and FTPSendRaw == "yes":
                self.log.info(
                    "captureUtils.sendPicture(): Preparing to send RAW file located in  %(rawFileName)s"
                    % {"rawFileName": rawFileName}
                )
                self.transferFile(
                    self.captureClass.getCaptureTime(),
                    rawFileName,
                    "raw/" + captureDirectory + "/" + captureFilename + ".raw",
                    FTPServerId,
                    FTPServerRetries,
                )
                # self.transferFile(rawFileName,  "pictures/" + captureDirectory + "/" + captureFilename + ".raw", FTPServerId, FTPServerRetries)

    def sendSensor(self, FTPServerId, FTPServerRetries, sensorFilename):
        """Send sensor file to a remote destination

        Args:
            FTPServerId: If in the config-sourceXX-ftpservers.cfg file
            FTPServerRetries: Number of retries when sending this file
            sensorFilename: Filename of the picture to copy

        """
        self.log.debug("captureUtils.sendSensor(): Start")
        if FTPServerId != "":
            captureDirectory = sensorFilename[:8]
            sensorFilePath = (
                self.dirCurrentSourcePictures + captureDirectory + "/" + sensorFilename
            )
            if os.path.isfile(sensorFilePath):
                self.log.info(
                    "captureUtils.sendPicture(): Preparing to send sensor JSONL file located in  %(sensorFilePath)s"
                    % {"sensorFilePath": sensorFilePath}
                )
                self.transferUtils.transferFile(
                    self.captureClass.getCaptureTime(),
                    sensorFilePath,
                    captureDirectory + "/" + sensorFilename,
                    FTPServerId,
                    FTPServerRetries,
                )

    def copyPicture(self, destinationSourceId, copyRaw, captureFilename):
        """Copy picture to another source on this webcampaks

        Args:
            destinationSourceId: source ID where to copy the picture to
            copyRaw: Should RAW file be copied to the destination souce as well ?
            captureFilename: Filename of the picture to copy

        """
        self.log.debug("captureUtils.copyPicture(): Start")
        captureDirectory = captureFilename[:8]
        sourceTmpDirectory = (
            self.configGeneral.getConfig("cfgbasedir")
            + self.configGeneral.getConfig("cfgsourcesdir")
            + "source"
            + str(destinationSourceId)
            + "/tmp/"
        )
        if os.path.isdir(sourceTmpDirectory):
            sourceJpgFilePath = (
                self.dirCurrentSourcePictures
                + captureDirectory
                + "/"
                + captureFilename
                + ".jpg"
            )
            destinationJpgFilePath = (
                sourceTmpDirectory + captureDirectory + "/" + captureFilename + ".jpg"
            )
            sourceRawFilePath = (
                self.dirCurrentSourcePictures
                + "raw/"
                + captureDirectory
                + "/"
                + captureFilename
                + ".raw"
            )
            destinationRawFilePath = (
                sourceTmpDirectory
                + "raw/"
                + captureDirectory
                + "/"
                + captureFilename
                + ".raw"
            )
            self.fileUtils.CheckFilepath(destinationJpgFilePath)
            shutil.copy(sourceJpgFilePath, destinationJpgFilePath)
            os.chmod(destinationJpgFilePath, 0o775)
            self.log.info(
                "captureUtils.copyPicture(): SourceCopy: JPG Picture copied to %(sourceTmpDirectory)s"
                % {"sourceTmpDirectory": str(destinationJpgFilePath)}
            )
            if os.path.isfile(sourceRawFilePath) and copyRaw == "yes":
                self.fileUtils.CheckFilepath(destinationRawFilePath)
                shutil.copy(sourceRawFilePath, destinationRawFilePath)
                os.chmod(destinationRawFilePath, 0o775)
                self.log.info(
                    "captureUtils.copyPicture(): SourceCopy: RAW Picture copied to %(destinationRawFilePath)s"
                    % {"destinationRawFilePath": destinationRawFilePath}
                )
        else:
            self.log.info(
                "captureUtils.copyPicture(): SourceCopy: Directory %(sourceTmpDirectory)s does not exist, ensure source exists"
                % {"sourceTmpDirectory": str(sourceTmpDirectory)}
            )

    def copySensor(self, destinationSourceId, sensorFilename):
        """Copy sensor file to another source on this webcampaks

        Args:
            destinationSourceId: source ID where to copy the picture to
            sensorFilename: Filename of the picture to copy

        """
        self.log.debug("captureUtils.copySensor(): Start")
        captureDirectory = sensorFilename[:8]
        sourceTmpDirectory = (
            self.configGeneral.getConfig("cfgbasedir")
            + self.configGeneral.getConfig("cfgsourcesdir")
            + "source"
            + str(destinationSourceId)
            + "/tmp/"
        )
        if os.path.isdir(sourceTmpDirectory):
            sourceSensorFilePath = (
                self.dirCurrentSourcePictures + captureDirectory + "/" + sensorFilename
            )
            destinationSensorFilePath = (
                sourceTmpDirectory + captureDirectory + "/" + sensorFilename
            )
            self.fileUtils.CheckFilepath(destinationSensorFilePath)
            shutil.copy(sourceSensorFilePath, destinationSensorFilePath)
            os.chmod(destinationSensorFilePath, 0o775)
            self.log.info(
                "captureUtils.copySensor(): SourceCopy: Sensor file copied to %(destinationSensorFilePath)s"
                % {"destinationSensorFilePath": str(destinationSensorFilePath)}
            )
        else:
            self.log.info(
                "captureUtils.copySensor(): SourceCopy: Directory %(sourceTmpDirectory)s does not exist, ensure source exists"
                % {"sourceTmpDirectory": str(sourceTmpDirectory)}
            )

    def purgePictures(self, captureFilename):
        """Function used to purge captured files
            - Clean tmp directory
            - Automatically delete old pictures after X days (work with full days directories and not on a pictures basis)
            - Automatically delete pictures if global size of pictures directory is over XXMB (work with full days directories and not on a pictures basis)

        Args:
            captureFilename: Filename of the picture to copy

        """
        self.log.debug("captureUtils.purgePictures(): Start")
        captureDirectory = captureFilename[:8]

        tmpJpgFile = self.dirCurrentSourceTmp + captureFilename + ".jpg"
        if os.path.isfile(tmpJpgFile):  # Delete regular JPG file
            self.log.info(
                "captureUtils.purgePictures(): Removing file: %(tmpJpgFile)s"
                % {"tmpJpgFile": tmpJpgFile}
            )
            os.remove(tmpJpgFile)

        tmpRawFile = self.dirCurrentSourceTmp + captureFilename + ".raw"
        if os.path.isfile(tmpRawFile):  # Delete RAW file
            self.log.info(
                "captureUtils.purgePictures(): Removing file: %(tmpRawFile)s"
                % {"tmpRawFile": tmpRawFile}
            )
            os.remove(tmpRawFile)

        for currentFile in sorted(os.listdir(self.dirCurrentSourceTmp)):
            if os.path.splitext(self.dirCurrentSourceTmp + currentFile)[1] == ".jpeg":
                self.log.info(
                    "captureUtils.purgePictures(): Removing file: %(currentDeleteFile)s"
                    % {"currentDeleteFile": self.dirCurrentSourceTmp + currentFile}
                )
                os.remove(self.dirCurrentSourceTmp + currentFile)
            if (
                os.path.splitext(currentFile)[1] == ".jpg"
                and str(
                    currentFile[0] + currentFile[1] + currentFile[2] + currentFile[3]
                )
                == "capt"
            ):
                self.log.info(
                    "captureUtils.purgePictures(): Removing file: %(currentDeleteFile)s"
                    % {"currentDeleteFile": self.dirCurrentSourceTmp + currentFile}
                )
                os.remove(self.dirCurrentSourceTmp + currentFile)

        if self.configSource.getConfig("cfgsavepictures") != "yes":
            self.log.info(
                "captureUtils.purgePictures(): Deleting pictures from archive"
            )
            archiveJpgFile = (
                self.dirCurrentSourcePictures
                + captureDirectory
                + "/"
                + captureFilename
                + ".jpg"
            )
            if os.path.isfile(archiveJpgFile):
                self.log.info(
                    "captureUtils.purgePictures(): Removing file: %(archiveJpgFile)s"
                    % {"archiveJpgFile": archiveJpgFile}
                )
                os.remove(archiveJpgFile)
            archiveRawFile = (
                self.dirCurrentSourcePictures
                + "raw/"
                + captureDirectory
                + "/"
                + captureFilename
                + ".raw"
            )
            if os.path.isfile(archiveRawFile):
                self.log.info(
                    "captureUtils.purgePictures(): DiskManagement: Delete picture from archive: RAW deleted"
                )
                self.log.info(
                    "captureUtils.purgePictures(): Removing file: %(archiveRawFile)s"
                    % {"archiveRawFile": archiveRawFile}
                )
                os.remove(archiveRawFile)

    def deleteOldPictures(self):
        """This function is used to delete old pictures
        If it detect an old picture, all pictures taken this day will be deleted.
        """
        self.log.debug("captureUtils.deleteOldPictures(): Start")
        self.log.info(
            "captureUtils.deleteOldPictures(): System configured to delete picture from:  %(picturesDirectory)s after %(days)s days"
            % {
                "picturesDirectory": self.dirCurrentSourcePictures,
                "days": self.configSource.getConfig("cfgcapturedeleteafterdays"),
            }
        )
        for currentScanFile in os.listdir(self.dirCurrentSourcePictures):
            if (
                os.path.isdir(
                    os.path.join(self.dirCurrentSourcePictures, currentScanFile)
                )
                and currentScanFile[:2] == "20"
            ):
                dirdate = (
                    int(currentScanFile[:4]),
                    int(currentScanFile[4:6]),
                    int(currentScanFile[6:8]),
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                )
                timestamp = int(time.mktime(dirdate))
                timeDifferenceInDays = int(
                    old_div(
                        (
                            int(self.captureClass.getCaptureTime().strftime("%s"))
                            - timestamp
                        ),
                        86400,
                    )
                )
                self.log.info(
                    "captureUtils.deleteOldPictures(): Directory %(currentScanFile)s is %(timeDifferenceInDays)s days old"
                    % {
                        "currentScanFile": currentScanFile,
                        "timeDifferenceInDays": timeDifferenceInDays,
                    }
                )
                if timeDifferenceInDays > int(
                    self.configSource.getConfig("cfgcapturedeleteafterdays")
                ):
                    self.log.info(
                        "captureUtils.deleteOldPictures(): Deleting Directory %(currentScanFile)s"
                        % {
                            "currentScanFile": self.dirCurrentSourcePictures
                            + currentScanFile
                        }
                    )
                    shutil.rmtree(self.dirCurrentSourcePictures + currentScanFile)
                    # Section to delete raw files
                    if os.path.isdir(
                        os.path.join(
                            self.dirCurrentSourcePictures + "raw/", currentScanFile
                        )
                    ):
                        self.log.info(
                            "captureUtils.deleteOldPictures(): Deleting Directory %(currentScanFile)s"
                            % {
                                "currentScanFile": self.dirCurrentSourcePictures
                                + "raw/"
                                + currentScanFile
                            }
                        )
                        shutil.rmtree(
                            self.dirCurrentSourcePictures + "raw/" + currentScanFile
                        )

    def deleteOverSize(self):
        """This function is used to free disk space by deleting old pictures
        This function will delete a whole day of pictures at once
        """
        self.log.debug("captureUtils.deleteOverSize(): Start")
        picturesDirSize = self.fileUtils.CheckDirSize(self.dirCurrentSourcePictures)
        self.log.info(
            "captureUtils.deleteOverSize(): Current pictures directory disk size %(picturesDirSize)s MB, max allowed size is %(maxSize)s MB"
            % {
                "picturesDirSize": picturesDirSize,
                "maxSize": str(self.configSource.getConfig("cfgcapturemaxdirsize")),
            }
        )
        if self.configSource.getConfig(
            "cfgcapturemaxdirsize"
        ) != "" and picturesDirSize > int(
            self.configSource.getConfig("cfgcapturemaxdirsize")
        ):
            for currentScanFile in sorted(os.listdir(self.dirCurrentSourcePictures)):
                if (
                    os.path.isdir(
                        os.path.join(self.dirCurrentSourcePictures, currentScanFile)
                    )
                    and len(currentScanFile) == 8
                ):
                    if self.fileUtils.CheckDirSize(self.dirCurrentSourcePictures) > int(
                        self.configSource.getConfig("cfgcapturemaxdirsize")
                    ):
                        self.log.info(
                            "captureUtils.deleteOldPictures(): Deleting Directory %(deleteDirectory)s"
                            % {
                                "deleteDirectory": self.dirCurrentSourcePictures
                                + currentScanFile
                            }
                        )
                        shutil.rmtree(self.dirCurrentSourcePictures + currentScanFile)
                        # Section to delete raw files
                        if os.path.isdir(
                            os.path.join(
                                self.dirCurrentSourcePictures + "raw/", currentScanFile
                            )
                        ):
                            self.log.info(
                                "captureUtils.deleteOldPictures(): Deleting Directory %(deleteDirectory)s"
                                % {
                                    "deleteDirectory": self.dirCurrentSourcePictures
                                    + "raw/"
                                    + currentScanFile
                                }
                            )
                            shutil.rmtree(
                                self.dirCurrentSourcePictures + "raw/" + currentScanFile
                            )

    def verifyCapturedFile(self, filePath):
        """Check if a captured file exists and has a proper size (greater than cfgcaptureminisize).

        Args:
            filePath: Full filepath of the picture

        Returns: boolean, depending if capture is successful or not

        """
        self.log.debug("captureUtils.verifyCapturedFile(): Start")
        if os.path.isfile(filePath):
            fileSize = os.path.getsize(filePath)
            self.log.info(
                "captureUtils.verifyCapturedFile(): File: %(filePath)s size is %(fileSize)s bytes"
                % {"filePath": str(filePath), "fileSize": str(fileSize)}
            )
        else:
            self.log.info(
                "captureUtils.verifyCapturedFile(): File does not exist: %(filePath)s"
                % {"filePath": str(filePath)}
            )
            fileSize = 0
        if fileSize > int(self.configSource.getConfig("cfgcaptureminisize")):
            self.log.info("captureUtils.verifyCapturedFile(): Check File: Successful")
            return True
        else:
            self.log.debug(
                "captureUtils.verifyCapturedFile(): Check File: capture failed, incorrecte size: %(IncorrectSize)s/%(TargetSize)s"
                % {
                    "IncorrectSize": str(fileSize),
                    "TargetSize": self.configSource.getConfig("cfgcaptureminisize"),
                }
            )
            return False

    def sendUsageStats(self):
        """Participate in the stats program by sending a few elements"""
        self.log.debug("captureUtils.sendUsageStats(): Start")
        # Get software version
        if os.path.isfile(self.configGeneral.getConfig("cfgbasedir") + "version"):
            f = open(self.configGeneral.getConfig("cfgbasedir") + "version", "r")
            try:
                SwVersion = f.read()
            except:
                SwVersion = "unknown"
            f.close()
        else:
            SwVersion = "unknown"
        # self.configGeneral.getConfig('cfgbasedir')
        CurrentCPU = platform.processor()
        CurrentCPU = re.sub(r"\s", "", CurrentCPU)
        CurrentDist = platform.linux_distribution()
        CurrentDist = re.sub(r"\s", "", str(CurrentDist))
        ServerUrl = (
            "http://stats.webcampak.com/stats.run.html?v="
            + str(SwVersion)
            + "&t="
            + self.configSource.getConfig("cfgsourcetype")
            + "&c="
            + CurrentCPU
            + "&d="
            + CurrentDist
        )
        ServerUrl = ServerUrl.rstrip()
        # print "Server URL:" + ServerUrl
        socket.setdefaulttimeout(10)
        try:
            urllib.request.urlretrieve(ServerUrl, self.dirCurrentSourceTmp + "tmpfile")
            self.log.info(
                "captureUtils.sendUsageStats(): Stats Program: Communication with central server successful"
            )
        except:
            self.log.info(
                "captureUtils.sendUsageStats(): Stats Program: Unable to communicate with central server"
            )

    def generateFailedCaptureHotlink(self):
        """In case of capture error, and if configured to do so, the system will generate failed hotlink pictures and send those via FTP
        The source for these hotlink pictures is the capture-failed.jpg file located in corresponding locales directory.
        """

        self.log.debug("captureUtils.generateFailedCaptureHotlink(): Start")
        if self.configSource.getConfig("cfghotlinkerrorcreate") == "yes":
            failedCaptureSourceFile = (
                self.dirLocale
                + self.configSource.getConfig("cfgsourcelanguage")
                + "/messages/capture-failed.jpg"
            )
            self.log.info(
                "captureUtils.generateFailedCaptureHotlink(): Using failed capture file: %(failedCaptureSourceFile)s"
                % {"failedCaptureSourceFile": failedCaptureSourceFile}
            )
            if os.path.isfile(failedCaptureSourceFile) == False:
                failedCaptureSourceFile = (
                    self.dirLocale + "en_US.utf8/messages/capture-failed.jpg"
                )
                self.log.info(
                    "captureUtils.generateFailedCaptureHotlink(): Failed capture not found, fallback on English version: %(failedCaptureSourceFile)s"
                    % {"failedCaptureSourceFile": failedCaptureSourceFile}
                )
            failedCaptureFile = (
                self.dirCurrentSourceTmp
                + self.captureClass.getCaptureTime().strftime("%Y%m%d%H%M%S")
                + ".jpg"
            )

            self.log.info(
                "captureUtils.generateFailedCaptureHotlink(): Copying capture file to: %(failedCaptureFile)s"
                % {"failedCaptureFile": failedCaptureFile}
            )
            shutil.copy(failedCaptureSourceFile, failedCaptureFile)
            self.pictureTransformations.setFilesourcePath(failedCaptureFile)
            self.pictureTransformations.setFiledestinationPath(failedCaptureFile)
            self.pictureTransformations.Text(
                self.configSource.getConfig("cfgimgtextfont"),
                "10",
                "southwest",
                "black",
                "14,10",
                "Capture Error - ",
                self.formatDateLegend(
                    self.captureClass.getCaptureTime(),
                    self.configSource.getConfig("cfgimgdateformat"),
                ),
                "black",
                "14,10",
            )

            self.log.debug(
                "captureUtils.generateFailedCaptureHotlink(): Generating hotlinks"
            )
            self.generateHotlinks()

            self.log.info(
                "captureUtils.generateFailedCaptureHotlink(): Removing temporary file: %(failedCaptureFile)s"
                % {"failedCaptureFile": failedCaptureFile}
            )
            os.remove(failedCaptureFile)
        else:
            self.log.debug(
                "captureUtils.generateFailedCaptureHotlink(): Failed hotlink creation disabled"
            )

    def getCustomCounter(self, CustomFile):
        """Webcampak uses some files to store counter values, this is mostly a legacy behavior and should be updated at some point

        Returns:
            int, value of the counter, 0 if file does not exists
        """
        self.log.debug("captureUtils.getCustomCounter(): Start")
        self.log.info(
            "captureUtils.getCustomCounter(): Opening file: %(customCounter)s"
            % {
                "customCounter": self.dirCache
                + "source"
                + self.currentSourceId
                + "-"
                + CustomFile
            }
        )
        if os.path.isfile(
            self.dirCache + "source" + self.currentSourceId + "-" + CustomFile
        ):
            f = open(
                self.dirCache + "source" + self.currentSourceId + "-" + CustomFile, "r"
            )
            try:
                return int(f.read())
            except:
                return 0
            f.close()
        else:
            return 0

    def setCustomCounter(self, CustomFile, ErrorCount):
        """Write current error count to a file
            This value is stored within a file per source in "webcampak/resources/cache" directory

        Args:
            CustomFile: tag of the file to be used
            ErrorCount: Count to be added to the file
        """
        self.log.debug("captureUtils.setCustomCounter(): Start")
        self.log.info(
            "captureUtils.setCustomCounter(): Opening file: %(customCounter)s"
            % {
                "customCounter": self.dirCache
                + "source"
                + self.currentSourceId
                + "-"
                + CustomFile
            }
        )
        f = open(
            self.dirCache + "source" + self.currentSourceId + "-" + CustomFile, "w"
        )
        f.write(str(ErrorCount))
        f.close()
