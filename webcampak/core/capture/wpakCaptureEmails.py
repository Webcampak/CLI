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
import socket

from ..wpakConfigObj import Config
from ..wpakEmailObj import emailObj
from ..wpakDbUtils import dbUtils

class captureEmails(object):
    """ This class is used to send success or error emails resulting of a capture
    
    Args:
        log: A class, the logging interface
    	
    Attributes:
        log: A class, the logging interface
    """    
    
    def __init__(self, captureClass):
        self.captureClass = captureClass        
        self.log = self.captureClass.log

        self.currentSourceId = self.captureClass.currentSourceId

        self.configSource = self.captureClass.configSource
        self.configGeneral = self.captureClass.configGeneral

        self.dirLocale = self.captureClass.dirLocale
        self.dirLocaleMessage = self.captureClass.dirLocaleMessage            
        self.dirCurrentLocaleMessages = self.captureClass.dirCurrentLocaleMessages
        self.dirCurrentSourcePictures = self.captureClass.dirCurrentSourcePictures
        self.dirEmails = self.captureClass.dirEmails
        self.dirCache = self.captureClass.dirCache
        self.dirStats = self.captureClass.dirStats
        
        self.captureUtils = self.captureClass.captureUtils
        self.fileUtils = self.captureClass.fileUtils
                
    def sendCaptureSuccess(self, captureFilename = None):
        """ This function queue an email to inform the user that the capture is successful.
        The email's content and subject is store within the locale's directory corresponding to the language configured for the source.
        If a filename is provided, a picture can be sent along the email.   
        
        Args:
            captureFilename: a YYYYMMDDHHMMSS format used to specify which picture to send along
        
        Returns:
            None
        """             
        self.log.debug("captureEmails.sendCaptureSuccess(): " + _("Start"))
        
        emailSuccessContent = self.dirCurrentLocaleMessages + "emailOnlineContent.txt"
        emailSuccessSubject = self.dirCurrentLocaleMessages + "emailOnlineSubject.txt"
        if os.path.isfile(emailSuccessContent) == False:
            emailSuccessContent = self.dirLocale + "en_US.utf8/" + self.dirLocaleMessage + "emailOnlineContent.txt"
            emailSuccessSubject = self.dirLocale + "en_US.utf8/" + self.dirLocaleMessage + "emailOnlineSubject.txt"
        self.log.info("capture.sendCaptureSuccess(): " + _("Using message subject file: %(emailSuccessSubject)s") % {'emailSuccessSubject': emailSuccessSubject} )                                
        self.log.info("capture.sendCaptureSuccess(): " + _("Using message content file: %(emailSuccessContent)s") % {'emailSuccessContent': emailSuccessContent} )                                                
        
        if os.path.isfile(emailSuccessContent) and os.path.isfile(emailSuccessSubject):
            emailContentFile = open(emailSuccessContent, 'r')
            emailContent = emailContentFile.read()
            emailContentFile.close()
            emailSubjectFile = open(emailSuccessSubject, 'r')
            emailSubject = emailSubjectFile.read()
            emailSubjectFile.close()
            emailSubject = emailSubject.replace("#CURRENTHOSTNAME#", socket.gethostname())
            emailSubject = emailSubject.replace("#CURRENTSOURCE#", self.currentSourceId)
            emailSubject = emailSubject.replace("#NBFAILURES#", str(self.captureUtils.getCustomCounter('errorcount')))
            newEmail = emailObj(self.log, self.dirEmails, self.fileUtils)
            newEmail.setFrom({'email': self.configGeneral.getConfig('cfgemailsendfrom')})
            db = dbUtils(self.captureClass)
            newEmail.setTo(db.getSourceEmailUsers(self.currentSourceId))
            db.closeDb()
            newEmail.setBody(emailContent)
            newEmail.setSubject(emailSubject)
            if captureFilename != None and int(self.configSource.getConfig('cfgemailsuccesspicturewidth')) > 0:
                captureDirectory = captureFilename[:8]                
                if os.path.isfile(self.dirCurrentSourcePictures + captureDirectory + "/" + captureFilename + ".jpg"):
                    captureFilename = self.dirCurrentSourcePictures + captureDirectory + "/" + captureFilename + ".jpg"                
                    newEmail.addAttachment({'PATH': captureFilename, 'WIDTH': int(self.configSource.getConfig('cfgemailsuccesspicturewidth')), 'NAME': 'last-capture.jpg'})
            newEmail.writeEmailObjectFile()                				
        else:
            self.log.debug("captureEmails.sendCaptureSuccess(): " + _("Unable to find default translation files to be used"))
            
    def sendCaptureError(self, sendEmailErrorCount, lastSuccessCapture):
        """ This function is used to send an email in case of capture error
        The email is only sent once
        If never sent and over the alert threshold an email is sent via the EmailClass
        
        Args:
            sendEmailErrorCount: number of errors
            lastSuccessCapture: date representing the last successful capture
                    
        Returns:
            None
        """     
        self.log.info("captureEmails.sendCaptureError(): " + _("Preparation of an email alert about the error"))

        emailErrorContent = self.dirCurrentLocaleMessages + "emailErrorContent.txt"
        emailErrorSubject = self.dirCurrentLocaleMessages + "emailErrorSubject.txt"
        if os.path.isfile(emailErrorContent) == False:
            self.log.info("capture.sendCaptureError(): " + _("Using to find message file: %(emailErrorContent)s") % {'emailErrorContent': emailErrorContent} )                                
            emailErrorContent = self.dirLocale + "en_US.utf8/" + self.dirLocaleMessage + "emailErrorContent.txt"
            emailErrorSubject = self.dirLocale + "en_US.utf8/" + self.dirLocaleMessage + "emailErrorSubject.txt"
        self.log.info("capture.sendCaptureError(): " + _("Using message subject file: %(emailErrorSubject)s") % {'emailErrorSubject': emailErrorSubject} )                                
        self.log.info("capture.sendCaptureError(): " + _("Using message content file: %(emailErrorContent)s") % {'emailErrorContent': emailErrorContent} )                                                
        if os.path.isfile(emailErrorContent) and os.path.isfile(emailErrorSubject):
            emailContentFile = open(emailErrorContent, 'r')
            emailContent = emailContentFile.read()
            emailContentFile.close()
            emailSubjectFile = open(emailErrorSubject, 'r')
            emailSubject = emailSubjectFile.read()
            emailSubjectFile.close()
            emailSubject = emailSubject.replace("#CURRENTHOSTNAME#", socket.gethostname())
            emailSubject = emailSubject.replace("#CURRENTSOURCE#", self.currentSourceId)
            emailSubject = emailSubject.replace("#LASTCAPTUREDATE#", self.captureUtils.formatDateLegend(lastSuccessCapture, self.configSource.getConfig('cfgimgdateformat')))
            
            newEmail = emailObj(self.log, self.dirEmails, self.fileUtils)
            newEmail.setFrom({'email': self.configGeneral.getConfig('cfgemailsendfrom')})
            db = dbUtils(self.captureClass)
            newEmail.setTo(db.getSourceEmailUsers(self.currentSourceId))
            db.closeDb()
            newEmail.setBody(emailContent)
            newEmail.setSubject(emailSubject)
            newEmail.writeEmailObjectFile() 
            
    def sendCaptureStats(self):
        """ Once a day, send stats of the previous day by email"""            
        self.log.debug("captureEmails.sendCaptureStats(): " + _("Start"))                        
        emailSent = 0
        currentDay = self.captureClass.getCaptureTime().strftime("%Y%m%d")
        for liststatsfile in sorted(os.listdir(self.dirStats), reverse=True):
            if liststatsfile[:8] == "capture-" and liststatsfile != "capture-" + currentDay + ".txt" and emailSent == 0:  # We don't want to take in consideration current day
                if os.path.isfile(self.dirCache + "source" + self.currentSourceId + "-" + liststatsfile[8:16] + "-statsemail"):
                    self.log.info("captureEmails.sendCaptureStats(): " + _("Email Capture Stats: Email already sent, taking no action"))
                    emailSent = 1
                else:
                    self.log.info("captureEmails.sendCaptureStats(): " + _("Preparation of an email alert about the error"))
                    emailContentFile = self.dirCurrentLocaleMessages + "emailCaptureStatsContent.txt"
                    emailSubjectFile = self.dirCurrentLocaleMessages + "emailCaptureStatsSubject.txt"
                    if os.path.isfile(emailContentFile) == False:
                        self.log.info("capture.sendCaptureError(): " + _("Using to find message file: %(emailContentFile)s") % {'emailContentFile': emailContentFile} )                                
                        emailContentFile = self.dirLocale + "en_US.utf8/" + self.dirLocaleMessage + "emailCaptureStatsContent.txt"
                        emailSubjectFile = self.dirLocale + "en_US.utf8/" + self.dirLocaleMessage + "emailCaptureStatsSubject.txt"
                    self.log.info("capture.sendCaptureError(): " + _("Using message subject file: %(emailSubjectFile)s") % {'emailSubjectFile': emailSubjectFile} )                                
                    self.log.info("capture.sendCaptureError(): " + _("Using message content file: %(emailContentFile)s") % {'emailContentFile': emailContentFile} )                                                
                    if os.path.isfile(emailContentFile) and os.path.isfile(emailSubjectFile):
                        emailContentFile = open(emailContentFile, 'r')
                        emailContent = emailContentFile.read()
                        emailContentFile.close()
                        emailSubjectFile = open(emailSubjectFile, 'r')
                        emailSubject = emailSubjectFile.read()
                        emailSubjectFile.close()

                        captureStatsFile = Config(self.log, self.dirStats + liststatsfile)

                        emailSubject = emailSubject.replace("#CURRENTHOSTNAME#", socket.gethostname())
                        emailSubject = emailSubject.replace("#CURRENTSOURCE#", self.currentSourceId)
                        emailSubject = emailSubject.replace("#CAPTURESUCCESS#", str(captureStatsFile.getStat('CaptureSuccess')))		
                        emailSubject = emailSubject.replace("#CAPTUREREQUEST#", str(captureStatsFile.getStat('CaptureRequest')))	

                        emailContent = emailContent.replace("#CURRENTSOURCE#", self.currentSourceId)
                        emailContent = emailContent.replace("#CAPTURESUCCESS#", str(captureStatsFile.getStat('CaptureSuccess')))		
                        emailContent = emailContent.replace("#CAPTUREREQUEST#", str(captureStatsFile.getStat('CaptureRequest')))		
                        emailContent = emailContent.replace("#MAINFTPSUCCESS#", str(captureStatsFile.getStat('MainFTPSuccess')))		
                        emailContent = emailContent.replace("#MAINFTPREQUEST#", str(captureStatsFile.getStat('MainFTPRequest')))		
                        emailContent = emailContent.replace("#SECONDFTPSUCCESS#", str(captureStatsFile.getStat('SecondFTPSuccess')))		
                        emailContent = emailContent.replace("#SECONDFTPREQUEST#", str(captureStatsFile.getStat('SecondFTPRequest')))		
                        emailContent = emailContent.replace("#HOTLINKFTPSUCCESS#", str(captureStatsFile.getStat('HotlinkFTPSuccess')))		
                        emailContent = emailContent.replace("#HOTLINKFTPREQUEST#", str(captureStatsFile.getStat('HotlinkFTPRequest')))		
                        emailContent = emailContent.replace("#LASTCAPTURE#", str(captureStatsFile.getStat('LatestCapture')))		

                        newEmail = emailObj(self.log, self.dirEmails, self.fileUtils)
                        newEmail.setFrom({'email': self.configGeneral.getConfig('cfgemailsendfrom')})
                        db = dbUtils(self.captureClass)
                        newEmail.setTo(db.getSourceEmailUsers(self.currentSourceId))
                        db.closeDb()
                        newEmail.setBody(emailContent)
                        newEmail.setSubject(emailSubject)
                        newEmail.writeEmailObjectFile() 

                        f = open(self.dirCache + "source" + self.currentSourceId + "-" + liststatsfile[8:16] + "-statsemail", 'w')
                        f.write('1')
                        f.close()	            
            