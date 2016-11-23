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
from tabulate import tabulate
import socket

from wpakConfigObj import Config
from wpakTimeUtils import timeUtils
from wpakSourcesUtils import sourcesUtils
from wpakFileUtils import fileUtils
from wpakDbUtils import dbUtils
from wpakEmailObj import emailObj
from wpakFTPUtils import FTPUtils
from wpakAlertsObj import alertObj
from wpakDbUtils import dbUtils

class alertsCapture(object):
    """ This class is used to verify if pictures are properly captured and not running late
    
    Args:
        log: A class, the logging interface
        appConfig: A class, the app config interface
        config_dir: A string, filesystem location of the configuration directory
    	sourceId: Source ID of the source to capture
        
    Attributes:
        tbc
    """

    def __init__(self, log, appConfig, config_dir, sourceId):
        self.log = log
        self.appConfig = appConfig
        self.config_dir = config_dir
        self.sourceId = sourceId

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
        self.initGetText(self.dirLocale, self.configGeneral.getConfig('cfgsystemlang'),
                         self.configGeneral.getConfig('cfggettextdomain'))

        self.timeUtils = timeUtils(self)
        self.sourcesUtils = sourcesUtils(self)
        self.dbUtils = dbUtils(self)
        self.dbUtils = dbUtils(self)

    def setupLog(self):
        """ Setup logging to file"""
        reportsLogs = self.dirLogs + "alerts/"
        if not os.path.exists(reportsLogs):
            os.makedirs(reportsLogs)
        logFilename = reportsLogs + "capture.log"
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
        self.log.debug("alertsCapture.initGetText(): Start")
        try:
            t = gettext.translation(cfggettextdomain, dirLocale, [cfgsystemlang], fallback=True)
            _ = t.ugettext
            t.install()
            self.log.info("alertsCapture.initGetText(): " + _(
                "Initialized gettext with Domain: %(cfggettextdomain)s - Language: %(cfgsystemlang)s - Path: %(dirLocale)s")
                          % {'cfggettextdomain': cfggettextdomain, 'cfgsystemlang': cfgsystemlang,
                             'dirLocale': dirLocale})
        except:
            self.log.error("No translation file available")

    def run(self):
        """ Initiate daily reports creation for all sources """
        self.log.info("alertsCapture.run(): " + _("Initiate alerts capture"))

        currentAlerts = {}
        if self.sourceId != None:
            sourceAlerts = [self.sourceId]
        else:
            sourceAlerts = self.sourcesUtils.getActiveSourcesIds()

        for currentSource in sourceAlerts:
            self.log.info("alertsCapture.run(): " + _("Processing source: %(currentSource)s") % {'currentSource': str(currentSource)})
            configSource = Config(self.log, self.dirEtc + 'config-source' + str(currentSource) + '.cfg')
            cfgemailschedulealert = configSource.getConfig('cfgemailschedulealert')

            if cfgemailschedulealert == "yes":
                sourceSchedule = self.getSourceSchedule(currentSource)
                if sourceSchedule != {}:
                    self.log.info("alertsCapture.run(): " + _("The Alert Schedule is available for the source"))
                    cfgemailalertfailure = configSource.getConfig('cfgemailalertfailure')
                    cfgemailalertreminder = configSource.getConfig('cfgemailalertreminder')
                    self.log.info("alertsCapture.run(): " + _("Send an email after %(cfgemailalertfailure)s capture failures") % {'cfgemailalertfailure': str(cfgemailalertfailure)})
                    self.log.info("alertsCapture.run(): " + _("Send a reminder every %(cfgemailalertreminder)s capture failures") % {'cfgemailalertreminder': str(cfgemailalertreminder)})

                    latestPicture = self.sourcesUtils.getLatestPicture(currentSource)
                    self.log.info("alertsCapture.run(): " + _("Last picture: %(latestPicture)s") % {'latestPicture': str(latestPicture)})

                    currentSourceTime = self.timeUtils.getCurrentSourceTime(configSource)
                    lastCaptureTime = self.timeUtils.getTimeFromFilename(latestPicture, configSource)

                    self.log.info("alertsCapture.run(): " + _("Current Source Time: %(currentSourceTime)s") % {'currentSourceTime': str(currentSourceTime.isoformat())})
                    self.log.info("alertsCapture.run(): " + _("Last Capture Time: %(lastCaptureTime)s") % {'lastCaptureTime': str(lastCaptureTime.isoformat())})

                    secondsDiff = int((currentSourceTime-lastCaptureTime).total_seconds())
                    self.log.info("alertsCapture.run(): " + _("Seconds since last capture: %(secondsDiff)s") % {'secondsDiff': str(secondsDiff)})

                    missedCapture = self.getCountMissedSlots(currentSourceTime, lastCaptureTime, sourceSchedule)
                    self.log.info("alertsCapture.run(): " + _("Total Missed Captures: %(missedCapture)s") % {'missedCapture': missedCapture})

                    nextCaptureTime = self.getNextCaptureSlot(currentSourceTime, sourceSchedule, configSource)
                    self.log.info("alertsCapture.run(): " + _("Next Planned Capture Time: %(nextCaptureTime)s") % {'nextCaptureTime': str(nextCaptureTime.isoformat())})

                    incidentFile = None
                    if missedCapture == 0:
                        alertStatus = "GOOD"
                    elif missedCapture > 0 and int(cfgemailalertfailure) > missedCapture:
                        alertStatus = "LATE"
                    elif missedCapture >= int(cfgemailalertfailure):
                        alertStatus = "ERROR"
                        incidentFile = latestPicture[0:14] + ".jsonl"
                    self.log.info("alertsCapture.run(): " + _("Current Alert Status: %(alertStatus)s") % {'alertStatus': str(alertStatus)})

                    alertsFile = self.dirSources + "source" + str(currentSource) + "/resources/alerts/" + latestPicture[0:8] + ".jsonl";
                    self.log.info("alertsCapture.run(): " + _("Saving to Alerts file: %(alertsFile)s") % {'alertsFile': str(alertsFile)})

                    alertObject = alertObj(self.log, alertsFile)
                    alertObject.setAlertValue("sourceid", currentSource)
                    alertObject.setAlertValue("currentSourceTime", currentSourceTime.isoformat())
                    alertObject.setAlertValue("lastCaptureTime", lastCaptureTime.isoformat())
                    alertObject.setAlertValue("nextCaptureTime", nextCaptureTime.isoformat())
                    alertObject.setAlertValue("secondsSinceLastCapture", secondsDiff)
                    alertObject.setAlertValue("missedCapture", missedCapture)
                    alertObject.setAlertValue("status", alertStatus)
                    alertObject.setAlertValue("incidentFile", incidentFile)
                    alertObject.archiveAlertFile()

                    currentAlerts[currentSource] = alertObject.getAlert()

                else:
                    self.log.info("alertsCapture.run(): " + _("Alert Schedule is empty for the source"))
            else:
                self.log.info("alertsCapture.run(): " + _("Schedule based email alerts disabled for the source"))

            self.log.info("alertsCapture.run(): " + _("---------"))

        self.processUserAlerts(currentAlerts)

    def processUserAlerts(self, currentAlerts):
        """ Analyze current errors and process """
        self.log.debug("alertsCapture.processUserAlerts(): " + _("Start"))
        for currentUser in self.dbUtils.getUserWithSourceAlerts():
            self.log.info("alertsCapture.processUserAlerts(): " + _("Processing user %(name)s - email: %(email)s") % {'name': currentUser['name'], 'email': currentUser['email']})


    def getNextCaptureSlot(self, currentSourceTime, sourceSchedule, configSource):
        """ Calculates the next expected capture slot based on calendar """
        self.log.debug("alertsCapture.getNextCaptureSlot(): " + _("Start"))

        sourceTimeDayOfWeek = currentSourceTime.strftime("%w")
        if sourceTimeDayOfWeek == 0: # Sunday is 7, not 0
            sourceTimeDayOfWeek = 7
        sourceTimeHour = currentSourceTime.strftime("%H")
        sourceTimeMinute = currentSourceTime.strftime("%M")
        sourceTimeWeek = currentSourceTime.strftime("%W")
        sourceTimeYear = currentSourceTime.strftime("%Y")
        sourceTargetWeek = sourceTimeWeek
        sourceTime = int(str(sourceTimeDayOfWeek) + str(sourceTimeHour) + str(sourceTimeMinute))

        nextScanTime = None
        for scanTime in sorted(sourceSchedule):
            if sourceSchedule[scanTime] == "Y":
                self.log.debug("alertsCapture.getNextCaptureSlot(): " + _("Scanning Day: %(scanDay)s Hour: %(scanHour)s minute: %(scanMinute)s - Status: %(slotActive)s") % {'scanDay': str(scanTime)[0], 'scanHour': str(scanTime)[1:3], 'scanMinute': str(scanTime)[3:6], 'slotActive': sourceSchedule[scanTime]})
                if scanTime >= sourceTime:
                    nextScanTime = scanTime
                    break
        if nextScanTime == None:
            sourceTargetWeek = sourceTimeWeek + 1
            for scanTime in sorted(sourceSchedule):
                if sourceSchedule[scanTime] == "Y":
                    self.log.debug("alertsCapture.getNextCaptureSlot(): " + _("Scanning Day: %(scanDay)s Hour: %(scanHour)s minute: %(scanMinute)s - Status: %(slotActive)s") % {'scanDay': str(scanTime)[0], 'scanHour': str(scanTime)[1:3], 'scanMinute': str(scanTime)[3:6], 'slotActive': sourceSchedule[scanTime]})
                    nextScanTime = scanTime
                    break

        self.log.info("alertsCapture.getNextCaptureSlot(): " + _("Next Capture slot: %(nextScanTime)s") % {'nextScanTime': nextScanTime})

        # Build next capture date
        targetDayOfWeek = int(str(scanTime)[0])
        if (targetDayOfWeek == 7):
            sourceTargetWeek = sourceTargetWeek + 1
            targetDayOfWeek = 0
        if sourceTargetWeek == 53:
            sourceTimeYear = sourceTimeYear + 1
            sourceTargetWeek = 0

        nextCaptureTime = datetime.strptime(str(sourceTimeYear) + "-" + str(sourceTargetWeek) + "-" + str(targetDayOfWeek) + "-" + str(nextScanTime)[1:3] + "-" + str(nextScanTime)[3:6], "%Y-%W-%w-%H-%M")

        if configSource.getConfig('cfgcapturetimezone') != "":  # Update the timezone from UTC to the source's timezone
            self.log.info("alertsCapture.getNextCaptureSlot(): " + _("Source timezone is: %(sourceTimezone)s") % {'sourceTimezone': configSource.getConfig('cfgcapturetimezone')})
            sourceTimezone = tz.gettz(configSource.getConfig('cfgcapturetimezone'))
            nextCaptureTime = nextCaptureTime.replace(tzinfo=sourceTimezone)

        return nextCaptureTime


    def getCountMissedSlots(self, currentSourceTime, lastCaptureTime, sourceSchedule):
        """ Calculate the number of missed slots between last captured picture and current date using capture schedule """
        self.log.debug("alertsCapture.getCountMissedSlots(): " + _("Start"))

        sourceTimeDayOfWeek = currentSourceTime.strftime("%w")
        if sourceTimeDayOfWeek == 0: # Sunday is 7, not 0
            sourceTimeDayOfWeek = 7
        sourceTimeHour = currentSourceTime.strftime("%H")
        sourceTimeMinute = currentSourceTime.strftime("%M")
        sourceTimeWeek = currentSourceTime.strftime("%W")
        sourceTimeYear = currentSourceTime.strftime("%Y")
        sourceTime = int(str(sourceTimeDayOfWeek) + str(sourceTimeHour) + str(sourceTimeMinute))

        captureTimeDayOfWeek = lastCaptureTime.strftime("%w")
        if captureTimeDayOfWeek == 0: # Sunday is 7, not 0
            captureTimeDayOfWeek = 7
        captureTimeHour = lastCaptureTime.strftime("%H")
        captureTimeMinute = lastCaptureTime.strftime("%M")
        captureTimeWeek = lastCaptureTime.strftime("%W")
        captureTimeYear = lastCaptureTime.strftime("%Y")
        captureTime = int(str(captureTimeDayOfWeek) + str(captureTimeHour) + str(captureTimeMinute))

        missedCaptureRoundOne = 0
        missedCaptureRoundTwo = 0
        missedPicturesInDiffWeek = 0
        fullWeekCaptures = len(sourceSchedule)
        self.log.info("alertsCapture.getCountMissedSlots(): " + _("Analyzing source schedule"))
        self.log.info("alertsCapture.getCountMissedSlots(): " + _("Source Time: %(sourceTime)s")% {'sourceTime': sourceTime})
        self.log.info("alertsCapture.getCountMissedSlots(): " + _("Capture Time: %(captureTime)s")% {'captureTime': captureTime})
        self.log.info("alertsCapture.getCountMissedSlots(): " + _("Number of captures in full week: %(fullWeekCaptures)s")% {'fullWeekCaptures': fullWeekCaptures})
        if (captureTimeWeek != sourceTimeWeek):
            diffWeek = ((int(sourceTimeYear)*52) + int(sourceTimeWeek)) - ((int(captureTimeYear)*52) + int(captureTimeWeek)) - 1
            self.log.info("alertsCapture.getCountMissedSlots(): " + _("Number of week difference: %(diffWeek)s")% {'diffWeek': diffWeek})
            missedPicturesInDiffWeek = diffWeek * fullWeekCaptures

        # Scan all capture times backward, and count number of slots until it get a match between capture slot and capture time, if no match it keeps going
        for scanTime in reversed(sorted(sourceSchedule)):
            if sourceSchedule[scanTime] == "Y":
                if scanTime == captureTime and sourceTimeWeek == captureTimeWeek:
                    break
                if scanTime <= sourceTime:
                    missedCaptureRoundOne += 1
                    self.log.debug("alertsCapture.getCountMissedSlots(): " + _("Scanning Day: %(scanDay)s Hour: %(scanHour)s minute: %(scanMinute)s - Status: %(slotActive)s") % {'scanDay': str(scanTime)[0], 'scanHour': str(scanTime)[1:3], 'scanMinute': str(scanTime)[3:6], 'slotActive': sourceSchedule[scanTime]})

        self.log.info("alertsCapture.getCountMissedSlots(): " + _("Number of missed captures in round 1: %(missedCaptureRoundOne)s")% {'missedCaptureRoundOne': missedCaptureRoundOne})

        if sourceTimeWeek != captureTimeWeek:
            # Scan all capture times backward, and count number of slots until it get a match between capture slot and capture time, if no match it keeps going
            for scanTime in reversed(sorted(sourceSchedule)):
                if sourceSchedule[scanTime] == "Y":
                    if scanTime == captureTime:
                        break
                    if scanTime >= captureTime:
                        missedCaptureRoundTwo += 1
                        self.log.debug("alertsCapture.getCountMissedSlots(): " + _("Scanning Day: %(scanDay)s Hour: %(scanHour)s minute: %(scanMinute)s - Status: %(slotActive)s") % {'scanDay': str(scanTime)[0], 'scanHour': str(scanTime)[1:3], 'scanMinute': str(scanTime)[3:6], 'slotActive': sourceSchedule[scanTime]})

        self.log.info("alertsCapture.getCountMissedSlots(): " + _("Number of missed captures in round 2: %(missedCaptureRoundTwo)s")% {'missedCaptureRoundTwo': missedCaptureRoundTwo})

        missedCapture = missedCaptureRoundOne + missedCaptureRoundTwo + missedPicturesInDiffWeek


        """
        for scanDay in reversed(sorted(sourceSchedule)):
            for scanHour in reversed(sorted(sourceSchedule[scanDay])):
                for scanMinute in reversed(sorted(sourceSchedule[scanDay][scanHour])):
                    if sourceSchedule[scanDay][scanHour][scanMinute] == "Y":
                        if sourceTimeDayOfWeek == scanDay and scanHour == sourceTimeHour and scanMinute <= sourceTimeMinute:
                            missedCapture += 1

                        self.log.info("alertsCapture.getCountMissedSlots(): " + _("Scanning Day: %(scanDay)s Hour: %(scanHour)s minute: %(scanMinute)s - Status: %(slotActive)s") % {'scanDay': scanDay, 'scanHour': scanHour, 'scanMinute': scanMinute, 'slotActive': sourceSchedule[scanDay][scanHour][scanMinute]})
        """
        return missedCapture

    def getSourceSchedule(self, sourceId):
        """ Verify if schedule exists for the source """
        self.log.debug("alertsCapture.checkScheduleActive(): " + _("Start"))
        sourceScheduleFile = self.dirEtc + 'config-source' + str(sourceId) + '-schedule.json'
        if os.path.isfile(sourceScheduleFile):
            try:
                with open(sourceScheduleFile) as sourceSchedule:
                    sourceScheduleObj = json.load(sourceSchedule)
                    sourceScheduleNum = self.convertScheduleToFlat(sourceScheduleObj)
                    return sourceScheduleNum
            except Exception:
                self.log.error("alertsCapture.getSourceSchedule(): " + _("File appears corrupted: %(sourceScheduleFile)s ") % {'sourceScheduleFile': sourceScheduleFile})
        else:
            return {}

    def convertScheduleToNumericalIndex(self, sourceSchedule):
        self.log.debug("alertsCapture.convertScheduleToNumericalIndex(): " + _("Start"))
        self.log.info("alertsCapture.convertScheduleToNumericalIndex(): " + _("Converting object to numerical index"))
        sourceScheduleNum = {}
        for scanDay in sourceSchedule:
            scanDayNum = int(scanDay)
            sourceScheduleNum[scanDayNum] = {};
            for scanHour in sourceSchedule[scanDay]:
                scanHourNum = int(scanHour)
                sourceScheduleNum[scanDayNum][scanHourNum] = {};
                for scanMinute in sourceSchedule[scanDay][scanHour]:
                    scanMinuteNum = int(scanMinute)
                    sourceScheduleNum[scanDayNum][scanHourNum][scanMinuteNum] = sourceSchedule[scanDay][scanHour][scanMinute]
        return sourceScheduleNum

    # As a tentative to simplify the core, return the schedule as a flat array
    def convertScheduleToFlat(self, sourceSchedule):
        self.log.debug("alertsCapture.convertScheduleToNumericalIndex(): " + _("Start"))
        self.log.info("alertsCapture.convertScheduleToNumericalIndex(): " + _("Converting object to flat array"))
        sourceScheduleFlat = {}
        for scanDay in sourceSchedule:
            scanDayNum = int(scanDay)
            for scanHour in sourceSchedule[scanDay]:
                scanHourNum = int(scanHour)
                if scanHourNum < 10:
                    scanHourTxt = "0" + str(scanHourNum)
                else:
                    scanHourTxt = str(scanHourNum)
                for scanMinute in sourceSchedule[scanDay][scanHour]:
                    scanMinuteNum = int(scanMinute)
                    if scanMinuteNum < 10:
                        scanMinuteTxt = "0" + str(scanMinuteNum)
                    else:
                        scanMinuteTxt = str(scanMinuteNum)
                    fullKey = int(str(scanDayNum) + scanHourTxt + scanMinuteTxt)
                    sourceScheduleFlat[fullKey] = sourceSchedule[scanDay][scanHour][scanMinute]
        return sourceScheduleFlat