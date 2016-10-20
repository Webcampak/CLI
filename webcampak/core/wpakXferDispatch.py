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

import os, uuid
import shutil
import dateutil.parser
import gettext

from wpakConfigObj import Config
from wpakFileUtils import fileUtils
from wpakXferUtils import xferUtils
from wpakTimeUtils import timeUtils

class xferDispatch:
    """ Initialize transfer queues and dispatch files to the queue
    Read files from the global queue directory, starting from the oldest ones and stops once all threads are full
    Each transfer queue (or thread) can hold up to "self.maxFilesPerThread" files (defined in XferUtils.py)
    
    Args:
        log: A class, the logging interface
        config_dir: A string, filesystem location of the configuration directory
    	
    Attributes:
        log: A class, the logging interface
        config_dir: A string, filesystem location of the configuration directory
        configPaths: An object, containing all paths listed in param_paths.yml
        
        dirXferThreads: A string, directory containing xfer threads
        dirXferQueue: A string, directory containing xfer queue
        dirEtc: A string, directory containing configuration files
        
        configGeneral: An object, containing all webcampak level configuration settings (not source specific)
        xferUtils: A class, containing utilities used by various xfer processes
        timeUtils: A class, containing utilities for time-related actions
    """
    def __init__(self, log, appConfig, config_dir):
        self.log = log
        self.appConfig = appConfig                
        self.config_dir = config_dir
        self.configPaths = Config(self.log, self.config_dir + 'param_paths.yml')

        self.dirXferThreads = self.configPaths.getConfig('parameters')['dir_xfer'] + 'threads/'
        self.dirXferFailed = self.configPaths.getConfig('parameters')['dir_xfer'] + 'failed/'
        self.dirXferQueue = self.configPaths.getConfig('parameters')['dir_xfer'] + 'queued/'
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirConfig = self.configPaths.getConfig('parameters')['dir_config']
        self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']
        self.dirLocale = self.configPaths.getConfig('parameters')['dir_locale']
        self.dirLocaleMessage = self.configPaths.getConfig('parameters')['dir_locale_message']

        self.setupLog()

        self.configGeneral = Config(self.log, self.dirConfig + 'config-general.cfg')
        self.initGetText(self.dirLocale, self.configGeneral.getConfig('cfgsystemlang'), self.configGeneral.getConfig('cfggettextdomain'))

                                
        self.xferUtils = xferUtils(self.log, self.config_dir)
        self.timeUtils = timeUtils(self)

    def initGetText(self, dirLocale, cfgsystemlang, cfggettextdomain):
        """ Initialize Gettext with the corresponding translation domain

        Args:
            dirLocale: A string, directory location of the file
            cfgsystemlang: A string, webcampak-level language configuration parameter from config-general.cfg
            cfggettextdomain: A string, webcampak-level gettext domain configuration parameter from config-general.cfg

        Returns:
            None
        """
        self.log.debug("capture.initGetText(): Start")
        try:
            t = gettext.translation(cfggettextdomain, dirLocale, [cfgsystemlang], fallback=True)
            _ = t.ugettext
            t.install()
            self.log.info("capture.initGetText(): " + _("Initialized gettext with Domain: %(cfggettextdomain)s - Language: %(cfgsystemlang)s - Path: %(dirLocale)s")
                          % {'cfggettextdomain': cfggettextdomain, 'cfgsystemlang': cfgsystemlang, 'dirLocale': dirLocale} )
        except:
            self.log.error("No translation file available")

    def setupLog(self):      
        """ Setup logging to file """        
        xferLogs = self.dirLogs + "xfer/"
        if not os.path.exists(xferLogs):
            os.makedirs(xferLogs)  
        logFilename = xferLogs + "dispatch.log"
        self.appConfig.set(self.log._meta.config_section, 'file', logFilename)
        self.appConfig.set(self.log._meta.config_section, 'rotate', True)
        self.appConfig.set(self.log._meta.config_section, 'max_bytes', 512000)
        self.appConfig.set(self.log._meta.config_section, 'max_files', 10)
        self.log._setup_file_log()                            
                            
    def run(self):
        """Entry point of the class, used to initialize and populate threads."""
        # Load the config containing all paths and the general config file
        self.log.info("xferDispatch.run(): Running XFer Dispatch")

        # Load the number of xfer threads
        self.log.info("xferDispatch.run(): Maximum number of threads for the queue: " + self.xferUtils.getCfgxferthreads())        

        self.initializeThreads(int(self.xferUtils.getCfgxferthreads()))        
        self.populateThreads()
        
    def populateThreads(self):
        """ Go through each queue file one by one and identify the best thread to move the file to.
        Once all threads are full, the function stop looping through queued files.
        """    	
        self.log.info("xferDispatch.populateThreads(): Start")        
        allQueuedFiles = self.xferUtils.getAllQueuedFiles() # List all files currently queued
        fullServers = set([]) # List ftp server hash which are full

        for currentQueuedFile in allQueuedFiles:
            self.log.info("xferDispatch.run(): Processing: " + currentQueuedFile)
            if self.xferUtils.areThreadsFull():
                break
            else:
                ftpserverHash = None
                try:
                    queuedJson = self.xferUtils.loadJsonFile(currentQueuedFile)
                except Exception:
                    self.log.error("xferDispatch.run(): Unable to JSON decode: " + currentQueuedFile)
                    fileUtils.CheckDir(self.dirXferFailed)
                    shutil.move(currentQueuedFile, self.dirXferFailed + os.path.basename(currentQueuedFile))
                    break

                if (queuedJson['job']['source']['type'] == 'ftp'):
                    ftpserverHash = queuedJson['job']['source']['ftpserverhash']
                    ftpserverMaxThreads = self.getMaxThreadsForFTPServer(self.dirEtc + 'config-source' + str(queuedJson['job']['source']['sourceid']) + '-ftpservers.cfg', str(queuedJson['job']['source']['ftpserverid']))
                elif  (queuedJson['job']['destination']['type'] == 'ftp'):
                    ftpserverHash = queuedJson['job']['destination']['ftpserverhash']  
                    ftpserverMaxThreads = self.getMaxThreadsForFTPServer(self.dirEtc + 'config-source' + str(queuedJson['job']['destination']['sourceid']) + '-ftpservers.cfg', str(queuedJson['job']['destination']['ftpserverid']))

                if (ftpserverHash != None): 
                    self.log.info("xferDispatch.populateThreads(): FTP Server Hash: " + ftpserverHash)
                    self.log.info("xferDispatch.populateThreads(): FTP Server Threads: " + ftpserverMaxThreads)
                    if ftpserverHash in fullServers:
                        self.log.info("xferDispatch.populateThreads(): All threads are full for this server, skipping ... ")
                    else:
                        threadStats = self.getThreadStats(ftpserverHash)
                        targetThread = self.identifyTargetThread(threadStats, int(ftpserverMaxThreads))
                        if (targetThread == None):
                            self.log.info("xferDispatch.populateThreads(): All threads are full for this server, adding FTP Hash to list of full servers ... ")
                            fullServers.add(ftpserverHash)
                        else:
                            self.log.info("xferDispatch.populateThreads(): Move file to: " + self.dirXferThreads + targetThread + '/' + os.path.basename(currentQueuedFile))
                            shutil.move(currentQueuedFile, self.dirXferThreads + targetThread + '/' + os.path.basename(currentQueuedFile))
            
    def identifyTargetThread(self, threadStats, ftpserverMaxThreads):  
        """ Identify the least occupied thread into which the file should be added
        
        Args:
            threadStats: A class, the logging interface
            ftpserverMaxThreads: An int, Maximum number of threads for this particular FTP server
        
        Returns:
            A string containing the UUID of the target thread.
        """    	
        self.log.info("xferDispatch.identifyTargetThread(): Start")        
        self.log.info("xferDispatch.identifyTargetThread(): FTP Server Max Threads: " + str(ftpserverMaxThreads))
        identifiedThread = None        
        #1- Reverse sort array by total file count and remove all threads with more self.xferUtils.getMaxFilesPerThread() files and hashCount = 0
        # since those cannot be candidates anyway
        removedFullThreads = {}
        for key in sorted(threadStats, key=lambda x: threadStats[x]['filesCount'], reverse=True):
            #print '1- ', key, threadStats[key]
            if (threadStats[key]['filesCount'] < self.xferUtils.getMaxFilesPerThread()):
                removedFullThreads[key] = threadStats[key]     
            elif (threadStats[key]['filesCount'] >= self.xferUtils.getMaxFilesPerThread() and threadStats[key]['hashCount'] > 0) :
                removedFullThreads[key] = threadStats[key]
            #else:
            #    print 'skipping...'
        
        #2- Count the number of treads with hashCount > 0
        #print removedFullThreads
        nbActiveThreads = 0;
        for key in sorted(removedFullThreads, key=lambda x: removedFullThreads[x]['filesCount'], reverse=True):
            if removedFullThreads[key]['hashCount'] > 0:
                nbActiveThreads = nbActiveThreads + 1
        self.log.info("xferDispatch.identifyTargetThread(): Number of available threads with this server Hash: " + str(nbActiveThreads))        

        if (nbActiveThreads < ftpserverMaxThreads):
            #If not all ftp server threads are used, take the one with 0 hash and the least amount of files
            for key in sorted(removedFullThreads, key=lambda x: removedFullThreads[x]['filesCount'])[:1]:
                if (removedFullThreads[key]['hashCount'] == 0):
                    identifiedThread = key
        else:
            #All server threads are used, look for a thread with hashcount > 0 but the least amount of files
            #3a - Remove all threads where hashcount = 0
            sortedFilesThreads = {}
            for key in sorted(removedFullThreads, key=lambda x: removedFullThreads[x]['filesCount'], reverse=True):
                #print '2: ', key, removedFullThreads[key]
                if (removedFullThreads[key]['hashCount'] > 0 and removedFullThreads[key]['filesCount'] < self.xferUtils.getMaxFilesPerThread()):
                    sortedFilesThreads[key] = removedFullThreads[key]                
            
            #3b - From the resulting list, get the thread with the lowest amount of files
            for key in sorted(sortedFilesThreads, key=lambda x: sortedFilesThreads[x]['filesCount'])[:1]:
                #print '3: ', key, sortedFilesThreads[key]
                identifiedThread = key             
                
        self.log.info("xferDispatch.identifyTargetThread(): Identified thread for queued file: " + str(identifiedThread))
        return identifiedThread
             
    def getMaxThreadsForFTPServer(self, configFile, serverId):  
        """ Get the maximum number of threads for a particular FTP Server
        
        Args:
            configFile: A string, Filepath of a FTP server configuration file
            serverId: An int, Server ID in the config file
        
        Returns:
            An int, Max threads for a particular FTP server
        """      	
        self.log.info("xferDispatch.getMaxThreadsForFTPServer(): Start")
        self.log.info("xferDispatch.getMaxThreadsForFTPServer(): Config File: " + configFile)
        self.log.info("xferDispatch.getMaxThreadsForFTPServer(): Server ID: " + serverId)
        ftpServer = Config(self.log, configFile)
        return ftpServer.getConfig('cfgftpserverslist' + str(serverId))[7]

    def initializeThreads(self, threadsNumber):
        """ Initialize all threads, if there has been some inactivity on a thread, it will be re-initialized
        
        Args:
            threadsNumber: Number of threads to initialize
        
        Returns:
            None
        """       	
        self.log.info("xferDispatch.initializeThreads(): Start")
        self.log.info("xferDispatch.initializeThreads(): Threads Dir: " + self.dirXferThreads)
        self.log.info("xferDispatch.initializeThreads(): Threads Number: " + str(threadsNumber))
        
        # Verify existing threads directory, delete old/hanged ones if any
        threadsCpt = 0
        for currentFilename in [f for f in os.listdir(fileUtils.CheckDir(self.dirXferThreads)) if f.endswith(".json")]:
            self.log.info("xferDispatch.initializeThreads(): Current thread file: " + currentFilename)
	    if os.path.exists(self.dirXferThreads + os.path.splitext(currentFilename)[0]):
                threadJson = self.xferUtils.loadJsonFile(self.dirXferThreads + currentFilename)                    
                if threadJson['last_job'] != None:                    
                    lastJobCompletion = dateutil.parser.parse(threadJson['last_job']['date_completed'])
                    currentDate = self.timeUtils.getCurrentDate()
                    if (currentDate-lastJobCompletion).total_seconds() < 1800:
                        self.log.info("xferDispatch.initializeThreads(): This thread has been active in the last 30 minutes and might still be active") 
                        if (threadJson.has_key('pid') and self.xferUtils.isPidAlive(threadJson['pid'])):
                            self.log.info("xferDispatch.initializeThreads(): Thread is alive, PID: " + str(threadJson['pid']))                             
                            threadsCpt = threadsCpt + 1    
                        else:
                            self.log.info("xferDispatch.initializeThreads(): This thread is not running")
                            self.clearThreadDirectory(self.dirXferThreads + os.path.splitext(currentFilename)[0])                              
                    else:
                        self.log.info("xferDispatch.initializeThreads(): This thread has been inactive for more than 30 minutes")
                        self.log.info("xferDispatch.initializeThreads(): Killing the process")
                        self.xferUtils.killThreadByPid(threadJson['pid'])
                        self.log.info("xferDispatch.initializeThreads(): Removing json file and its corresponding directory")
                        self.clearThreadDirectory(self.dirXferThreads + os.path.splitext(currentFilename)[0])                    
                else:
                    self.log.info("xferDispatch.initializeThreads(): This thread has never been executed")
                    self.log.info("xferDispatch.initializeThreads(): Removing json file and its corresponding directory")
                    self.clearThreadDirectory(self.dirXferThreads + os.path.splitext(currentFilename)[0])
            else: 
                self.log.info("xferDispatch.initializeThreads(): Associated directory does not exist: " + self.dirXferThreads + os.path.splitext(currentFilename)[0])
                self.log.info("xferDispatch.initializeThreads(): Removing: " + self.dirXferThreads + currentFilename)
                os.remove(self.dirXferThreads + currentFilename)
        
        # Create threads directories (number of threads based on above analysis
        nbThreadsToCreate = threadsNumber - threadsCpt
        self.log.info("xferDispatch.initializeThreads(): Number of threads to create: " + str(nbThreadsToCreate))
        for i in range(0, nbThreadsToCreate):
            threadUuid = uuid.uuid4()             
            self.log.info("xferDispatch.initializeThreads(): Creating thread #" + str(i) + " UUID: " + str(threadUuid))
            threadJson = {}
            threadJson['date_created'] = self.timeUtils.getCurrentDateIso()
            threadJson['uuid'] = str(threadUuid)
            threadJson['last_job'] = None
            if self.xferUtils.writeJsonFile(self.dirXferThreads + str(threadUuid) + '.json', threadJson):  
                os.makedirs(self.dirXferThreads + str(threadUuid))
                
    def clearThreadDirectory(self, currentThreadDirectory):
        """ Take a thread directory name, move all its content back to the queue, delete it and its associated json
        
        Args:
            currentThreadDirectory: A string, thread directory
        
        Returns:
            None
        """    	
        self.log.info("xferDispatch.clearThreadDirectory(): Start")
        for currentFilename in [f for f in os.listdir(currentThreadDirectory) if f.endswith(".json")]:
            fileUtils.CheckDir(self.dirXferQueue + currentFilename[0:8])
            os.rename(currentThreadDirectory + "/" + currentFilename, self.dirXferQueue + currentFilename[0:8] + '/' + currentFilename)
            self.log.info("xferDispatch.clearThreadDirectory(): Moved: " + currentFilename + " to: " + self.dirXferQueue + currentFilename[0:8] + '/')
        os.rmdir(currentThreadDirectory)
        os.remove(currentThreadDirectory + '.json')
            
    def getThreadStats(self, ftpserverHash):
        """ Build a dictionary containing the number of files currently in a thread
            as well as the number of times a specific hash is present
        
        Args:
            ftpserverHash: Hash of a particular FTP server, the hash is the unique ID of the server 
                            and is always generated the same way
        
        Returns:
            A string, Thread stats dictionary
        """       	
        threads = {}
        for currentFilename in [f for f in os.listdir(self.dirXferThreads) if f.endswith(".json")]:
            currentThreadHash = os.path.splitext(currentFilename)[0]
            self.log.info("xferDispatch.getThreadStats(): Calculating Thread: " + currentThreadHash)
            threadsFilesCount = 0
            ftpserverHashCount = 0
            # Look into the threads directory for json files, load all of them and increase counts
            for currentFilename in [f for f in os.listdir(self.dirXferThreads + currentThreadHash + '/') if f.endswith(".json")]:
                threadJson = self.xferUtils.loadJsonFile(self.dirXferThreads + currentThreadHash + '/' + currentFilename)                    
                threadsFilesCount = threadsFilesCount + 1
                if (threadJson['job']['destination']['ftpserverhash'] == ftpserverHash or threadJson['job']['source']['ftpserverhash'] == ftpserverHash ): 
                    ftpserverHashCount = ftpserverHashCount + 1
            threads[currentThreadHash] = {}
            threads[currentThreadHash]['filesCount'] = threadsFilesCount
            threads[currentThreadHash]['hashCount'] = ftpserverHashCount
            self.log.info("xferDispatch.getThreadStats(): Thread: " + currentThreadHash + ' Files Count: ' + str(threadsFilesCount) + ' Hash Count: ' + str(ftpserverHashCount))            
        return threads
    

        
