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
import time
import gettext
import json
from datetime import tzinfo, timedelta, datetime
import pytz
from dateutil import tz
import dateutil.parser
from tabulate import tabulate
import socket

from wpakConfigObj import Config
from wpakConfigCache import configCache
from wpakTimeUtils import timeUtils
from wpakSourcesUtils import sourcesUtils
from wpakFileUtils import fileUtils
from wpakDbUtils import dbUtils
from wpakEmailObj import emailObj
from wpakFTPUtils import FTPUtils
from wpakAlertsObj import alertObj

class alertsEmails(object):
    """ This class contains functions used to send email to source users
    
    Args:
        parentClass: The parent class

    Attributes:
        tbc
    """

    def __init__(self, parentClass):
        self.log = parentClass.log

        self.configPaths = parentClass.configPaths
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']
        self.dirLocale = self.configPaths.getConfig('parameters')['dir_locale']
        self.dirLocaleEmails = self.configPaths.getConfig('parameters')['dir_locale_emails']
        self.dirEmails = self.configPaths.getConfig('parameters')['dir_emails']

        self.configGeneral = parentClass.configGeneral
        self.dbUtils = parentClass.dbUtils
        self.configCache = parentClass.configCache
        self.fileUtils = parentClass.fileUtils

    def loadEmailTemplateFile(self, configSource, TemplateFilename):
        """Simple function to load an email template (either subject or content)"""
        self.log.debug("alertsEmails.loadEmailTemplateFile(): " + _("Start"))

        templateFile = self.dirLocale + configSource.getConfig('cfgsourcelanguage') + "/" + self.dirLocaleEmails + TemplateFilename
        if os.path.isfile(templateFile) == False:
            templateFile = self.dirLocale + "en_US.utf8/" + self.dirLocaleEmails + TemplateFilename
        if os.path.isfile(templateFile):
            self.log.info("alertsEmails.sendCaptureSuccess(): " + _("Using message subject file: %(templateFile)s") % {'templateFile': templateFile})
            templateFileContent = open(templateFile, 'r')
            templateContent = templateFileContent.read()
            templateFileContent.close()
            return templateContent
        else:
            return None


    def sendCaptureError(self, currentAlert):
        """ This function queue an email to inform the user that the capture is failing
        The email's content and subject is store within the locale's directory corresponding to the language configured for the source.

        Args:
            currentAlert: a capture alert object

        Returns:
            None
        """
        self.log.debug("alertsEmails.sendCaptureSuccess(): " + _("Start"))
        configSource = self.configCache.getSourceConfig("source", currentAlert.getAlertValue("sourceid"))

        emailContent = self.loadEmailTemplateFile(configSource, "alertErrorContent.txt")
        if currentAlert.getAlertValue("emailType") == "REMINDER":
            emailSubject = self.loadEmailTemplateFile(configSource, "alertErrorReminderSubject.txt")
        else:
            emailSubject = self.loadEmailTemplateFile(configSource, "alertErrorSubject.txt")

        if emailContent != None and emailSubject != None:
            currentSourceTime = dateutil.parser.parse(currentAlert.getAlertValue("currentTime"))
            lastCatpureTime = dateutil.parser.parse(currentAlert.getAlertValue("lastCaptureTime"))
            emailSubject = emailSubject.replace("#CURRENTHOSTNAME#", socket.gethostname())
            emailSubject = emailSubject.replace("#CURRENTSOURCE#", str(currentAlert.getAlertValue("sourceid")))
            emailSubject = emailSubject.replace("#CURRENTSOURCENAME#", self.dbUtils.getSourceName(currentAlert.getAlertValue("sourceid")))
            emailSubject = emailSubject.replace("#LASTCAPTURETIME#", lastCatpureTime.strftime("%c"))
            emailContent = emailContent.replace("#CURRENTSOURCETIME#", currentSourceTime.strftime("%c"))
            emailContent = emailContent.replace("#LASTCAPTURETIME#", lastCatpureTime.strftime("%c"))
            newEmail = emailObj(self.log, self.dirEmails, self.fileUtils)
            newEmail.setFrom({'email': self.configGeneral.getConfig('cfgemailsendfrom')})
            newEmail.setTo(self.dbUtils.getSourceEmailUsers(currentAlert.getAlertValue("sourceid")))
            newEmail.setBody(emailContent)
            newEmail.setSubject(emailSubject)
            newEmail.writeEmailObjectFile()
        else:
            self.log.info("alertsEmails.sendCaptureSuccess(): " + _("Unable to find default translation files to be used"))

    def sendCaptureSuccess(self, currentAlert):
        """ This function queue an email to inform the user that the capture is successful.
        The email's content and subject is store within the locale's directory corresponding to the language configured for the source.
        If a filename is provided, a picture can be sent along the email.

        Args:
            currentAlert: a capture alert object

        Returns:
            None
        """
        self.log.debug("alertsEmails.sendCaptureSuccess(): " + _("Start"))
        configSource = self.configCache.getSourceConfig("source", currentAlert.getAlertValue("sourceid"))

        emailContent = self.loadEmailTemplateFile(configSource, "alertWorkingContent.txt")
        emailSubject = self.loadEmailTemplateFile(configSource, "alertWorkingSubject.txt")

        if emailContent != None and emailSubject != None:
            emailSubject = emailSubject.replace("#CURRENTHOSTNAME#", socket.gethostname())
            emailSubject = emailSubject.replace("#CURRENTSOURCE#", str(currentAlert.getAlertValue("sourceid")))
            emailSubject = emailSubject.replace("#CURRENTSOURCENAME#", self.dbUtils.getSourceName(currentAlert.getAlertValue("sourceid")))
            currentSourceTime = dateutil.parser.parse( currentAlert.getAlertValue("currentTime"))
            lastCatpureTime = dateutil.parser.parse( currentAlert.getAlertValue("lastCaptureTime"))
            emailContent = emailContent.replace("#CURRENTSOURCETIME#", currentSourceTime.strftime("%c"))
            emailContent = emailContent.replace("#LASTCAPTURETIME#", lastCatpureTime.strftime("%c"))
            newEmail = emailObj(self.log, self.dirEmails, self.fileUtils)
            newEmail.setFrom({'email': self.configGeneral.getConfig('cfgemailsendfrom')})
            newEmail.setTo(self.dbUtils.getSourceEmailUsers(currentAlert.getAlertValue("sourceid")))
            newEmail.setBody(emailContent)
            newEmail.setSubject(emailSubject)
            if currentAlert.getAlertValue("lastPicture") != None and int(configSource.getConfig('cfgemailsuccesspicturewidth')) > 0:
                captureDirectory = currentAlert.getAlertValue("lastPicture")[:8]
                dirCurrentSourcePictures = self.dirSources + 'source' + str(currentAlert.getAlertValue("sourceid")) + '/' + self.configPaths.getConfig('parameters')['dir_source_pictures']
                if os.path.isfile(dirCurrentSourcePictures + captureDirectory + "/" + currentAlert.getAlertValue("lastPicture")):
                    captureFilename = dirCurrentSourcePictures + captureDirectory + "/" + currentAlert.getAlertValue("lastPicture")
                    newEmail.addAttachment({'PATH': captureFilename,
                                            'WIDTH': int(configSource.getConfig('cfgemailsuccesspicturewidth')),
                                            'NAME': 'last-capture.jpg'})
            newEmail.writeEmailObjectFile()
        else:
            self.log.info("alertsEmails.sendCaptureSuccess(): " + _("Unable to find default translation files to be used"))

