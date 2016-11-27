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
import dateutil.parser
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
            self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Processing source: %(currentSource)s") % {'currentSource': str(currentSource)})
            configSource = Config(self.log, self.dirEtc + 'config-source' + str(currentSource) + '.cfg')
            if configSource.getConfig('cfgemailerroractivate') == "yes" and (configSource.getConfig('cfgemailalerttime') == "yes" or configSource.getConfig('cfgemailalertscheduleslot') == "yes"  or configSource.getConfig('cfgemailalertscheduledelay') == "yes"):
                self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Email alerts are enabled for this source") % {'currentSource': str(currentSource)})

                currentTime = self.timeUtils.getCurrentSourceTime(configSource)
                latestPicture = self.sourcesUtils.getLatestPicture(currentSource)
                lastCaptureTime = self.timeUtils.getTimeFromFilename(latestPicture, configSource)
                secondsDiff = int((currentTime-lastCaptureTime).total_seconds())

                self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Last picture: %(latestPicture)s") % {'currentSource': str(currentSource), 'latestPicture': str(latestPicture)})
                self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Current Source Time: %(currentTime)s") % {'currentSource': str(currentSource), 'currentTime': str(currentTime.isoformat())})
                self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Last Capture Time: %(lastCaptureTime)s") % {'currentSource': str(currentSource), 'lastCaptureTime': str(lastCaptureTime.isoformat())})
                self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Seconds since last capture: %(secondsDiff)s") % {'currentSource': str(currentSource), 'secondsDiff': str(secondsDiff)})

                alertsFile = self.dirSources + "source" + str(currentSource) + "/resources/alerts/" + currentTime.strftime("%Y%m%d") + ".jsonl";
                lastAlertFile = self.dirSources + "source" + str(currentSource) + "/resources/alerts/last-alert.json";
                lastEmailFile = self.dirSources + "source" + str(currentSource) + "/resources/alerts/last-email.json";
                self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Alerts Log file: %(alertsFile)s") % {'currentSource': str(currentSource), 'alertsFile': alertsFile})
                self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Last Alert file: %(alertsFile)s") % {'currentSource': str(currentSource), 'alertsFile': lastAlertFile})
                self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Last Email file: %(alertsFile)s") % {'currentSource': str(currentSource), 'alertsFile': lastEmailFile})

                lastAlert = alertObj(self.log, lastAlertFile)
                lastAlert.loadAlertFile()

                lastEmail = alertObj(self.log, lastEmailFile)
                lastEmail.loadAlertFile()

                if lastEmail.getAlert() != {}:
                    lastEmailTime = dateutil.parser.parse(lastEmail.getAlertValue("currentTime"))
                    secondsSinceLastEmail = int((currentTime-lastEmailTime).total_seconds())
                    self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Seconds since last email: %(secondsSinceLastEmail)s") % {'currentSource': str(currentSource), 'secondsSinceLastEmail': str(secondsSinceLastEmail)})
                else:
                    secondsSinceLastEmail = None

                if configSource.getConfig('cfgemailalerttime') == "yes":
                    self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Time based alert enabled") % {'currentSource': str(currentSource)})
                    self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Time based: cfgemailalerttime: %(cfgemailalerttime)s") % {'currentSource': str(currentSource), 'cfgemailalerttime': str(configSource.getConfig('cfgemailalerttime'))})
                    self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Time based: cfgemailalerttimefailure: %(cfgemailalerttimefailure)s") % {'currentSource': str(currentSource), 'cfgemailalerttimefailure': str(configSource.getConfig('cfgemailalerttimefailure'))})
                    self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Time based: cfgemailalerttimereminder: %(cfgemailalerttimereminder)s") % {'currentSource': str(currentSource), 'cfgemailalerttimereminder': str(configSource.getConfig('cfgemailalerttimereminder'))})

                    # Determine if source id in an error state
                    minutesDiff = int(secondsDiff / 60)
                    self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Time based: Minutes since last capture: %(minutesDiff)s") % {'currentSource': str(currentSource), 'minutesDiff': str(minutesDiff)})
                    if minutesDiff >= int(configSource.getConfig('cfgemailalerttimefailure')):
                        alertStatus = "ERROR"
                    else:
                        alertStatus = "GOOD"
                    self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Time based alert Status: %(alertStatus)s") % {'currentSource': str(currentSource), 'alertStatus': alertStatus})

                if configSource.getConfig('cfgemailalertscheduleslot') == "yes" or configSource.getConfig('cfgemailalertscheduledelay') == "yes":

                    sourceSchedule = self.getSourceSchedule(currentSource)
                    if sourceSchedule != {}:
                        self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - An alert schedule is available for the source") % {'currentSource': str(currentSource)})

                        missedCapture = self.getCountMissedSlots(currentTime, lastCaptureTime, sourceSchedule)
                        nextCaptureTime = self.getNextCaptureSlot(currentTime, sourceSchedule, configSource)

                        self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Total Missed Captures: %(missedCapture)s") % {'currentSource': str(currentSource), 'missedCapture': missedCapture})
                        self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Next Planned Capture Time: %(nextCaptureTime)s") % {'currentSource': str(currentSource), 'nextCaptureTime': str(nextCaptureTime.isoformat())})

                        if configSource.getConfig('cfgemailalertscheduleslot') == "yes":
                            self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Schedule slot based alert enabled") % {'currentSource': str(currentSource)})
                            self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Schedule slot based: cfgemailalertscheduleslot: %(cfgemailalertscheduleslot)s") % {'currentSource': str(currentSource), 'cfgemailalertscheduleslot': str(configSource.getConfig('cfgemailalertscheduleslot'))})
                            self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Schedule slot based: cfgemailalertscheduleslotfailure: %(cfgemailalertscheduleslotfailure)s") % {'currentSource': str(currentSource), 'cfgemailalertscheduleslotfailure': str(configSource.getConfig('cfgemailalertscheduleslotfailure'))})
                            self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Schedule slot based: cfgemailalertscheduleslotreminder: %(cfgemailalertscheduleslotreminder)s") % {'currentSource': str(currentSource), 'cfgemailalertscheduleslotreminder': str(configSource.getConfig('cfgemailalertscheduleslotreminder'))})

                            cfgemailalertscheduleslotfailure = int(configSource.getConfig('cfgemailalertscheduleslotfailure'))
                            if missedCapture == 0:
                                alertStatus = "GOOD"
                            elif missedCapture > 0 and int(cfgemailalertscheduleslotfailure) > missedCapture:
                                alertStatus = "LATE"
                            elif missedCapture >= int(cfgemailalertscheduleslotfailure):
                                alertStatus = "ERROR"
                            self.log.info("alertsCapture.run(): " + _("Source: %(currentSource)s - Schedule slot Alert Status: %(alertStatus)s") % {'currentSource': str(currentSource), 'alertStatus': str(alertStatus)})


                        cfgemailschedulealert = configSource.getConfig('cfgemailschedulealert')
                        cfgemailalertfailure = configSource.getConfig('cfgemailalertfailure')
                        cfgemailalertreminder = configSource.getConfig('cfgemailalertreminder')
                        self.log.info("alertsCapture.run(): " + _("Send an email after %(cfgemailalertfailure)s capture failures") % {'cfgemailalertfailure': str(cfgemailalertfailure)})
                        self.log.info("alertsCapture.run(): " + _("Send a reminder every %(cfgemailalertreminder)s capture failures") % {'cfgemailalertreminder': str(cfgemailalertreminder)})


                        if missedCapture == 0:
                            alertStatus = "GOOD"
                        elif missedCapture > 0 and int(cfgemailalertfailure) > missedCapture:
                            alertStatus = "LATE"
                        elif missedCapture >= int(cfgemailalertfailure):
                            alertStatus = "ERROR"
                        self.log.info("alertsCapture.run(): " + _("Current Alert Status: %(alertStatus)s") % {'alertStatus': str(alertStatus)})

                        currentAlert = alertObj(self.log, alertsFile)
                        currentAlert.setAlertValue("sourceid", currentSource)
                        currentAlert.setAlertValue("currentTime", currentTime.isoformat())
                        currentAlert.setAlertValue("lastCaptureTime", lastCaptureTime.isoformat())
                        currentAlert.setAlertValue("nextCaptureTime", nextCaptureTime.isoformat())
                        currentAlert.setAlertValue("missedCapture", missedCapture)
                        currentAlert.setAlertValue("secondsSinceLastCapture", secondsDiff)
                        currentAlert.setAlertValue("secondsSinceLastEmail", None)
                        currentAlert.setAlertValue("missedCapturesSinceLastEmail", None)
                        currentAlert.setAlertValue("status", alertStatus)

                        # This section is used to determine if an alert or a reminder should be sent
                        # Is the source currently considered to be failing to capture pictures based on configured threshold
                        if int(missedCapture) >= int(cfgemailalertfailure) and int(cfgemailalertfailure) != 0:
                            self.log.info("alertsCapture.run(): " + _("Missed captures above configured threshold: %(missedCapture)s/%(cfgemailalertfailure)s") % {'missedCapture': str(missedCapture), 'cfgemailalertfailure': str(cfgemailalertfailure)})
                            if lastEmail.getAlert() == {}:
                                # There was no email sent before for this particular source, sending a new email
                                self.log.info("alertsCapture.run(): " + _("There was not email sent previously, requesting a new email to be sent"))
                                currentAlert.setAlertValue("email", True)
                                currentAlert.setAlertValue("emailType", "NEW")
                                currentAlert.setAlertValue("missedCapturesSinceLastEmail", 0)
                                currentAlert.setAlertValue("secondsSinceLastEmail", 0)
                            elif lastEmail.getAlertValue("lastCaptureTime") != lastCaptureTime.isoformat():
                                # The last email sent was for a different picture
                                self.log.info("alertsCapture.run(): " + _("Last captured pictures in last sent email is different, requesting a new email to be sent"))
                                currentAlert.setAlertValue("email", True)
                                currentAlert.setAlertValue("emailType", "NEW")
                                currentAlert.setAlertValue("missedCapturesSinceLastEmail", 0)
                                currentAlert.setAlertValue("secondsSinceLastEmail", 0)
                            else:
                                # There was an email sent before for the source, analyzing previous email to determine action
                                lastEmailMissedCaptures = lastEmail.getAlertValue("missedCapture")
                                self.log.info("alertsCapture.run(): " + _("Last Email Missed Captures: %(lastEmailMissedCaptures)s") % {'lastEmailMissedCaptures': str(lastEmailMissedCaptures)})

                                missedCaptureSinceLastEmail = missedCapture - lastEmailMissedCaptures
                                currentAlert.setAlertValue("missedCapturesSinceLastEmail", missedCaptureSinceLastEmail)
                                self.log.info("alertsCapture.run(): " + _("Missed Capture since last email: %(missedCaptureSinceLastEmail)s") % {'missedCaptureSinceLastEmail': str(missedCaptureSinceLastEmail)})


                                if missedCaptureSinceLastEmail >= int(cfgemailalertreminder):
                                    # Number of failed captures since last email is above threshold, sending a reminder email
                                    self.log.info("alertsCapture.run(): " + _("Missed captures above configured threshold: %(missedCaptureSinceLastEmail)s/%(cfgemailalertreminder)s") % {'missedCaptureSinceLastEmail': str(missedCaptureSinceLastEmail), 'cfgemailalertreminder': str(cfgemailalertreminder)})
                                    self.log.info("alertsCapture.run(): " + _("Requesting a reminder to be email to be sent"))
                                    currentAlert.setAlertValue("email", True)
                                    currentAlert.setAlertValue("emailType", "REMINDER")
                                    currentAlert.setAlertValue("missedCapturesSinceLastEmail", 0)
                                    currentAlert.setAlertValue("secondsSinceLastEmail", 0)
                                else:
                                    # Number of failed captures is not sufficient to trigger email to be sent, but numbers are recorded
                                    self.log.info("alertsCapture.run(): " + _("Missed captures below configured threshold: %(missedCaptureSinceLastEmail)s/%(cfgemailalertreminder)s") % {'missedCaptureSinceLastEmail': str(missedCaptureSinceLastEmail), 'cfgemailalertreminder': str(cfgemailalertreminder)})
                                    self.log.info("alertsCapture.run(): " + _("There has not been sufficient failure since last email, no email will be sent"))
                                    currentAlert.setAlertValue("email", False)
                                    currentAlert.setAlertValue("missedCapturesSinceLastEmail", missedCaptureSinceLastEmail)
                                    currentAlert.setAlertValue("secondsSinceLastEmail", secondsSinceLastEmail)

                        if currentAlert.getAlertValue("email") == True:
                            currentAlert.writeAlertFile(lastEmailFile)

                        currentAlert.archiveAlertFile()
                        currentAlert.writeAlertFile(lastAlertFile)

                        currentAlerts[currentSource] = currentAlert.getAlert()
                    else:
                        self.log.info("alertsCapture.run(): " + _("Alert Schedule is empty for the source"))
            else:
                self.log.info("alertsCapture.run(): " + _("Schedule based email alerts disabled for the source"))

            self.log.info("alertsCapture.run(): " + _("---------"))

        #self.processUserAlerts(currentAlerts)

    def processUserAlerts(self, currentAlerts):
        """ Analyze current errors and process """
        self.log.debug("alertsCapture.processUserAlerts(): " + _("Start"))
        for currentAlert in currentAlerts:
            curAlert = currentAlerts[currentAlert]
            self.log.info("alertsCapture.processUserAlerts(): " + _("Processing Alert for source %(currentSource)s") % {'currentSource': curAlert["sourceid"]})
            curUsers = self.dbUtils.getUsersAlertsForSource(curAlert["sourceid"])
            incidentsFile = self.dirSources + "source" + str(curAlert["sourceid"]) + "/resources/alerts/incidents/" + curAlert["incidentFile"];
            self.log.info("alertsCapture.run(): " + _("Saving to Alerts file: %(incidentsFile)s") % {'incidentsFile': incidentsFile})

    def getNextCaptureSlot(self, currentTime, sourceSchedule, configSource):
        """ Calculates the next expected capture slot based on calendar """
        self.log.debug("alertsCapture.getNextCaptureSlot(): " + _("Start"))

        sourceTimeDayOfWeek = currentTime.strftime("%w")
        if sourceTimeDayOfWeek == 0: # Sunday is 7, not 0
            sourceTimeDayOfWeek = 7
        sourceTimeHour = currentTime.strftime("%H")
        sourceTimeMinute = currentTime.strftime("%M")
        sourceTimeWeek = currentTime.strftime("%W")
        sourceTimeYear = currentTime.strftime("%Y")
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
            sourceTargetWeek = int(sourceTargetWeek) + 1
            targetDayOfWeek = 0
        if sourceTargetWeek == 53:
            sourceTimeYear = int(sourceTimeYear) + 1
            sourceTargetWeek = 0

        nextCaptureTime = datetime.strptime(str(sourceTimeYear) + "-" + str(sourceTargetWeek) + "-" + str(targetDayOfWeek) + "-" + str(nextScanTime)[1:3] + "-" + str(nextScanTime)[3:6], "%Y-%W-%w-%H-%M")

        if configSource.getConfig('cfgcapturetimezone') != "":  # Update the timezone from UTC to the source's timezone
            self.log.info("alertsCapture.getNextCaptureSlot(): " + _("Source timezone is: %(sourceTimezone)s") % {'sourceTimezone': configSource.getConfig('cfgcapturetimezone')})
            sourceTimezone = tz.gettz(configSource.getConfig('cfgcapturetimezone'))
            nextCaptureTime = nextCaptureTime.replace(tzinfo=sourceTimezone)

        return nextCaptureTime


    def getCountMissedSlots(self, currentTime, lastCaptureTime, sourceSchedule):
        """ Calculate the number of missed slots between last captured picture and current date using capture schedule """
        self.log.debug("alertsCapture.getCountMissedSlots(): " + _("Start"))

        sourceTimeDayOfWeek = currentTime.strftime("%w")
        if sourceTimeDayOfWeek == 0: # Sunday is 7, not 0
            sourceTimeDayOfWeek = 7
        sourceTimeHour = currentTime.strftime("%H")
        sourceTimeMinute = currentTime.strftime("%M")
        sourceTimeWeek = currentTime.strftime("%W")
        sourceTimeYear = currentTime.strftime("%Y")
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