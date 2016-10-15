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

class videoEmails(object):
    """ This class is used to send success or error emails resulting of a capture
    
    Args:
        log: A class, the logging interface
    	
    Attributes:
        log: A class, the logging interface
    """    
    
    def __init__(self, videoClass):
        self.videoClass = videoClass        
        self.log = self.videoClass.log

        self.currentSourceId = self.videoClass.currentSourceId

        self.configSource = self.videoClass.configSource
        self.configGeneral = self.videoClass.configGeneral

        self.dirLocale = self.videoClass.dirLocale
        self.dirLocaleMessage = self.videoClass.dirLocaleMessage            
        self.dirCurrentLocaleMessages = self.videoClass.dirCurrentLocaleMessages
        self.dirCurrentSourcePictures = self.videoClass.dirCurrentSourcePictures
        self.dirEmails = self.videoClass.dirEmails
        self.dirCache = self.videoClass.dirCache
        self.dirStats = self.videoClass.dirStats
        
        self.fileUtils = self.videoClass.fileUtils
                
    def sendVideoSuccess(self, videoFilename):
        """ This function queue an email to inform the user that video creation is successful
        The email's content and subject is store within the locale's directory corresponding to the language configured for the source.
        If a filename is provided, a picture can be sent along the email.   
        
        Args:
            videoFilename: Filename of the generated video
        
        Returns:
            None
        """             
        self.log.debug("videoEmails.sendVideoSuccess(): " + _("Start"))
        
        emailSuccessContent = self.dirCurrentLocaleMessages + "emailVideoContent.txt"
        emailSuccessSubject = self.dirCurrentLocaleMessages + "emailVideoSubject.txt"
        if os.path.isfile(emailSuccessContent) == False:
            emailSuccessContent = self.dirLocale + "en_US.utf8/" + self.dirLocaleMessage + "emailVideoContent.txt"
            emailSuccessSubject = self.dirLocale + "en_US.utf8/" + self.dirLocaleMessage + "emailVideoSubject.txt"
        self.log.info("capture.sendVideoSuccess(): " + _("Using message subject file: %(emailSuccessSubject)s") % {'emailSuccessSubject': emailSuccessSubject} )                                
        self.log.info("capture.sendVideoSuccess(): " + _("Using message content file: %(emailSuccessContent)s") % {'emailSuccessContent': emailSuccessContent} )                                                
        
        if os.path.isfile(emailSuccessContent) and os.path.isfile(emailSuccessSubject):
            emailContentFile = open(emailSuccessContent, 'r')
            emailContent = emailContentFile.read()
            emailContentFile.close()
            emailSubjectFile = open(emailSuccessSubject, 'r')
            emailSubject = emailSubjectFile.read()
            emailSubjectFile.close()
            emailSubject = emailSubject.replace("#CURRENTHOSTNAME#", socket.gethostname())
            emailSubject = emailSubject.replace("#CURRENTSOURCE#", self.currentSourceId)
            emailSubject = emailSubject.replace("#VIDEOFILENAME#", videoFilename)
            newEmail = emailObj(self.log, self.dirEmails, self.fileUtils)
            newEmail.setFrom({'email': self.configGeneral.getConfig('cfgemailsendfrom')})
            db = dbUtils(self.captureClass)
            newEmail.setTo(db.getSourceEmailUsers(self.currentSourceId))
            db.closeDb()
            newEmail.setBody(emailContent)
            newEmail.setSubject(emailSubject)
            # Note: Add log file along with the email            
            newEmail.writeEmailObjectFile()                				
        else:
            self.log.debug("videoEmails.sendVideoSuccess(): " + _("Unable to find default translation files to be used"))
            
