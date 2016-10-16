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
import json

class xferJob(object):
    def __init__(self, loadFile = None):
        self.xferJobFile = None
        self.initxferJob()
        if loadFile != None:
            self.loadXferJobFile(loadFile)
        
    # Getters and Setters
    def setStatus(self, value):
        self.xferJob['job']['status'] = value
        
    def getStatus(self):
        return self.xferJob['job']['status']

    def setRetries(self, value):
        self.xferJob['job']['retries'] = value
        
    def getRetries(self):
        return self.xferJob['job']['retries']    
    
    # DEPRECATED
    """
    def setPath(self, value):
        self.xferJob['job']['path'] = value
        
    def getPath(self):
        return self.xferJob['job']['path']    
    """
    def setSource(self, value):
        self.xferJob['job']['source'] = value
        
    def getSource(self):
        return self.xferJob['job']['source']    

    def setSourceSourceId(self, value):
        self.xferJob['job']['source']['sourceid'] = value
        
    def getSourceSourceId(self):
        return self.xferJob['job']['source']['sourceid']  

    def setSourceType(self, value):
        self.xferJob['job']['source']['type'] = value
        
    def getSourceType(self):
        return self.xferJob['job']['source']['type']  

    def setSourceFilePath(self, value):
        self.xferJob['job']['source']['filepath'] = value
        
    def getSourceFilePath(self):
        return self.xferJob['job']['source']['filepath']  

    def setSourceFtpServerId(self, value):
        self.xferJob['job']['source']['ftpserverid'] = value
        
    def getSourceFtpServerId(self):
        return self.xferJob['job']['source']['ftpserverid']  
    
    def setSourceFtpServerHash(self, value):
        self.xferJob['job']['source']['ftpserverhash'] = value
        
    def getSourceFtpServerHash(self):
        return self.xferJob['job']['source']['ftpserverhash'] 
    
    def setDestination(self, value):
        self.xferJob['job']['destination'] = value
        
    def getDestination(self):
        return self.xferJob['job']['destination'] 

    def setDestinationSourceId(self, value):
        self.xferJob['job']['destination']['sourceid'] = value
        
    def getDestinationSourceId(self):
        return self.xferJob['job']['destination']['sourceid']  

    def setDestinationType(self, value):
        self.xferJob['job']['destination']['type'] = value
        
    def getDestinationType(self):
        return self.xferJob['job']['destination']['type']  

    def setDestinationFilePath(self, value):
        self.xferJob['job']['destination']['filepath'] = value
        
    def getDestinationFilePath(self):
        return self.xferJob['job']['destination']['filepath']  

    def setDestinationFtpServerId(self, value):
        self.xferJob['job']['destination']['ftpserverid'] = value
        
    def getDestinationFtpServerId(self):
        return self.xferJob['job']['destination']['ftpserverid']  
    
    def setDestinationFtpServerHash(self, value):
        self.xferJob['job']['destination']['ftpserverhash'] = value
        
    def getDestinationFtpServerHash(self):
        return self.xferJob['job']['destination']['ftpserverhash'] 

    def setHash(self, value):
        self.xferJob['job']['hash'] = value
        
    def getHash(self):
        return self.xferJob['job']['hash']     

    def setDateQueued(self, value):
        self.xferJob['job']['date_queued'] = value
        
    def getDateQueued(self):
        return self.xferJob['job']['date_queued']      

    def setDateStarted(self, value):
        self.xferJob['job']['date_start'] = value
        
    def getDateStarted(self):
        return self.xferJob['job']['date_start']      
 
    def setDateCompleted(self, value):
        self.xferJob['job']['date_completed'] = value
        
    def getDateCompleted(self):
        return self.xferJob['job']['date_completed']     
    
    def setLogs(self, value):
        self.xferJob['logs'] = value
        
    def getLogs(self):
        return self.xferJob['logs'] 

    def setXferReport(self, value):
        self.xferJob['job']['xfer_report'] = value
        
    def getXferReport(self):
        self.xferJob['job']['xfer_report']    
    
    def getXferJob(self):
        return self.xferJob
        
    def setXferJob(self, value):
        self.xferJob =  value
    
    # Function: initxferJob
    # Description; Initialize the job dictionary
    # Return: Nothing
    def initxferJob(self):
        self.xferJob = {}
        self.xferJob['job'] = {}
        self.xferJob['job']['status'] = 'queued'
        #self.xferJob['job']['path'] = None          # deprecated
        self.xferJob['job']['retries'] = None
        #self.xferJob['job']['max_retries'] = None   # deprecated
        self.xferJob['job']['source'] = {}
        self.xferJob['job']['source']['sourceid'] = None
        self.xferJob['job']['source']['type'] = None
        self.xferJob['job']['source']['ftpserverid'] = None
        self.xferJob['job']['source']['ftpserverhash'] = None        
        self.xferJob['job']['source']['filepath'] = None        
        self.xferJob['job']['destination'] = {}
        self.xferJob['job']['destination']['sourceid'] = None
        self.xferJob['job']['destination']['type'] = None
        self.xferJob['job']['destination']['ftpserverid'] = None      
        self.xferJob['job']['destination']['ftpserverhash'] = None      
        self.xferJob['job']['destination']['filepath'] = None      
        self.xferJob['job']['hash'] = None
        self.xferJob['job']['date_queued'] = None
        self.xferJob['job']['date_start'] = None
        self.xferJob['job']['date_completed'] = None
        self.xferJob['job']['xfer_report'] = {}
        self.xferJob['job']['xfer_report']['date_started'] = None
        self.xferJob['job']['xfer_report']['date_completed'] = None
        self.xferJob['job']['xfer_report']['bytes'] = None
        self.xferJob['job']['xfer_report']['seconds'] = None
        self.xferJob['job']['xfer_report']['direction'] = None         
        self.xferJob['logs'] = {}

    
    # Function: loadXferJobFile
    # Description; Load the Job file into memory
    # Return: Nothing
    def loadXferJobFile(self, jobSrcFile):
        if os.path.isfile(jobSrcFile):        
            with open(jobSrcFile) as jobFileContent:    
                self.xferJob = json.load(jobFileContent)
        return None
    
    # Function: writeXferJobFile
    # Description; Write the Job file to disk
    # Return: True if success, false otherwise
    def writeXferJobFile(self, jobDstFile):    
        with open(jobDstFile, "w") as jobJsonFile:
            jobJsonFile.write(json.dumps(self.xferJob))
        return True
            
 
    