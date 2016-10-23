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
import gettext

from wpakConfigObj import Config
from wpakFileUtils import fileUtils
from wpakXferUtils import xferUtils
from wpakFTPTransfer import FTPTransfer


# This class is used to start & process stored in the transfer queue

class xferStop:
    def __init__(self, log, appConfig, config_dir, threadUUID):
        self.log = log
        self.appConfig = appConfig
        self.config_dir = config_dir
        self.configPaths = Config(self.log, self.config_dir + 'param_paths.yml')
        self.xferUtils = xferUtils(self.log, self.config_dir)
        self.argThreadUUID = threadUUID

        self.dirXferThreads = fileUtils.CheckDir(self.configPaths.getConfig('parameters')['dir_xfer'] + 'threads/')
        self.dirXferQueue = fileUtils.CheckDir(self.configPaths.getConfig('parameters')['dir_xfer'] + 'queued/')
        self.dirXferFailed = fileUtils.CheckDir(self.configPaths.getConfig('parameters')['dir_xfer'] + 'failed/')
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirConfig = self.configPaths.getConfig('parameters')['dir_config']
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']
        self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']
        self.dirLocale = self.configPaths.getConfig('parameters')['dir_locale']
        self.dirLocaleMessage = self.configPaths.getConfig('parameters')['dir_locale_message']

        self.setupLog()

        self.configGeneral = Config(self.log, self.dirConfig + 'config-general.cfg')
        self.initGetText(self.dirLocale, self.configGeneral.getConfig('cfgsystemlang'),
                         self.configGeneral.getConfig('cfggettextdomain'))

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
        logFilename = xferLogs + "stop.log"
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
        self.log.info("xferStop.run(): Running XFer Start")
        if (self.getArgThreadUUID() == None):
            self.log.info("xferStop.run(): Stopping all threads currently running")
            for currentThreadUUID in self.xferUtils.getThreadsUUID():
                self.stopThread(currentThreadUUID)
                self.log.info("xferStop.run(): ----")
        else:
            self.stopThread(self.getArgThreadUUID())

    # Function: stopThread
    # Description: Stop a thread by ID
    ## threadUUID: UUID of the thread
    # Return: Nothing       
    def stopThread(self, threadUUID):
        self.log.info("(" + str(os.getpid()) + ")xferStop.stopThread(): Processing Thread UUID: " + threadUUID)
        threadPid = self.xferUtils.getThreadPid(threadUUID)
        if self.xferUtils.isPidAlive(threadPid):
            self.log.info("(" + str(os.getpid()) + ")xferStop.stopThread(): Thread is currently alive, issuing SIGKILL")
            self.xferUtils.killThreadByPid(threadPid)
        else:
            self.log.info("(" + str(os.getpid()) + ")xferStop.stopThread(): Thread is not alive, doing nothing")
