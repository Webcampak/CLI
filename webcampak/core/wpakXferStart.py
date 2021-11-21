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

from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from builtins import object
import os
from multiprocessing import Process
import gettext

from .wpakConfigObj import Config
from .wpakFileUtils import fileUtils
from .wpakXferUtils import xferUtils
from .wpakFTPTransfer import FTPTransfer
from .wpakTimeUtils import timeUtils


# This class is used to start & process stored in the transfer queue

class xferStart(object):
    def __init__(self, log, appConfig, config_dir, threadUUID):
        self.log = log
        self.appConfig = appConfig
        self.config_dir = config_dir
        self.configPaths = Config(self.log, self.config_dir + 'param_paths.yml')
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirConfig = self.configPaths.getConfig('parameters')['dir_config']
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']
        self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']
        self.dirLocale = self.configPaths.getConfig('parameters')['dir_locale']
        self.dirLocaleMessage = self.configPaths.getConfig('parameters')['dir_locale_message']
        self.dirSyncReports = self.configPaths.getConfig('parameters')['dir_sync-reports']

        self.setupLog()

        self.configGeneral = Config(self.log, self.dirConfig + 'config-general.cfg')
        self.initGetText(self.dirLocale, self.configGeneral.getConfig('cfgsystemlang'),
                         self.configGeneral.getConfig('cfggettextdomain'))

        self.xferUtils = xferUtils(self.log, self.config_dir)
        self.timeUtils = timeUtils(self)

        self.argThreadUUID = threadUUID

        self.dirXferThreads = fileUtils.CheckDir(self.configPaths.getConfig('parameters')['dir_xfer'] + 'threads/')
        self.dirXferQueue = fileUtils.CheckDir(self.configPaths.getConfig('parameters')['dir_xfer'] + 'queued/')
        self.dirXferFailed = fileUtils.CheckDir(self.configPaths.getConfig('parameters')['dir_xfer'] + 'failed/')

        self.maxFilesPerThread = 10

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
            self.log.info("capture.initGetText(): " + _(
                "Initialized gettext with Domain: %(cfggettextdomain)s - Language: %(cfgsystemlang)s - Path: %(dirLocale)s")
                          % {'cfggettextdomain': cfggettextdomain, 'cfgsystemlang': cfgsystemlang,
                             'dirLocale': dirLocale})
        except:
            self.log.error("No translation file available")

    def setupLog(self):
        """ Setup logging to file """
        xferLogs = self.dirLogs + "xfer/"
        if not os.path.exists(xferLogs):
            os.makedirs(xferLogs)
        logFilename = xferLogs + "start.log"
        self.appConfig.set(self.log._meta.config_section, 'file', logFilename)
        self.appConfig.set(self.log._meta.config_section, 'rotate', True)
        self.appConfig.set(self.log._meta.config_section, 'max_bytes', 512000)
        self.appConfig.set(self.log._meta.config_section, 'max_files', 10)
        self.log._setup_file_log()

        # Define setters and getters

    def getArgThreadUUID(self):
        return self.argThreadUUID

    # Start threads and process their content
    # Function: run
    # Description: Start the threads processing process
    # Each thread will get started in its own thread.
    # Return: Nothing           
    def run(self):
        # Load the config containing all paths and the general config file
        self.log.info("xferStart.run(): Running XFer Start")
        if (self.getArgThreadUUID() == None):
            self.log.info("xferStart.run(): Starting all threads in parrallel")
            p = {}
            for currentThreadUUID in self.xferUtils.getThreadsUUID():
                self.log.info("xferStart.run(): Thread: " + currentThreadUUID)
                if self.xferUtils.isThreadRunning(currentThreadUUID) == False:
                    p[currentThreadUUID] = Process(target=self.startThread, args=(currentThreadUUID,))
                    p[currentThreadUUID].start()
                    self.xferUtils.setThreadPid(currentThreadUUID, p[currentThreadUUID].pid)
                else:
                    self.log.info("xferStart.run(): Thread already running: " + currentThreadUUID)

                self.log.info("xferStart.run(): ----")
                # p[currentThreadUUID].join()
                # self.startThread(currentThreadUUID) #To be replaced by calling threads individually with the --thread option
        else:
            self.startThread(self.getArgThreadUUID())

    # Function: startThread
    # Description: Process the content of a thread
    ## threadUUID: UUID of the thread, each UUID contains an both a json files containing thread details as well 
    ## as a directory containing actual jobs. The function all itself until the thread directory is empty
    ## The thread directory gets populated from the queue by calling "webcampak xfer dispatch" from the command line or a cron job
    # Return: Nothing       
    def startThread(self, threadUUID):
        self.log.info("(" + str(os.getpid()) + ")xferStart.startThread(): Processing Thread UUID: " + threadUUID)
        self.log.info("(" + str(os.getpid()) + ")xferStart.startThread(): Thread process: " + str(os.getpid()))
        # Load the config containing all paths and the general config file
        if self.xferUtils.checkThreadUUID(threadUUID):
            currentThreadQueueCount = self.xferUtils.countThreadsQueue(threadUUID)
            if (currentThreadQueueCount == 0):
                self.log.info("(" + str(os.getpid()) + ")xferStart.startThread(): Thread is empty leaving process")
            else:
                self.log.info(
                    "(" + str(os.getpid()) + ")xferStart.startThread(): Number of files left in the thread: " + str(
                        currentThreadQueueCount))
                firstThreadFile = self.xferUtils.getFirstThreadFile(threadUUID)
                if firstThreadFile != None:
                    self.log.info(
                        "(" + str(os.getpid()) + ")xferStart.startThread(): Processing File: " + firstThreadFile)
                    self.processJob(threadUUID, firstThreadFile)
                    # At the end of the process, the thread calls itself again, to rerun the function until there are no more files into the queue
                    self.startThread(threadUUID)
        else:
            self.log.info(
                "(" + str(os.getpid()) + ")xferStart.startThread(): Thread UUID does not exist: " + threadUUID)

    # Function: processJob
    # Description; This function initiate processing of a xfer job
    ## threadUUID: Thread UUID where the file is located
    ## firstThreadFile: Filepath of the job to be processed
    # Return: Nothing            
    def processJob(self, threadUUID, firstThreadFile):
        self.log.info(
            "(" + str(os.getpid()) + ")xferStart.processJob(): Thread: " + threadUUID + " - Job:" + firstThreadFile)
        jobJsonContent = self.xferUtils.loadJsonFile(firstThreadFile)
        # Change job status to processing and save back to file
        jobJsonContent['job']['status'] = 'processing'
        self.xferUtils.writeJsonFile(firstThreadFile, jobJsonContent)
        # Calculate source and destination file size
        print("Source: " + jobJsonContent['job']['source']['filepath'])
        print("Destination: " + jobJsonContent['job']['destination']['filepath'])
        jobSourceFilesize = self.getJobFilesize(jobJsonContent['job']['source'])
        jobJsonContent = self.xferUtils.logToJson(firstThreadFile, jobJsonContent,
                                                  'Checking file size on source: ' + str(jobSourceFilesize) + ' bytes')
        jobDestinationFilesize = self.getJobFilesize(jobJsonContent['job']['destination'])
        jobJsonContent = self.xferUtils.logToJson(firstThreadFile, jobJsonContent,
                                                  'Checking file size on destination: ' + str(
                                                      jobDestinationFilesize) + ' bytes')
        # If filesize are identical, there is no need to transfer the file and the job can be removed
        if (jobSourceFilesize != jobDestinationFilesize):
            self.log.info("(" + str(
                os.getpid()) + ")xferStart.processJob(): Source and destination are different, starting process")
            jobJsonContent = self.xferUtils.logToJson(firstThreadFile, jobJsonContent,
                                                      'Source filesize different from destination filesize, copying file')
            # Set or increment the retries count for the job
            if 'retries' in jobJsonContent['job']:
                jobJsonContent['job']['retries'] = int(jobJsonContent['job']['retries']) - 1
            else:
                jobJsonContent['job']['retries'] = 0

            self.log.info("(" + str(os.getpid()) + ")xferStart.processJob(): Current retries count: " + str(
                jobJsonContent['job']['retries']))

            # if (jobJsonContent['job']['retries'] == 0):
            #    exit()

            if (jobJsonContent['job']['source']['type'] == 'filesystem' and jobJsonContent['job']['destination'][
                'type'] == 'ftp'):
                self.log.info("(" + str(
                    os.getpid()) + ")xferStart.processJob(): Copy from local source to remote FTP destination")
                jobJsonContent['job']['filesourceid'] = jobJsonContent['job']['source']['sourceid']
                jobJsonContent = self.xferUtils.logToJson(firstThreadFile, jobJsonContent,
                                                          'Copying from source filesystem to destination FTP')
                jobJsonContent = self.processFTPFile(firstThreadFile, jobJsonContent, 'destination', 'source',
                                                     jobSourceFilesize)
                self.xferUtils.setThreadLastJob(threadUUID, jobJsonContent['job']['xfer_report'])
                self.moveThreadFileAfterTransfer(jobJsonContent, firstThreadFile)

            elif (jobJsonContent['job']['source']['type'] == 'ftp' and jobJsonContent['job']['destination'][
                'type'] == 'filesystem'):
                self.log.info("(" + str(
                    os.getpid()) + ")xferStart.processJob(): Will copy from remote FTP source to local filesystem")
                jobJsonContent['job']['filesourceid'] = jobJsonContent['job']['destination']['sourceid']
                jobJsonContent = self.xferUtils.logToJson(firstThreadFile, jobJsonContent,
                                                          'Copying from source FTP to destination filesystem')
                jobJsonContent = self.processFTPFile(firstThreadFile, jobJsonContent, 'source', 'destination',
                                                     jobSourceFilesize)
                self.xferUtils.setThreadLastJob(threadUUID, jobJsonContent['job']['xfer_report'])
                self.moveThreadFileAfterTransfer(jobJsonContent, firstThreadFile)

            elif (jobJsonContent['job']['source']['type'] == 'filesystem' and jobJsonContent['job']['destination'][
                'type'] == 'filesystem'):
                jobJsonContent['job']['status'] = 'completed'
                jobJsonContent = self.xferUtils.logToJson(firstThreadFile, jobJsonContent,
                                                          'ERROR: Copying from filesystem to filesystem is not yet supported')

            elif (jobJsonContent['job']['source']['type'] == 'ftp' and jobJsonContent['job']['destination'][
                'type'] == 'ftp'):
                jobJsonContent['job']['status'] = 'completed'
                jobJsonContent = self.xferUtils.logToJson(firstThreadFile, jobJsonContent,
                                                          'ERROR: Copying from FTP to FTP is not yet supported')
        elif (int(jobSourceFilesize)):
            self.log.info("(" + str(
                os.getpid()) + ")xferStart.processJob(): Error, file does not exist on source, verify your configuration")
            os.remove(firstThreadFile)
        else:
            self.log.info("(" + str(os.getpid()) + ")xferStart.processJob(): File already exists, not copying anything")
            os.remove(firstThreadFile)

    # Function: moveThreadFileAfterTransfer
    # Description: Once file has been transfered, this function take care of moving and gzipping the job to its final location
    ## jobJsonContent: Current content of the job
    ## firstThreadFile: Filepath of the job
    # Return: Nothing         
    def moveThreadFileAfterTransfer(self, jobJsonContent, firstThreadFile):
        self.log.info("(" + str(os.getpid()) + ")xferStart.moveThreadFileAfterTransfer(): Filepath: " + firstThreadFile)
        if (jobJsonContent['job']['xfer_report'] != None):
            self.log.info("(" + str(
                os.getpid()) + ")xferStart.moveThreadFileAfterTransfer(): Transfer has been successful, storing completed file")
            if 'sync-report' in jobJsonContent['job']:
                #destinationFilePath = self.dirSources + "/source" + str(jobJsonContent['job']['filesourceid']) + "/resources/sync-reports/" + os.path.splitext(jobJsonContent['job']['sync-report']['filename'])[0] + "/"
                destinationFilePath = self.dirSyncReports + "/completed/" + os.path.splitext(jobJsonContent['job']['sync-report']['filename'])[0] + "/"
            else:
                destinationFilePath = self.dirSources + "/source" + str(
                    jobJsonContent['job']['filesourceid']) + "/resources/xfer/" + os.path.basename(firstThreadFile)[
                                                                                  0:8] + "/"
            self.log.info(
                "(" + str(os.getpid()) + ")xferStart.moveThreadFileAfterTransfer(): Storing to: " + destinationFilePath)
            destinationJobFile = fileUtils.CheckDir(destinationFilePath)
            self.xferUtils.writeJsonFileGzip(destinationFilePath + os.path.basename(firstThreadFile) + ".gz",
                                             jobJsonContent)
            self.log.info(
                "(" + str(os.getpid()) + ")xferStart.moveThreadFileAfterTransfer(): Removing file: " + firstThreadFile)
            os.remove(firstThreadFile)

        elif (jobJsonContent['job']['xfer_report'] == None and jobJsonContent['job']['retries'] >= 0):
            self.log.info("(" + str(
                os.getpid()) + ")xferStart.moveThreadFileAfterTransfer(): Transfer failed, moving file back to queue")
            fileUtils.CheckDir(self.dirXferQueue + os.path.basename(firstThreadFile)[0:8])
            os.rename(firstThreadFile,
                      self.dirXferQueue + os.path.basename(firstThreadFile)[0:8] + '/' + os.path.basename(
                          firstThreadFile))
            self.log.info(
                "xferDispatch.clearThreadDirectory(): Moved: " + firstThreadFile + " to: " + self.dirXferQueue + os.path.basename(
                    firstThreadFile)[0:8] + '/')
        else:
            self.log.info("(" + str(
                os.getpid()) + ")xferStart.moveThreadFileAfterTransfer(): Transfer failed and exceeded retries, moving file to failed directory")
            fileUtils.CheckDir(self.dirXferFailed + os.path.basename(firstThreadFile)[0:8])
            self.xferUtils.writeJsonFileGzip(
                self.dirXferFailed + os.path.basename(firstThreadFile)[0:8] + '/' + os.path.basename(
                    firstThreadFile) + '.gz', jobJsonContent)
            self.log.info("(" + str(
                os.getpid()) + ")xferStart.moveThreadFileAfterTransfer(): Target filename for failed file: " + self.dirXferFailed + os.path.basename(
                firstThreadFile)[0:8] + '/' + os.path.basename(firstThreadFile) + '.gz')
            self.log.info(
                "(" + str(os.getpid()) + ")xferStart.moveThreadFileAfterTransfer(): Removing file: " + firstThreadFile)
            os.remove(firstThreadFile)


            # Function: processFTPFile

    # Description: Transfer (upload or download) the file to its location and generate an xfer report
    ## firstThreadFile: Filepath of the job
    ## jobJsonContent: Current content of the job
    ## ftpFileLocation: indicate whether the ftp transfer happen for the source of for the destination, used to determine whether an upload or a download needs to happen
    ## localFileLocation: indicate whether the local transfer happen for the source of for the destination, used to determine whether an upload or a download needs to happen
    ## sourceFilesize: filesize of the file to be transferred
    # Return: updated jobJsonContent              
    def processFTPFile(self, firstThreadFile, jobJsonContent, ftpFileLocation, localFileLocation, sourceFilesize):
        self.log.info("(" + str(os.getpid()) + ")xferStart.putFTPFile()")
        currentFTP = FTPTransfer(self.log, self.config_dir)
        jobJsonContent = self.xferUtils.logToJson(firstThreadFile, jobJsonContent, 'Establishing FTP connection')
        currentFTPConnectionStatus = currentFTP.initByServerId(jobJsonContent['job'][ftpFileLocation]['sourceid'],
                                                               jobJsonContent['job'][ftpFileLocation]['ftpserverid'])
        localFilepath = self.dirSources + 'source' + str(jobJsonContent['job'][localFileLocation]['sourceid']) + '/' + \
                        jobJsonContent['job'][localFileLocation]['filepath']
        ftpServerConfig = Config(self.log, self.dirEtc + "config-source" + str(
            jobJsonContent['job'][ftpFileLocation]['sourceid']) + "-ftpservers.cfg")
        remoteFilepath = \
        ftpServerConfig.getConfig('cfgftpserverslist' + str(jobJsonContent['job'][ftpFileLocation]['ftpserverid']))[4] + \
        jobJsonContent['job'][ftpFileLocation]['filepath']
        startDate = self.timeUtils.getCurrentDate()
        if ftpFileLocation == 'destination':
            ftpTransferSuccess = currentFTP.putFile(localFilepath, remoteFilepath)
            ftpDirection = 'upload'
        else:
            ftpTransferSuccess = currentFTP.getFile(localFilepath, remoteFilepath)
            ftpDirection = 'download'

        if ftpTransferSuccess:
            endDate = self.timeUtils.getCurrentDate()
            transferTime = int((endDate - startDate).total_seconds() * 1000)
            jobJsonContent['job']['xfer_report'] = {}
            jobJsonContent['job']['xfer_report']['date_started'] = startDate.isoformat()
            jobJsonContent['job']['xfer_report']['date_completed'] = endDate.isoformat()
            jobJsonContent['job']['xfer_report']['bytes'] = sourceFilesize
            jobJsonContent['job']['xfer_report']['transfertime'] = transferTime
            jobJsonContent['job']['xfer_report']['direction'] = ftpDirection
            jobJsonContent = self.xferUtils.logToJson(firstThreadFile, jobJsonContent,
                                                      'File successfully transferred in ' + str(transferTime) + ' ms')
        else:
            jobJsonContent = self.xferUtils.logToJson(firstThreadFile, jobJsonContent, 'Unable to upload file')
            jobJsonContent['job']['xfer_report'] = {}
        currentFTP.closeFtp()
        return jobJsonContent

    # Function: getJobFilesize
    # Description: Calculate size of the file to be transferred or is local equivalent
    ## filepath: Path of the file to be transferred
    ## job: Specific ['source] or ['destination'] job portion of the array
    # Return: file size
    def getJobFilesize(self, job):
        self.log.info("(" + str(os.getpid()) + ")xferStart.getJobFilesize(): Start")
        fileSize = 0
        if (job['type'] == 'filesystem'):
            filesystemPath = self.dirSources + 'source' + str(job['sourceid']) + '/' + job['filepath']
            self.log.info("(" + str(os.getpid()) + ")xferStart.getJobFilesize(): Filesystem path: " + filesystemPath)
            if (os.path.isfile(filesystemPath)):
                fileSize = os.path.getsize(filesystemPath)
        elif (job['type'] == 'ftp'):
            ftpServerConfig = Config(self.log, self.dirEtc + "config-source" + str(job['sourceid']) + "-ftpservers.cfg")
            ftpFilepath = ftpServerConfig.getConfig('cfgftpserverslist' + str(job['ftpserverid']))[4] + job['filepath']
            self.log.info("(" + str(os.getpid()) + ")xferStart.getJobFilesize(): FTP path: " + ftpFilepath)
            currentFTP = FTPTransfer(self.log, self.config_dir)
            currentFTPConnectionStatus = currentFTP.initByServerId(job['sourceid'], job['ftpserverid'])
            if (currentFTPConnectionStatus):
                fileSize = currentFTP.getFilesize(ftpFilepath)
            currentFTP.closeFtp()
        return fileSize
