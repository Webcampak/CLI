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
from tabulate import tabulate

from wpakConfigObj import Config
from wpakTimeUtils import timeUtils
from wpakSourcesUtils import sourcesUtils
from wpakFileUtils import fileUtils
from wpakDbUtils import dbUtils

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
        self.dirLocaleEmails = self.configPaths.getConfig('parameters')['dir_locale_emails']
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
        self.dbUtils = dbUtils(self)
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

            sourceQuota = self.dbUtils.getSourceQuota(currentSource)
            sourceDiskUsage = fileUtils.CheckDirDu(self.dirSources + 'source' + str(currentSource) +'/')
            self.log.info("reportsDaily.run(): " + _("Source disk quota is: %(sourceQuota)s") % {'sourceQuota': str(sourceQuota)})
            self.log.info("reportsDaily.run(): " + _("Source disk usage is: %(sourceDiskUsage)s") % {'sourceDiskUsage': str(sourceDiskUsage)})
            if sourceQuota == None:
                sourceDiskPercentUsed = None
            else:
                sourceDiskPercentUsed = int(sourceDiskUsage/sourceQuota)

            sourceSchedule = self.getSourceSchedule(currentSource)

            emailReports = []
            # Identify missing reports for source
            missingReports = self.getMissingReports(currentSource)
            for currentReportDay in missingReports:
                if int(self.timeUtils.getCurrentDate().strftime("%Y%m%d")) == currentReportDay:
                    self.log.info("reportsDaily.run(): " + _("Skipping report for current day: %(currentReportDay)s") % {'currentReportDay': str(currentReportDay)})
                else:
                    currentSourceReport = self.generateReport(currentSource, currentReportDay, sourceSchedule)
                    currentSourceReport['source'] = {'quota': sourceQuota, 'usage': sourceDiskUsage, 'percentUsed': sourceDiskPercentUsed}
                    currentSourceReport['disk'] = self.getFileSystemUsage(self.dirSources)
                    dirCurrentSourceReports = self.dirSources + 'source' + str(currentSource) +'/' + self.configPaths.getConfig('parameters')['dir_source_resources_reports']
                    jsonReportFile = dirCurrentSourceReports + str(currentReportDay) + '.json'
                    self.log.info("reportsDaily.run(): " + _("Preparing to save report in %(jsonReportFile)s") % {'jsonReportFile': str(jsonReportFile)})
                    if self.writeJsonFile(jsonReportFile,currentSourceReport):
                        print self.prepareEmailReportContent(currentSource, currentReportDay, currentSourceReport)
                        emailReports.append({'sourceid': currentSource, 'reportDay': currentReportDay, 'report': currentSourceReport})
                        #Send email
                    else:
                        self.log.error("reportsDaily.run(): " + _("Error saving report file to disk %(jsonReportFile)s") % {'jsonReportFile': str(jsonReportFile)})

        self.log.info("reportsDaily.run(): " + _("Getting ready to send reports"))
        print self.dbUtils.getUserWithSourceAlerts()

    def prepareEmailReportContent(self, currentSource, currentReportDay, currentSourceReport):
        self.log.debug("reportsDaily.prepareEmailReportContent(): " + _("Start"))
        self.log.info("reportsDaily.prepareEmailReportContent(): " + _("Preparing report content for Source: %(currentSource)s and Day: %(currentReportDay)s") % {'currentSource': str(currentSource), 'currentReportDay': str(currentReportDay)})
        self.configSource = Config(self.log, self.dirEtc + 'config-source' + str(currentSource) + '.cfg')
        dirCurrentLocaleEmails = self.dirLocale + self.configSource.getConfig('cfgsourcelanguage') + "/" + self.dirLocaleEmails
        dailyReportContentSourceFile = dirCurrentLocaleEmails + "dailyReportContentSource.txt"
        if os.path.isfile(dailyReportContentSourceFile) == False:
            dailyReportContentSourceFile = self.dirLocale + "en_US.utf8/" + self.dirLocaleEmails + "dailyReportContentSource.txt"
        self.log.info("capture.sendCaptureReport(): " + _("Using message content file: %(dailyReportContentSourceFile)s") % {'dailyReportContentSourceFile': dailyReportContentSourceFile} )
        dailyReportContentSourceFile = open(dailyReportContentSourceFile, 'r')
        dailyReportContentSource = dailyReportContentSourceFile.read()
        dailyReportContentSourceFile.close()

        dailyReportContentSource = dailyReportContentSource.replace("#SOURCEID#", str(currentSource))
        dailyReportContentSource = dailyReportContentSource.replace("#SOURCENAME#", str(currentSource))

        headers = ["Description", "Used", "Available" , "% Used"]
        table = [\
            ["Source",currentSourceReport['source']['usage'], currentSourceReport['source']['quota'], currentSourceReport['source']['percentUsed']]\
            ,["Total Disk",currentSourceReport['disk']['used'], currentSourceReport['disk']['total'], currentSourceReport['disk']['percentUsed']]\
            ]
        print tabulate(table, headers, tablefmt="fancy_grid")



        """
        headers = ["Description", "JPG", "RAW" , "TOTAL"]
        table = [["Capture Count",currentSourceReport['']],["eggs",451],["bacon",0]]
        print tabulate(table, headers, tablefmt="fancy_grid")
        """

        """
        Source: #SOURCEID# - #SOURCENAME#
        Total Capture Count: {{ reportItem.total.count }}
        Total Capture Size: {{ emailTable.bytesToSize(reportItem.total.size) }}
        Total Capture Score: {{ reportItem.schedule.overall.plannedSlots }} %
        --------------------------------------------------------------------------------
        Scheduled Slots: {{ reportItem.schedule.overall.plannedSlots }}
        JPG Capture Count: {{ reportItem.jpg.count }}
        JPG Capture Size: {{ emailTable.bytesToSize(reportItem.jpg.size) }}
        JPG Success Rate: {{ reportItem.schedule.jpg.successRate }}
        RAW Capture Count: {{ reportItem.raw.count }}
        RAW Capture Size: {{ emailTable.bytesToSize(reportItem.raw.size) }}
        RAW Success Rate: {{ reportItem.schedule.raw.successRate }}
        """


    def sendReportEmail(self, currentSource, currentReportDay, sourceSchedule):
        self.log.debug("reportsDaily.sendReportEmail(): " + _("Start"))
        self.log.info("reportsDaily.sendReportEmail(): " + _("Preparing to send report for Source: %(currentSource)s and Day: %(currentReportDay)s") % {'currentSource': str(currentSource), 'currentReportDay': str(currentReportDay)})

        emailReportSubject = self.dirCurrentLocaleMessages + "dailyReportSubject.txt"
        emailReportContent = self.dirCurrentLocaleMessages + "dailyReportContent.txt"
        if os.path.isfile(emailReportContent) == False:
            emailReportSubject = self.dirLocale + "en_US.utf8/" + self.dirLocaleMessage + "dailyReportSubject.txt"
            emailReportContent = self.dirLocale + "en_US.utf8/" + self.dirLocaleMessage + "dailyReportContent.txt"
        self.log.info("capture.sendCaptureReport(): " + _("Using message subject file: %(emailReportSubject)s") % {'emailReportSubject': emailReportSubject} )
        self.log.info("capture.sendCaptureReport(): " + _("Using message content file: %(emailReportContent)s") % {'emailReportContent': emailReportContent} )




    def generateReport(self, currentSource, currentReportDay, sourceSchedule):
        self.log.debug("reportsDaily.generateReport(): " + _("Start"))
        self.log.info("reportsDaily.generateReport(): " + _("Generating report for Source: %(currentSource)s and Day: %(currentReportDay)s") % {'currentSource': str(currentSource), 'currentReportDay': str(currentReportDay)})

        dirCurrentSourcePictures = self.dirSources + 'source' + str(currentSource) +'/' + self.configPaths.getConfig('parameters')['dir_source_pictures']
        currentJPGs = self.getPicturesStats(dirCurrentSourcePictures + str(currentReportDay) + "/")
        currentRAWs = self.getPicturesStats(dirCurrentSourcePictures + "raw/" + str(currentReportDay) + "/")
        reportDatetime = datetime.strptime(str(currentReportDay) + "120000", "%Y%m%d%H%M%S")
        if sourceSchedule != None:
            scheduleReport = self.compareScheduleWithDisk(sourceSchedule, currentJPGs, currentRAWs, reportDatetime)
        else:
            scheduleReport = None

        return {\
            'capture': {'JPG': currentJPGs, 'RAW': currentRAWs}\
            , 'schedule': scheduleReport
            }

    def compareScheduleWithDisk(self, sourceSchedule, currentJPGs, currentRAWs, reportDatetime):
        self.log.debug("reportsDaily.compareScheduleWithDisk(): " + _("Start"))
        self.log.info("reportsDaily.compareScheduleWithDisk(): " + _("Comparing Scedhule with Disk"))
        reportDayOfWeek = str(int(reportDatetime.strftime("%w")) + 1)
        reportDate = reportDatetime.strftime("%Y%m%d")
        intersectJPG = {}
        extraJPG = {}
        missingJPG = []
        intersectRAW = {}
        extraRAW = {}
        missingRAW = []
        for hour in range(24):
            for minute in range(59):
                if hour < 10:
                    fullHour = "0" + str(hour)
                else:
                    fullHour = str(hour)
                if minute < 10:
                    fullMinute = "0" + str(minute)
                else:
                    fullMinute = str(minute)
                self.log.debug("reportsDaily.compareScheduleWithDisk(): " + _("Testing timeslot: %(fullHour)s:%(fullMinute)s") % {'fullHour': str(fullHour), 'fullMinute': str(fullMinute)})
                if reportDayOfWeek in sourceSchedule:
                    # Test if filename exists
                    testIdx = reportDate + fullHour + fullMinute
                    fullHour = str(int(fullHour))
                    fullMinute = str(int(fullMinute))
                    if testIdx in currentJPGs['list']:
                        if fullHour in sourceSchedule[reportDayOfWeek] and fullMinute in sourceSchedule[reportDayOfWeek][fullHour] and sourceSchedule[reportDayOfWeek][fullHour][fullMinute] == 'Y':
                            intersectJPG[testIdx] = currentJPGs['list'][testIdx]
                        else:
                            extraJPG[testIdx] = currentJPGs['list'][testIdx]
                    else:
                        if fullHour in sourceSchedule[reportDayOfWeek] and fullMinute in sourceSchedule[reportDayOfWeek][fullHour] and sourceSchedule[reportDayOfWeek][fullHour][fullMinute] == 'Y':
                            missingJPG.append(testIdx)

                    if testIdx in currentRAWs['list']:
                        if fullHour in sourceSchedule[reportDayOfWeek] and fullMinute in sourceSchedule[reportDayOfWeek][fullHour] and sourceSchedule[reportDayOfWeek][fullHour][fullMinute] == 'Y':
                            intersectRAW[testIdx] = currentRAWs['list'][testIdx]
                        else:
                            extraRAW[testIdx] = currentRAWs['list'][testIdx]
                    else:
                        if fullHour in sourceSchedule[reportDayOfWeek] and fullMinute in sourceSchedule[reportDayOfWeek][fullHour] and sourceSchedule[reportDayOfWeek][fullHour][fullMinute] == 'Y':
                            missingRAW.append(testIdx)
        return { \
            'onschedule': {'JPG': {'list': intersectJPG, 'count' : len(intersectJPG)}, 'RAW': {'list': intersectRAW, 'count' : len(intersectRAW)}} \
            , 'missing': {'JPG': {'list': missingJPG, 'count' : len(missingJPG)}, 'RAW': {'list': missingRAW, 'count' : len(missingRAW)}} \
            , 'extra': {'JPG': {'list': extraJPG, 'count' : len(extraJPG)}, 'RAW': {'list': extraRAW, 'count' : len(extraRAW)}} \
            }


    def getPicturesStats(self, picturesDirectory):
        self.log.debug("reportsDaily.getPicturesStats(): " + _("Start"))
        self.log.info("reportsDaily.getPicturesStats(): " + _("Scanning directory: %(picturesDirectory)s") % {'picturesDirectory': picturesDirectory})
        listPictures = {}
        picturesCount = 0
        picturesTotalSize = 0
        if os.path.exists(picturesDirectory):
            for currentPicture in os.listdir(picturesDirectory):
                if len(os.path.splitext(os.path.basename(currentPicture))[0]) == 14 and (os.path.splitext(os.path.basename(currentPicture))[1] == ".jpg" or os.path.splitext(os.path.basename(currentPicture))[1] == ".raw"):
                    pictureSize = os.path.getsize(picturesDirectory + currentPicture)
                    picturesCount =  picturesCount + 1
                    picturesTotalSize = picturesTotalSize + pictureSize
                    pictureIdx = currentPicture[0:12]
                    listPictures[pictureIdx] = {'filename': currentPicture, 'filesize': pictureSize}
                    #listPictures.append({'filename': currentPicture, 'filesize': pictureSize})
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

    def getSourceSchedule(self, currentSource):
        self.log.debug("reportsDaily.getSourceSchedule(): " + _("Start"))
        scheduleFile = self.dirEtc + 'config-source' + str(currentSource) + '-schedule.json';
        self.log.info("reportsDaily.generateReport(): " + _("Looking for Schedule file: %(scheduleFile)s") % {'scheduleFile': str(scheduleFile)})
        if os.path.isfile(scheduleFile):
            with open(scheduleFile) as scheduleJsonFile:
                sourceSchedule = json.load(scheduleJsonFile)
                if len(sourceSchedule) > 0:
                    return sourceSchedule
                else:
                    return None
        else:
            return None



    def writeJsonFile(self, jsonFile, jsonContent):
        """ Write the content of a dictionary to a JSON file
        Args:
            None

        Returns:
            Boolean: Success of the operation
        """
        self.log.debug("reportsDaily.writeJsonFile(): " + _("Start"))
        if fileUtils.CheckFilepath(jsonFile) != "":
            with open(jsonFile, "w") as threadJsonFile:
                threadJsonFile.write(json.dumps(jsonContent))
            return True
        return False

    def getFileSystemUsage(self, directory):
        """Get disk usage for a partition located in a specific directory """
        self.log.debug("reportsDaily.getFileSystemUsage(): " + _("Start"))
        statvfs = os.statvfs(directory)
        totalSpace = statvfs.f_frsize * statvfs.f_blocks         # Size of filesystem in bytes
        totalFreeSpace = statvfs.f_frsize * statvfs.f_bavail     # Number of free bytes that ordinary user
        return {'free': totalFreeSpace, 'total': totalSpace, 'used': int(totalSpace - totalFreeSpace), 'percentUsed': int(int(totalSpace - totalFreeSpace)/totalSpace)}

     
               