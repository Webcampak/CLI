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

from future import standard_library

standard_library.install_aliases()
from builtins import object
import os
import socket
import urllib.request, urllib.parse, urllib.error
from urllib.error import URLError
from urllib.request import (
    HTTPPasswordMgrWithDefaultRealm,
    HTTPBasicAuthHandler,
    build_opener,
)


class captureWebfile(object):
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir
        self.captureClass = parentClass

        self.configPaths = parentClass.configPaths
        self.dirEtc = self.configPaths.getConfig("parameters")["dir_etc"]
        self.dirSources = self.configPaths.getConfig("parameters")["dir_sources"]
        self.dirCache = self.configPaths.getConfig("parameters")["dir_cache"]
        self.dirLogs = self.configPaths.getConfig("parameters")["dir_logs"]
        self.dirResources = self.configPaths.getConfig("parameters")["dir_resources"]

        self.configGeneral = parentClass.configGeneral
        self.configSource = parentClass.configSource
        self.currentSourceId = parentClass.getSourceId()
        self.currentCaptureDetails = parentClass.currentCaptureDetails

        self.dirCurrentSourceTmp = (
            self.dirSources
            + "source"
            + self.currentSourceId
            + "/"
            + self.configPaths.getConfig("parameters")["dir_source_tmp"]
        )
        self.dirCurrentSourcePictures = (
            self.dirSources
            + "source"
            + self.currentSourceId
            + "/"
            + self.configPaths.getConfig("parameters")["dir_source_pictures"]
        )

        # self.captureDate = parentClass.getCaptureTime().strftime("%Y%m%d%H%M%S")
        # self.captureFilename = self.captureDate + ".jpg"

        self.fileUtils = parentClass.fileUtils
        self.captureUtils = parentClass.captureUtils
        self.timeUtils = parentClass.timeUtils
        self.pictureTransformations = parentClass.pictureTransformations

    # Function: Capture
    # Description; This function is used to capture a sample picture
    # Return: Nothing
    def capture(self):
        self.log.info("captureTestPicture.capture(): Starting the capture process")
        self.currentCaptureDetails.setCaptureValue(
            "captureDate",
            self.timeUtils.getCurrentSourceTime(self.configSource).isoformat(),
        )

        self.captureFilename = self.captureClass.getCaptureTime().strftime(
            "%Y%m%d%H%M%S"
        )
        self.fileUtils.CheckFilepath(
            self.dirCurrentSourceTmp + self.captureFilename + ".jpg"
        )

        socket.setdefaulttimeout(10)
        url = self.configSource.getConfig("cfgsourcewebfileurl")
        self.log.info(
            "captureWebfile.capture(): Starting the capture process, URL: %(remoteURL)s"
            % {"remoteURL": url}
        )
        urlusername = ""
        try:
            userpass = url.split("@", 1)[0]
            targeturl = url.split("@", 1)[1]
            targeturl = userpass.split("//", 1)[0] + "//" + targeturl
            userpass = userpass.split("//", 1)[1]
            urlusername = userpass.split(":", 1)[0]
            urlpassword = userpass.split(":", 1)[1]
            self.log.info(
                "captureWebfile.capture(): Url contains username and password, Username is: %(urlusername)s"
                % {"urlusername": urlusername}
            )
        except:
            self.log.info(
                "captureWebfile.capture(): Url does not contain username and password"
            )

        if urlusername != "":
            try:
                # From: http://twigstechtips.blogspot.com/2011/10/python-fetching-https-urls-which.html
                password_mgr = HTTPPasswordMgrWithDefaultRealm()
                password_mgr.add_password(None, targeturl, urlusername, urlpassword)
                opener = build_opener(HTTPBasicAuthHandler(password_mgr))
                file = opener.open(targeturl)
                localFile = open(
                    self.dirCurrentSourceTmp + self.captureFilename + ".jpg", "w"
                )
                localFile.write(file.read())
                localFile.close()
            except URLError:
                self.log.info("captureWebfile.capture(): Error opening the URL")
                self.log.info(
                    "captureWebfile.capture(): Check your username and password"
                )
                return False
        else:
            try:
                urllib.request.urlretrieve(
                    self.configSource.getConfig("cfgsourcewebfileurl"),
                    self.dirCurrentSourceTmp + self.captureFilename + ".jpg",
                )
            except:
                self.log.info("captureWebfile.capture(): Error opening the URL")
                return False

        if self.captureUtils.verifyCapturedFile(
            self.dirCurrentSourceTmp + self.captureFilename + ".jpg"
        ):
            return [self.dirCurrentSourceTmp + self.captureFilename + ".jpg"]
        else:
            self.log.error(
                "captureWebfile.triggerCapture(): Failed to capture from Camera"
            )
            if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".jpg"):
                os.remove(self.dirCurrentSourceTmp + self.captureFilename + ".jpg")
            return False
