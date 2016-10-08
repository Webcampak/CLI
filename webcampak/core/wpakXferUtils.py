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
from datetime import tzinfo, timedelta, datetime
from pytz import timezone
import shutil
import pytz
import json
import dateutil.parser
import zlib
import gzip

from wpakConfigObj import Config
from wpakFileUtils import fileUtils

# This class is used to initialize transfer queues and dispatch files to the queue
# It reads files from the global queue directory, starting from the oldest ones, and stops one all threads are full
# Each transfer queue (or thread) can hold up to "self.maxFilesPerThread" files 

class xferUtils:
    """ This class is contains various utilties of the xfer module

    Args:
        log: A class, the logging interface
        config_dir: A string, filesystem location of the configuration directory

    Attributes:
        tbc
    """
    def __init__(self, log, config_dir):
        self.log = log
        self.config_dir = config_dir
        self.configPaths = Config(self.log, self.config_dir + 'param_paths.yml')
        
        self.dirXferThreads = self.configPaths.getConfig('parameters')['dir_xfer'] + 'threads/'
        self.dirXferQueue = self.configPaths.getConfig('parameters')['dir_xfer'] + 'queued/'
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirConfig = self.configPaths.getConfig('parameters')['dir_config']

        self.configGeneral = Config(self.log, self.dirConfig + 'config-general.cfg')
        
        self.maxFilesPerThread = 10


    # Getters and Setters
    def getMaxFilesPerThread(self):
        return self.maxFilesPerThread

    def getCfgxferthreads(self):
        return self.configGeneral.getConfig('cfgxferthreads')
        
    def getTimezone(self):
        return self.configGeneral.getConfig('cfgservertimezone')
    
    def getCurrentDate(self):    
        return datetime.now(pytz.timezone(self.getTimezone()))
    
    def getCurrentDateIso(self):
        return self.getCurrentDate().isoformat()
        
    def loadJsonFile(self, jsonFile):
        """ Load content of a JSON file
        Args:
            None

        Returns:
            JSON dictionary: Python dictionary representation of a json
        """
        self.log.debug("xferUtils.loadJsonFile(): " + _("Start"))
        if os.path.isfile(jsonFile):
            with open(jsonFile) as threadJsonFile:    
                threadJson = json.load(threadJsonFile)
                return threadJson
        return None
        
    def writeJsonFile(self, jsonFile, jsonContent):
        """ Write the content of a dictionary to a JSON file
        Args:
            None

        Returns:
            Boolean: Success of the operation
        """
        self.log.debug("xferUtils.writeJsonFile(): " + _("Start"))
        if fileUtils.CheckFilepath(jsonFile) != "":                
            with open(jsonFile, "w") as threadJsonFile:
                threadJsonFile.write(json.dumps(jsonContent))
            return True
        return False        


    def writeJsonFileGzip(self, jsonFile, jsonContent):
        """ Write the content of a dictionary to a Gzipped JSON file
        Args:
            None

        Returns:
            Boolean: Success of the operation
        """
        self.log.debug("xferUtils.writeJsonFileGzip(): " + _("Start"))
        if fileUtils.CheckFilepath(jsonFile) != "":                
            with gzip.open(jsonFile, "wb") as threadJsonFile:
                threadJsonFile.write(json.dumps(jsonContent))
            return True
        return False  

    def logToJson(self, jsonFile, jsonContent, msg):
        """ Add a log line to a json file. Perform a write operation after each log (to keep status in case of failure)
        Args:
            None

        Returns:
            Dictionary: Returns jsonContent modified with the added log line
        """
        self.log.debug("xferUtils.logToJson(): " + _("Start"))
        self.log.info("xferUtils.logToJson(): " + _("Log Message: %(msg)s ") % {'msg': msg})
        jsonIdx = len(jsonContent['logs']) + 1
        jsonContent['logs'][jsonIdx] = {'date': self.getCurrentDateIso(), 'message': msg}
        self.writeJsonFile(jsonFile, jsonContent)
        return jsonContent
        

    def getThreadsUUID(self):
        """ Returns a list of threads UUID composing the different queue
        Args:
            None

        Returns:
            Array: threads UUID
        """
        self.log.debug("xferUtils.getThreadsUUID(): " + _("Start"))
        threads = []
        for currentFilename in [f for f in os.listdir(self.dirXferThreads) if f.endswith(".json")]:
            threads.append(os.path.splitext(currentFilename)[0])
        return threads

    def getThreadPid(self, threadUUID):
        """ Get the PID currently processing the thread UUID
        Args:
            threadUUID: UUID of the thread to look for

        Returns:
            Array: PID of the thread
        """
        self.log.debug("xferUtils.getThreadPid(): " + _("Start"))
        threadJson = self.loadJsonFile(self.dirXferThreads + threadUUID + '.json')
        if (threadJson.has_key('pid')):
            return threadJson['pid']
        else:
            return None
        
    def setThreadPid(self, threadUUID, pid):
        """ Associate a PID to a threadUUID and save this value in a json file
        Args:
            threadUUID: UUID of the thread
            pid: PID of the process currently processing the thread

        Returns:
            None
        """
        self.log.debug("xferUtils.setThreadPid(): " + _("Start"))
        threadJson = self.loadJsonFile(self.dirXferThreads + threadUUID + '.json')
        threadJson['pid'] = pid
        threadJson['date_updated'] = self.getCurrentDateIso()
        self.writeJsonFile(self.dirXferThreads + threadUUID + '.json', threadJson)        

    def setThreadLastJob(self, threadUUID, jobReport):
        """ Record the last job processed by the thread
        Args:
            threadUUID: UUID of the thread
            jobReport: Last job processed by the thread

        Returns:
            None
        """
        self.log.debug("xferUtils.setThreadLastJob(): " + _("Start"))
        threadJson = self.loadJsonFile(self.dirXferThreads + threadUUID + '.json')
        threadJson['last_job'] = jobReport
        threadJson['date_updated'] = self.getCurrentDateIso()
        self.writeJsonFile(self.dirXferThreads + threadUUID + '.json', threadJson)           
        

    def isPidAlive(self, pid):
        """ Check if a process is running, using its PID
            Args:
                pid: PID to test

            Returns:
                Boolean: Thread running or not
        """
        self.log.debug("xferUtils.isPidAlive(): " + _("Start"))
        try:
            os.kill(pid, 0)
            self.log.info("xferUtils.isPidAlive(): " + _("Process is running: %(pid)s ") % {'pid': str(pid)})
            return True
        except OSError:
            self.log.info("xferUtils.isPidAlive(): " + _("Process does not exist: %(pid)s ") % {'pid': str(pid)})
            return False

    def killThreadByPid(self, pid):
        """ Aggressively kill a PID
            Args:
                pid: PID to kill

            Returns:
                Boolean: Operation successful or not
        """
        self.log.debug("xferUtils.killThreadByPid(): " + _("Start"))
        try:
            os.kill(pid, signal.SIGKILL) #or signal.SIGKILL  SIGTERM
            self.log.info("xferUtils.isPidAlive(): " + _("Process has been killed: %(pid)s ") % {'pid': str(pid)})
            return True
        except OSError:
            self.log.info("xferUtils.isPidAlive(): " + _("Process did not exist: %(pid)s ") % {'pid': str(pid)})
            return False        
        
    def isThreadRunning(self, threadUUID):
        """ Evaluate if a thread is currently running
            Args:
                threadUUID: UUID of the thread

            Returns:
                Boolean: Thread running or not
        """
        self.log.debug("xferUtils.isThreadRunning(): " + _("Start"))
        threadJson = self.loadJsonFile(self.dirXferThreads + threadUUID + '.json')
        if (threadJson.has_key('pid')):
            if self.isPidAlive(threadJson['pid']):
                return True
            else:                
                return False
        else:    
            return False

    def countThreadsQueue(self, threadUUID):
        """ Count the number of files in the threads' queue
            Args:
                threadUUID: UUID of the thread

            Returns:
                Int: Number of files in the thread
        """
        self.log.debug("xferUtils.countThreadsQueue(): " + _("Start"))
        threadsFilesCount = 0
        for currentFilename in [f for f in os.listdir(self.dirXferThreads + threadUUID + '/') if f.endswith(".json")]:
            threadsFilesCount = threadsFilesCount + 1
        return threadsFilesCount

    def getThreadFiles(self, threadUUID):
        """ List all files currently in the thread's directory (currently being processed)
            Args:
                threadUUID: UUID of the thread

            Returns:
                Array: Files currently being processed by the thread
        """
        self.log.debug("xferUtils.getThreadFiles(): " + _("Start"))
        allThreadFiles = []
        for currentFilename in [f for f in os.listdir(self.dirXferThreads + threadUUID + '/') if f.endswith(".json")]:
            allThreadFiles.append(os.path.join(self.dirXferThreads + threadUUID + '/', currentFilename))
        allThreadFiles.sort()
        return allThreadFiles  

    def getFirstThreadFile(self, threadUUID):
        """ Get the first (or next) thread file to be processed
            Args:
                threadUUID: UUID of the thread

            Returns:
                String: Filename
        """
        self.log.debug("xferUtils.getFirstThreadFile(): " + _("Start"))
        allThreadFiles = []
        for currentFilename in [f for f in os.listdir(self.dirXferThreads + threadUUID + '/') if f.endswith(".json")]:
            allThreadFiles.append(os.path.join(self.dirXferThreads + threadUUID + '/', currentFilename))
        allThreadFiles.sort()
        return allThreadFiles[0]

    def isThreadFull(self, threadUUID):
        """ Check if threads is full, return True if all full, False if some still have room
            Args:
                threadUUID: UUID of the thread

            Returns:
                Boolean: True of False depending if the thread is full or not
        """
        self.log.debug("xferUtils.isThreadFull(): " + _("Start"))
        if (self.countThreadsQueue(threadUUID) < self.getMaxFilesPerThread()):
            return False
        else:
            return True
        
    def areThreadsFull(self):
        """ Check if all threads are full, return True if all full, False if some still have room
            Args:
                None

            Returns:
                Boolean: True of False depending if the thread is full or not
        """
        self.log.debug("xferUtils.areThreadsFull(): " + _("Start"))
        threadsFull = True
        for currentThreadUUID in self.getThreadsUUID():
            if (self.isThreadFull(currentThreadUUID) == False):
                threadsFull = False
        return threadsFull
            
                 
    def checkThreadUUID(self, threadUUID):
        """ Check if Thread UUID is valid, simply by checking if a corresponding .json file exists
            Args:
                None

            Returns:
                Boolean: True of False depending if the thread is valid or not
        """
        self.log.debug("xferUtils.checkThreadUUID(): " + _("Start"))
        return os.path.isfile(self.dirXferThreads + threadUUID + '.json')
    
    def getAllQueuedFiles(self):
        """ List all files currently in the global queue directory
            It recursively searched through all json files
            Args:
                None

            Returns:
                Boolean: True of False depending if the thread is valid or not
        """
        self.log.debug("xferUtils.getAllQueuedFiles(): " + _("Start"))
        allQueuedFiles = []
        for dirpath, dirnames, filenames in os.walk(self.dirXferQueue):
            for filename in [f for f in filenames if f.endswith(".json")]:                
                allQueuedFiles.append(os.path.join(dirpath, filename))      
        allQueuedFiles.sort()
        return allQueuedFiles       

        
