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

from wpakConfigObj import Config
from wpakTimeUtils import timeUtils
from wpakSourcesUtils import sourcesUtils

from wpakFTPUtils import FTPUtils

# This class is used to capture a picture or sensors from a source
class reportsDaily(object):
    """ This class is used to capture from a source
    
    Args:
        log: A class, the logging interface
        appConfig: A class, the app config interface
        config_dir: A string, filesystem location of the configuration directory
    	sourceId: Source ID of the source to capture
        
    Attributes:
        tbc
    """    
    def __init__(self, log, appConfig, config_dir):
        self.log = log
        self.appConfig = appConfig
        self.config_dir = config_dir

        self.configPaths = Config(self.log, self.config_dir + 'param_paths.yml')   
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirConfig = self.configPaths.getConfig('parameters')['dir_config']
        self.dirBin = self.configPaths.getConfig('parameters')['dir_bin']
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']
        self.dirSourceLive = self.configPaths.getConfig('parameters')['dir_source_live']
        self.dirSourceCapture = self.configPaths.getConfig('parameters')['dir_source_capture']
        self.dirLocale = self.configPaths.getConfig('parameters')['dir_locale']
        self.dirLocaleMessage = self.configPaths.getConfig('parameters')['dir_locale_message']
        self.dirStats = self.configPaths.getConfig('parameters')['dir_stats']        
        self.dirCache = self.configPaths.getConfig('parameters')['dir_cache']
        self.dirEmails = self.configPaths.getConfig('parameters')['dir_emails']                
        self.dirResources = self.configPaths.getConfig('parameters')['dir_resources']  
        self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']  
        self.dirXferQueue = self.configPaths.getConfig('parameters')['dir_xfer'] + 'queued/'

        self.setupLog()
        
        self.configGeneral = Config(self.log, self.dirConfig + 'config-general.cfg')
        self.initGetText(self.dirLocale, self.configGeneral.getConfig('cfgsystemlang'), self.configGeneral.getConfig('cfggettextdomain'))

        self.timeUtils = timeUtils(self)
        self.sourcesUtils = sourcesUtils(self)
        self.FTPUtils = FTPUtils(self)

    def setupLog(self):      
        """ Setup logging to file"""
        reportsLogs = self.dirLogs + "reports/"
        if not os.path.exists(reportsLogs):
            os.makedirs(reportsLogs)
        logFilename = reportsLogs + "daily.log"
        self.appConfig.set(self.log._meta.config_section, 'file', logFilename)
        self.appConfig.set(self.log._meta.config_section, 'rotate', True)
        self.appConfig.set(self.log._meta.config_section, 'max_bytes', 512000)
        self.appConfig.set(self.log._meta.config_section, 'max_files', 10)
        self.log._setup_file_log()
              
    def initGetText(self, dirLocale, cfgsystemlang, cfggettextdomain):
        """ Initialize Gettext with the corresponding translation domain
        
        Args:
            dirLocale: A string, directory location of the file
            cfgsystemlang: A string, webcampak-level language configuration parameter from config-general.cfg
            cfggettextdomain: A string, webcampak-level gettext domain configuration parameter from config-general.cfg
        
        Returns:
            None
        """    	        
        self.log.debug("reportsDaily.initGetText(): Start")
        try:
            t = gettext.translation(cfggettextdomain, dirLocale, [cfgsystemlang], fallback=True)
            _ = t.ugettext
            t.install()
            self.log.info("reportsDaily.initGetText(): " + _("Initialized gettext with Domain: %(cfggettextdomain)s - Language: %(cfgsystemlang)s - Path: %(dirLocale)s")
                                                    % {'cfggettextdomain': cfggettextdomain, 'cfgsystemlang': cfgsystemlang, 'dirLocale': dirLocale} )        
        except:
            self.log.error("No translation file available")


    def run(self):
        """ Initiate daily reports creation for all sources """
        self.log.info("reportsDaily.run(): " + _("Initiate reports creation"))
        for currentSource in self.sourcesUtils.getActiveSourcesIds():
            self.log.info("reportsDaily.run(): " + _("Processing source %(currentSource)s") % {'currentSource': str(currentSource)})
            # Identify missing reports for source
            missingReports = self.getMissingReports(currentSource)
            for currentReportDay in missingReports:
                self.generateReport(currentSource, currentReportDay)

    def generateReport(self, currentSource, currentReportDay):
        self.log.debug("reportsDaily.generateReport(): " + _("Start"))
        self.log.info("reportsDaily.generateReport(): " + _("Generating report for Source: %(currentSource)s and Day: %(currentReportDay)s") % {'currentSource': str(currentSource), 'currentReportDay': str(currentReportDay)})

        dirCurrentSourcePictures = self.dirSources + 'source' + str(currentSource) +'/' + self.configPaths.getConfig('parameters')['dir_source_pictures']
        currentJPGs = self.getPicturesStats(dirCurrentSourcePictures + str(currentReportDay) + "/")
        currentRAWs = self.getPicturesStats(dirCurrentSourcePictures + "raw/" + str(currentReportDay) + "/")
        print currentJPGs
        print currentRAWs

    def getPicturesStats(self, picturesDirectory):
        self.log.debug("reportsDaily.getPicturesStats(): " + _("Start"))
        self.log.info("reportsDaily.getPicturesStats(): " + _("Scanning directory: %(picturesDirectory)s") % {'picturesDirectory': picturesDirectory})
        listPictures = []
        picturesCount = 0
        picturesTotalSize = 0
        if os.path.exists(picturesDirectory):
            for currentPicture in os.listdir(picturesDirectory):
                if len(os.path.splitext(os.path.basename(currentPicture))[0]) == 14 and (os.path.splitext(os.path.basename(currentPicture))[1] == ".jpg" or os.path.splitext(os.path.basename(currentPicture))[1] == ".raw"):
                    pictureSize = os.path.getsize(picturesDirectory + currentPicture)
                    picturesCount =  picturesCount + 1
                    picturesTotalSize = picturesTotalSize + pictureSize
                    listPictures.append({'filename': currentPicture, 'filesize': pictureSize})
        return {'count': picturesCount, 'size': picturesTotalSize, 'list': listPictures}


    def getMissingReports(self, sourceId):
        """Compare pictures directory with reports directory to fine missing reports"""
        self.log.info("reportsDaily.getMissingReports(): " + _("Start"))
        dirCurrentSourcePictures = self.dirSources + 'source' + str(sourceId) +'/' + self.configPaths.getConfig('parameters')['dir_source_pictures']
        dirCurrentSourceReports = self.dirSources + 'source' + str(sourceId) +'/' + self.configPaths.getConfig('parameters')['dir_source_resources_reports']
        missingDays = []
        for picturesDay in os.listdir(dirCurrentSourcePictures):
            if picturesDay[0:2] == "20" and len(picturesDay) == 8:
                if os.path.isfile(dirCurrentSourceReports + picturesDay + '.json'):
                    self.log.info("reportsDaily.getMissingReports(): " + _("Report exists for day: %(picturesDay)s") % {'picturesDay': str(picturesDay)})
                else:
                    self.log.info("reportsDaily.getMissingReports(): " + _("Report does not exist for day: %(picturesDay)s") % {'picturesDay': str(picturesDay)})
                    missingDays.append(int(picturesDay))
        missingDays.sort(reverse=True)
        return missingDays





     
               