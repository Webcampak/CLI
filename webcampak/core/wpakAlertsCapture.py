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

from __future__ import absolute_import
from __future__ import division
from builtins import str
from builtins import object
from past.utils import old_div
import os
import time
import json
from datetime import tzinfo, timedelta, datetime
import pytz
from dateutil import tz
import dateutil.parser
from tabulate import tabulate
import socket

from .wpakConfigObj import Config
from .wpakConfigCache import configCache
from .wpakTimeUtils import timeUtils
from .wpakSourcesUtils import sourcesUtils
from .wpakFileUtils import fileUtils
from .wpakDbUtils import dbUtils
from .objects.wpakEmail import Email
from .wpakAlertsObj import alertObj
from .wpakAlertsEmails import alertsEmails


class alertsCapture(object):
    """This class is used to verify if pictures are properly captured and not running late

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

        self.configPaths = Config(self.log, self.config_dir + "param_paths.yml")
        self.dirEtc = self.configPaths.getConfig("parameters")["dir_etc"]
        self.dirConfig = self.configPaths.getConfig("parameters")["dir_config"]
        self.dirBin = self.configPaths.getConfig("parameters")["dir_bin"]
        self.dirSources = self.configPaths.getConfig("parameters")["dir_sources"]
        self.dirSourceLive = self.configPaths.getConfig("parameters")["dir_source_live"]
        self.dirSourceCapture = self.configPaths.getConfig("parameters")[
            "dir_source_capture"
        ]
        self.dirLocale = self.configPaths.getConfig("parameters")["dir_locale"]
        self.dirLocaleMessage = self.configPaths.getConfig("parameters")[
            "dir_locale_message"
        ]
        self.dirLocaleEmails = self.configPaths.getConfig("parameters")[
            "dir_locale_emails"
        ]
        self.dirStats = self.configPaths.getConfig("parameters")["dir_stats"]
        self.dirCache = self.configPaths.getConfig("parameters")["dir_cache"]
        self.dirEmails = self.configPaths.getConfig("parameters")["dir_emails"]
        self.dirResources = self.configPaths.getConfig("parameters")["dir_resources"]
        self.dirLogs = self.configPaths.getConfig("parameters")["dir_logs"]
        self.dirXferQueue = (
            self.configPaths.getConfig("parameters")["dir_xfer"] + "queued/"
        )

        self.setupLog()

        self.configGeneral = Config(self.log, self.dirConfig + "config-general.cfg")
        self.timeUtils = timeUtils(self)
        self.sourcesUtils = sourcesUtils(self)
        self.dbUtils = dbUtils(self)
        self.configCache = configCache(self)
        self.fileUtils = fileUtils(self)
        self.alertsEmails = alertsEmails(self)

    def setupLog(self):
        """Setup logging to file"""
        reportsLogs = self.dirLogs + "alerts/"
        if not os.path.exists(reportsLogs):
            os.makedirs(reportsLogs)
        logFilename = reportsLogs + "alert.log"
        self.appConfig.set(self.log._meta.config_section, "file", logFilename)
        self.appConfig.set(self.log._meta.config_section, "rotate", True)
        self.appConfig.set(self.log._meta.config_section, "max_bytes", 512000)
        self.appConfig.set(self.log._meta.config_section, "max_files", 10)
        self.log._setup_file_log()

    def run(self):
        """Initiate daily reports creation for all sources"""
        self.log.info("alertsCapture.run(): Initiate alerts capture")

        if self.sourceId != None:
            sourceAlerts = [self.sourceId]
        else:
            sourceAlerts = self.sourcesUtils.getActiveSourcesIds()

        for currentSource in sourceAlerts:
            self.log.info(
                "alertsCapture.run(): Source: %(currentSource)s - Processing source: %(currentSource)s"
                % {"currentSource": str(currentSource)}
            )
            configSource = self.configCache.loadSourceConfig(
                "source",
                self.dirEtc + "config-source" + str(currentSource) + ".cfg",
                currentSource,
            )
            if configSource.getConfig("cfgemailerroractivate") == "yes" and (
                configSource.getConfig("cfgemailalerttime") == "yes"
                or configSource.getConfig("cfgemailalertscheduleslot") == "yes"
            ):
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Email alerts are enabled for this source"
                    % {"currentSource": str(currentSource)}
                )

                currentTime = self.timeUtils.getCurrentSourceTime(configSource)
                latestPicture = self.sourcesUtils.getLatestPicture(currentSource)
                lastCaptureTime = self.timeUtils.getTimeFromFilename(
                    latestPicture, configSource
                )
                secondsDiff = int((currentTime - lastCaptureTime).total_seconds())

                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Last picture: %(latestPicture)s"
                    % {
                        "currentSource": str(currentSource),
                        "latestPicture": str(latestPicture),
                    }
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Current Source Time: %(currentTime)s"
                    % {
                        "currentSource": str(currentSource),
                        "currentTime": str(currentTime.isoformat()),
                    }
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Last Capture Time: %(lastCaptureTime)s"
                    % {
                        "currentSource": str(currentSource),
                        "lastCaptureTime": str(lastCaptureTime.isoformat()),
                    }
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Seconds since last capture: %(secondsDiff)s"
                    % {
                        "currentSource": str(currentSource),
                        "secondsDiff": str(secondsDiff),
                    }
                )

                alertsFile = (
                    self.dirSources
                    + "source"
                    + str(currentSource)
                    + "/resources/alerts/"
                    + currentTime.strftime("%Y%m%d")
                    + ".jsonl"
                )
                lastAlertFile = (
                    self.dirSources
                    + "source"
                    + str(currentSource)
                    + "/resources/alerts/last-alert.json"
                )
                lastEmailFile = (
                    self.dirSources
                    + "source"
                    + str(currentSource)
                    + "/resources/alerts/last-email.json"
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Alerts Log file: %(alertsFile)s"
                    % {"currentSource": str(currentSource), "alertsFile": alertsFile}
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Last Alert file: %(alertsFile)s"
                    % {"currentSource": str(currentSource), "alertsFile": lastAlertFile}
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Last Email file: %(alertsFile)s"
                    % {"currentSource": str(currentSource), "alertsFile": lastEmailFile}
                )

                lastAlert = alertObj(self.log, lastAlertFile)
                lastAlert.loadAlertFile()

                lastEmail = alertObj(self.log, lastEmailFile)
                lastEmail.loadAlertFile()

                currentAlert = alertObj(self.log, alertsFile)
                currentAlert.setAlertValue("sourceid", currentSource)
                currentAlert.setAlertValue("currentTime", currentTime.isoformat())
                currentAlert.setAlertValue("lastPicture", latestPicture)
                currentAlert.setAlertValue(
                    "lastCaptureTime", lastCaptureTime.isoformat()
                )
                currentAlert.setAlertValue("nextCaptureTime", None)
                currentAlert.setAlertValue("missedCapture", None)
                currentAlert.setAlertValue("secondsSinceLastCapture", secondsDiff)
                currentAlert.setAlertValue("missedCapturesSinceLastEmail", None)
                currentAlert.setAlertValue("email", None)

                if lastEmail.getAlert() != {} and lastEmail.getAlertValue(
                    "lastCaptureTime"
                ) == currentAlert.getAlertValue("lastCaptureTime"):
                    lastEmailTime = dateutil.parser.parse(
                        lastEmail.getAlertValue("currentTime")
                    )
                    secondsSinceLastEmail = int(
                        (currentTime - lastEmailTime).total_seconds()
                    )
                    self.log.info(
                        "alertsCapture.run(): Source: %(currentSource)s - Seconds since last email: %(secondsSinceLastEmail)s"
                        % {
                            "currentSource": str(currentSource),
                            "secondsSinceLastEmail": str(secondsSinceLastEmail),
                        }
                    )
                else:
                    secondsSinceLastEmail = None
                currentAlert.setAlertValue(
                    "secondsSinceLastEmail", secondsSinceLastEmail
                )

                # Determine alert state based on time since last capture
                timeAlertStatus = None
                if configSource.getConfig("cfgemailalerttime") == "yes":
                    self.log.info(
                        "alertsCapture.run(): Source: %(currentSource)s - Time based alert enabled"
                        % {"currentSource": str(currentSource)}
                    )
                    self.log.info(
                        "alertsCapture.run(): Source: %(currentSource)s - Time based: cfgemailalerttime: %(cfgemailalerttime)s"
                        % {
                            "currentSource": str(currentSource),
                            "cfgemailalerttime": str(
                                configSource.getConfig("cfgemailalerttime")
                            ),
                        }
                    )
                    self.log.info(
                        "alertsCapture.run(): Source: %(currentSource)s - Time based: cfgemailalerttimefailure: %(cfgemailalerttimefailure)s"
                        % {
                            "currentSource": str(currentSource),
                            "cfgemailalerttimefailure": str(
                                configSource.getConfig("cfgemailalerttimefailure")
                            ),
                        }
                    )
                    self.log.info(
                        "alertsCapture.run(): Source: %(currentSource)s - Time based: cfgemailalerttimereminder: %(cfgemailalerttimereminder)s"
                        % {
                            "currentSource": str(currentSource),
                            "cfgemailalerttimereminder": str(
                                configSource.getConfig("cfgemailalerttimereminder")
                            ),
                        }
                    )

                    # Determine if source id in an error state
                    minutesDiff = int(old_div(secondsDiff, 60))
                    self.log.info(
                        "alertsCapture.run(): Source: %(currentSource)s - Time based: Minutes since last capture: %(minutesDiff)s"
                        % {
                            "currentSource": str(currentSource),
                            "minutesDiff": str(minutesDiff),
                        }
                    )
                    if minutesDiff >= int(
                        configSource.getConfig("cfgemailalerttimefailure")
                    ):
                        timeAlertStatus = "ERROR"
                        if secondsSinceLastEmail != None and secondsSinceLastEmail >= (
                            int(configSource.getConfig("cfgemailalerttimereminder"))
                            * 60
                        ):
                            self.log.info(
                                "alertsCapture.run(): Source: %(currentSource)s - Requesting to send a reminder email based on time since last email"
                                % {"currentSource": str(currentSource)}
                            )
                            currentAlert.setAlertValue("email", True)
                            currentAlert.setAlertValue("emailType", "REMINDER")
                    else:
                        timeAlertStatus = "GOOD"
                    self.log.info(
                        "alertsCapture.run(): Source: %(currentSource)s - Time based alert Status: %(timeAlertStatus)s"
                        % {
                            "currentSource": str(currentSource),
                            "timeAlertStatus": timeAlertStatus,
                        }
                    )

                # Determine alert state based on per-configured alert schedule
                scheduleAlertStatus = None
                if configSource.getConfig("cfgemailalertscheduleslot") == "yes":
                    sourceSchedule = self.getSourceSchedule(currentSource)
                    if sourceSchedule != {}:
                        self.log.info(
                            "alertsCapture.run(): Source: %(currentSource)s - An alert schedule is available for the source"
                            % {"currentSource": str(currentSource)}
                        )
                        self.log.info(
                            "alertsCapture.run(): Source: %(currentSource)s - Schedule slot based alert enabled"
                            % {"currentSource": str(currentSource)}
                        )
                        self.log.info(
                            "alertsCapture.run(): Source: %(currentSource)s - Schedule slot based: cfgemailalertscheduleslot: %(cfgemailalertscheduleslot)s"
                            % {
                                "currentSource": str(currentSource),
                                "cfgemailalertscheduleslot": str(
                                    configSource.getConfig("cfgemailalertscheduleslot")
                                ),
                            }
                        )
                        self.log.info(
                            "alertsCapture.run(): Source: %(currentSource)s - Schedule slot based: cfgemailalertscheduleslotfailure: %(cfgemailalertscheduleslotfailure)s"
                            % {
                                "currentSource": str(currentSource),
                                "cfgemailalertscheduleslotfailure": str(
                                    configSource.getConfig(
                                        "cfgemailalertscheduleslotfailure"
                                    )
                                ),
                            }
                        )
                        self.log.info(
                            "alertsCapture.run(): Source: %(currentSource)s - Schedule slot based: cfgemailalertscheduleslotreminder: %(cfgemailalertscheduleslotreminder)s"
                            % {
                                "currentSource": str(currentSource),
                                "cfgemailalertscheduleslotreminder": str(
                                    configSource.getConfig(
                                        "cfgemailalertscheduleslotreminder"
                                    )
                                ),
                            }
                        )

                        if (
                            configSource.getConfig("cfgemailalertscheduleslotgrace")
                            != ""
                            and int(
                                configSource.getConfig("cfgemailalertscheduleslotgrace")
                            )
                            > 0
                        ):
                            # Offset current date by the grace period, this offset is used to include the time taken by the picture to arrive into the source (for example if uploaded from a remote webcampak)
                            self.log.info(
                                "alertsCapture.run(): Source: %(currentSource)s - Grace Period: Substracting a grace period of %(gracePeriod)s minutes from current date"
                                % {
                                    "currentSource": str(currentSource),
                                    "gracePeriod": configSource.getConfig(
                                        "cfgemailalertscheduleslotgrace"
                                    ),
                                }
                            )
                            self.log.info(
                                "alertsCapture.run(): Source: %(currentSource)s - Grace Period: Orignial Time %(currentTime)s"
                                % {
                                    "currentSource": str(currentSource),
                                    "currentTime": currentTime.isoformat(),
                                }
                            )
                            currentTime = currentTime - timedelta(
                                minutes=int(
                                    configSource.getConfig(
                                        "cfgemailalertscheduleslotgrace"
                                    )
                                )
                            )
                            self.log.info(
                                "alertsCapture.run(): Source: %(currentSource)s - Grace Period: Updated Time %(currentTime)s"
                                % {
                                    "currentSource": str(currentSource),
                                    "currentTime": currentTime.isoformat(),
                                }
                            )
                            # If the latest picture has been captured after current time, look for an older picture as later captured pictures should be taken in consideration in subsequent script execution
                            if int(lastCaptureTime.strftime("%Y%m%d%H%M%S")) > int(
                                currentTime.strftime("%Y%m%d%H%M%S")
                            ):
                                self.log.info(
                                    "alertsCapture.run(): Source: %(currentSource)s - Latest picture captured after the updated time with grace period. Looking for an older picture"
                                    % {"currentSource": str(currentSource)}
                                )
                                latestPicture = self.sourcesUtils.getLatestPicture(
                                    currentSource, currentTime
                                )
                                lastCaptureTime = self.timeUtils.getTimeFromFilename(
                                    latestPicture, configSource
                                )

                        missedCapture = self.getCountMissedSlots(
                            currentTime, lastCaptureTime, sourceSchedule
                        )
                        nextCaptureTime = self.getNextCaptureSlot(
                            currentTime, sourceSchedule, configSource
                        )
                        currentAlert.setAlertValue("missedCapture", missedCapture)
                        currentAlert.setAlertValue(
                            "nextCaptureTime", nextCaptureTime.isoformat()
                        )

                        self.log.info(
                            "alertsCapture.run(): Source: %(currentSource)s - Total Missed Captures: %(missedCapture)s"
                            % {
                                "currentSource": str(currentSource),
                                "missedCapture": missedCapture,
                            }
                        )
                        self.log.info(
                            "alertsCapture.run(): Source: %(currentSource)s - Next Planned Capture Time: %(nextCaptureTime)s"
                            % {
                                "currentSource": str(currentSource),
                                "nextCaptureTime": str(nextCaptureTime.isoformat()),
                            }
                        )

                        cfgemailalertscheduleslotfailure = int(
                            configSource.getConfig("cfgemailalertscheduleslotfailure")
                        )
                        if missedCapture == 0:
                            scheduleAlertStatus = "GOOD"
                        elif (
                            missedCapture > 0
                            and int(cfgemailalertscheduleslotfailure) > missedCapture
                        ):
                            scheduleAlertStatus = "LATE"
                        elif missedCapture >= int(cfgemailalertscheduleslotfailure):
                            scheduleAlertStatus = "ERROR"
                        self.log.info(
                            "alertsCapture.run(): Source: %(currentSource)s - Schedule slot Alert Status: %(scheduleAlertStatus)s"
                            % {
                                "currentSource": str(currentSource),
                                "scheduleAlertStatus": str(scheduleAlertStatus),
                            }
                        )

                        # Calculate number of missed capture since last email
                        if (
                            lastEmail.getAlert() != {}
                            and scheduleAlertStatus != "GOOD"
                            and lastEmail.getAlertValue("lastCaptureTime")
                            == currentAlert.getAlertValue("lastCaptureTime")
                        ):
                            lastEmailMissedCaptures = lastEmail.getAlertValue(
                                "missedCapture"
                            )
                            self.log.info(
                                "alertsCapture.run(): Source: %(currentSource)s - Last Email Missed Captures: %(lastEmailMissedCaptures)s"
                                % {
                                    "currentSource": str(currentSource),
                                    "lastEmailMissedCaptures": str(
                                        lastEmailMissedCaptures
                                    ),
                                }
                            )

                            missedCaptureSinceLastEmail = (
                                missedCapture - lastEmailMissedCaptures
                            )
                            currentAlert.setAlertValue(
                                "missedCapturesSinceLastEmail",
                                missedCaptureSinceLastEmail,
                            )
                            self.log.info(
                                "alertsCapture.run(): Source: %(currentSource)s - Missed Capture since last email: %(missedCaptureSinceLastEmail)s"
                                % {
                                    "currentSource": str(currentSource),
                                    "missedCaptureSinceLastEmail": str(
                                        missedCaptureSinceLastEmail
                                    ),
                                }
                            )

                            if missedCaptureSinceLastEmail >= int(
                                configSource.getConfig(
                                    "cfgemailalertscheduleslotreminder"
                                )
                            ):
                                self.log.info(
                                    "alertsCapture.run(): Source: %(currentSource)s - Requesting to send a reminder email based on number of missed captures since last email"
                                    % {"currentSource": str(currentSource)}
                                )
                                currentAlert.setAlertValue("email", True)
                                currentAlert.setAlertValue("emailType", "REMINDER")

                    else:
                        self.log.info(
                            "alertsCapture.run(): Source: %(currentSource)s - Alert Schedule is empty for the source"
                            % {"currentSource": str(currentSource)}
                        )

                # Determine overall Alert Status
                if timeAlertStatus == "ERROR" or scheduleAlertStatus == "ERROR":
                    alertStatus = "ERROR"
                elif scheduleAlertStatus == "LATE":
                    alertStatus = "LATE"
                else:
                    alertStatus = "GOOD"

                if (
                    lastAlert.getAlertValue("status") == "ERROR"
                    and alertStatus == "GOOD"
                ):
                    alertStatus = "RECOVER"

                currentAlert.setAlertValue("status", alertStatus)
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Overeall alert status: %(alertStatus)s"
                    % {
                        "currentSource": str(currentSource),
                        "alertStatus": str(alertStatus),
                    }
                )

                lastAlertMissedCapture = lastAlert.getAlertValue("missedCapture")
                lastAlertMinutesDiff = lastAlert.getAlertValue("minutesDiff")
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Validator for email alerts: cfgemailalwaysnotify: %(cfgemailalwaysnotify)s"
                    % {
                        "currentSource": str(currentSource),
                        "cfgemailalwaysnotify": configSource.getConfig(
                            "cfgemailalwaysnotify"
                        ),
                    }
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Validator for email alerts: cfgemailalerttime: %(cfgemailalerttime)s"
                    % {
                        "currentSource": str(currentSource),
                        "cfgemailalerttime": configSource.getConfig(
                            "cfgemailalwaysnotify"
                        ),
                    }
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Validator for email alerts: lastAlertMinutesDiff: %(lastAlertMinutesDiff)s"
                    % {
                        "currentSource": str(currentSource),
                        "lastAlertMinutesDiff": str(lastAlertMinutesDiff),
                    }
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Validator for email alerts: cfgemailalerttimefailure: %(cfgemailalerttimefailure)s"
                    % {
                        "currentSource": str(currentSource),
                        "cfgemailalerttimefailure": configSource.getConfig(
                            "cfgemailalerttimefailure"
                        ),
                    }
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Validator for email alerts: cfgemailalertscheduleslot: %(cfgemailalertscheduleslot)s"
                    % {
                        "currentSource": str(currentSource),
                        "cfgemailalertscheduleslot": configSource.getConfig(
                            "cfgemailalertscheduleslot"
                        ),
                    }
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Validator for email alerts: lastAlertMissedCapture: %(lastAlertMissedCapture)s"
                    % {
                        "currentSource": str(currentSource),
                        "lastAlertMissedCapture": str(lastAlertMissedCapture),
                    }
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Validator for email alerts: cfgemailalertscheduleslotfailure: %(cfgemailalertscheduleslotfailure)s"
                    % {
                        "currentSource": str(currentSource),
                        "cfgemailalertscheduleslotfailure": configSource.getConfig(
                            "cfgemailalertscheduleslotfailure"
                        ),
                    }
                )
                self.log.info(
                    "alertsCapture.run(): Source: %(currentSource)s - Validator for email alerts: lastAlert Status: %(lastAlertStatus)s"
                    % {
                        "currentSource": str(currentSource),
                        "lastAlertStatus": lastAlert.getAlertValue("status"),
                    }
                )

                # This section is used to determine if an email alert or a reminder should be sent
                if alertStatus == "RECOVER":
                    if configSource.getConfig("cfgemailalwaysnotify") == "yes":
                        currentAlert.setAlertValue("email", True)
                        currentAlert.setAlertValue("emailType", "RECOVER")
                    elif (
                        configSource.getConfig("cfgemailalwaysnotify") == "no"
                        and configSource.getConfig("cfgemailalerttime") == "yes"
                        and (
                            lastAlertMinutesDiff == None
                            or int(lastAlertMinutesDiff)
                            >= int(configSource.getConfig("cfgemailalerttimefailure"))
                        )
                    ):
                        currentAlert.setAlertValue("email", True)
                        currentAlert.setAlertValue("emailType", "RECOVER")
                    elif (
                        configSource.getConfig("cfgemailalwaysnotify") == "no"
                        and configSource.getConfig("cfgemailalertscheduleslot") == "yes"
                        and (
                            lastAlertMissedCapture == None
                            or int(lastAlertMissedCapture)
                            >= int(cfgemailalertscheduleslotfailure)
                        )
                    ):
                        currentAlert.setAlertValue("email", True)
                        currentAlert.setAlertValue("emailType", "RECOVER")
                elif alertStatus == "ERROR" and (
                    lastAlert.getAlertValue("status") == "GOOD"
                    or lastAlert.getAlertValue("status") == "LATE"
                    or lastAlert.getAlertValue("status") == "RECOVER"
                    or lastEmail.getAlert() == {}
                ):
                    currentAlert.setAlertValue("email", True)
                    currentAlert.setAlertValue("emailType", "NEW")

                if currentAlert.getAlertValue("email") == True:
                    self.log.info(
                        "alertsCapture.run(): Source: %(currentSource)s - Requesting an email alert to be sent for the source"
                        % {"currentSource": str(currentSource)}
                    )
                    currentAlert.writeAlertFile(lastEmailFile)
                    if currentAlert.getAlertValue("emailType") == "RECOVER":
                        self.alertsEmails.sendCaptureSuccess(currentAlert)
                    else:
                        self.alertsEmails.sendCaptureError(currentAlert)

                currentAlert.archiveAlertFile()
                currentAlert.writeAlertFile(lastAlertFile)
            else:
                self.log.info(
                    "alertsCapture.run(): Schedule based email alerts disabled for the source"
                )
            self.log.info("alertsCapture.run(): ---------")

    def getNextCaptureSlot(self, currentTime, sourceSchedule, configSource):
        """Calculates the next expected capture slot based on calendar"""
        self.log.debug("alertsCapture.getNextCaptureSlot(): Start")

        sourceTimeDayOfWeek = currentTime.strftime("%w")
        if sourceTimeDayOfWeek == 0:  # Sunday is 7, not 0
            sourceTimeDayOfWeek = 7
        sourceTimeHour = currentTime.strftime("%H")
        sourceTimeMinute = currentTime.strftime("%M")
        sourceTimeWeek = currentTime.strftime("%W")
        sourceTimeYear = currentTime.strftime("%Y")
        sourceTargetWeek = sourceTimeWeek
        sourceTime = int(
            str(sourceTimeDayOfWeek) + str(sourceTimeHour) + str(sourceTimeMinute)
        )

        nextScanTime = None
        for scanTime in sorted(sourceSchedule):
            if sourceSchedule[scanTime] == "Y":
                self.log.debug(
                    "alertsCapture.getNextCaptureSlot(): Scanning Day: %(scanDay)s Hour: %(scanHour)s minute: %(scanMinute)s - Status: %(slotActive)s"
                    % {
                        "scanDay": str(scanTime)[0],
                        "scanHour": str(scanTime)[1:3],
                        "scanMinute": str(scanTime)[3:6],
                        "slotActive": sourceSchedule[scanTime],
                    }
                )
                if scanTime >= sourceTime:
                    nextScanTime = scanTime
                    break
        if nextScanTime == None:
            sourceTargetWeek = sourceTimeWeek + 1
            for scanTime in sorted(sourceSchedule):
                if sourceSchedule[scanTime] == "Y":
                    self.log.debug(
                        "alertsCapture.getNextCaptureSlot(): Scanning Day: %(scanDay)s Hour: %(scanHour)s minute: %(scanMinute)s - Status: %(slotActive)s"
                        % {
                            "scanDay": str(scanTime)[0],
                            "scanHour": str(scanTime)[1:3],
                            "scanMinute": str(scanTime)[3:6],
                            "slotActive": sourceSchedule[scanTime],
                        }
                    )
                    nextScanTime = scanTime
                    break

        self.log.info(
            "alertsCapture.getNextCaptureSlot(): Next Capture slot: %(nextScanTime)s"
            % {"nextScanTime": nextScanTime}
        )

        # Build next capture date
        targetDayOfWeek = int(str(scanTime)[0])
        if targetDayOfWeek == 7:
            sourceTargetWeek = int(sourceTargetWeek) + 1
            targetDayOfWeek = 0
        if sourceTargetWeek == 53:
            sourceTimeYear = int(sourceTimeYear) + 1
            sourceTargetWeek = 0

        nextCaptureTime = datetime.strptime(
            str(sourceTimeYear)
            + "-"
            + str(sourceTargetWeek)
            + "-"
            + str(targetDayOfWeek)
            + "-"
            + str(nextScanTime)[1:3]
            + "-"
            + str(nextScanTime)[3:6],
            "%Y-%W-%w-%H-%M",
        )

        if (
            configSource.getConfig("cfgcapturetimezone") != ""
        ):  # Update the timezone from UTC to the source's timezone
            self.log.info(
                "alertsCapture.getNextCaptureSlot(): Source timezone is: %(sourceTimezone)s"
                % {"sourceTimezone": configSource.getConfig("cfgcapturetimezone")}
            )
            sourceTimezone = tz.gettz(configSource.getConfig("cfgcapturetimezone"))
            nextCaptureTime = nextCaptureTime.replace(tzinfo=sourceTimezone)

        return nextCaptureTime

    def getCountMissedSlots(self, currentTime, lastCaptureTime, sourceSchedule):
        """Calculate the number of missed slots between last captured picture and current date using capture schedule"""
        self.log.debug("alertsCapture.getCountMissedSlots(): Start")

        sourceTimeDayOfWeek = currentTime.strftime("%w")
        if sourceTimeDayOfWeek == 0:  # Sunday is 7, not 0
            sourceTimeDayOfWeek = 7
        sourceTimeHour = currentTime.strftime("%H")
        sourceTimeMinute = currentTime.strftime("%M")
        sourceTimeWeek = currentTime.strftime("%W")
        sourceTimeYear = currentTime.strftime("%Y")
        sourceTime = int(
            str(sourceTimeDayOfWeek) + str(sourceTimeHour) + str(sourceTimeMinute)
        )

        captureTimeDayOfWeek = lastCaptureTime.strftime("%w")
        if captureTimeDayOfWeek == 0:  # Sunday is 7, not 0
            captureTimeDayOfWeek = 7
        captureTimeHour = lastCaptureTime.strftime("%H")
        captureTimeMinute = lastCaptureTime.strftime("%M")
        captureTimeWeek = lastCaptureTime.strftime("%W")
        captureTimeYear = lastCaptureTime.strftime("%Y")
        captureTime = int(
            str(captureTimeDayOfWeek) + str(captureTimeHour) + str(captureTimeMinute)
        )

        missedCaptureRoundOne = 0
        missedCaptureRoundTwo = 0
        missedPicturesInDiffWeek = 0
        fullWeekCaptures = len(sourceSchedule)
        self.log.info("alertsCapture.getCountMissedSlots(): Analyzing source schedule")
        self.log.info(
            "alertsCapture.getCountMissedSlots(): Source Time: %(sourceTime)s"
            % {"sourceTime": sourceTime}
        )
        self.log.info(
            "alertsCapture.getCountMissedSlots(): Capture Time: %(captureTime)s"
            % {"captureTime": captureTime}
        )
        self.log.info(
            "alertsCapture.getCountMissedSlots(): Number of captures in full week: %(fullWeekCaptures)s"
            % {"fullWeekCaptures": fullWeekCaptures}
        )
        if captureTimeWeek != sourceTimeWeek:
            diffWeek = (
                ((int(sourceTimeYear) * 52) + int(sourceTimeWeek))
                - ((int(captureTimeYear) * 52) + int(captureTimeWeek))
                - 1
            )
            self.log.info(
                "alertsCapture.getCountMissedSlots(): Number of week difference: %(diffWeek)s"
                % {"diffWeek": diffWeek}
            )
            missedPicturesInDiffWeek = diffWeek * fullWeekCaptures

        # Scan all capture times backward, and count number of slots until it get a match between capture slot and capture time, if no match it keeps going
        for scanTime in reversed(sorted(sourceSchedule)):
            if sourceSchedule[scanTime] == "Y":
                if scanTime == captureTime and sourceTimeWeek == captureTimeWeek:
                    break
                if scanTime <= sourceTime:
                    missedCaptureRoundOne += 1
                    self.log.debug(
                        "alertsCapture.getCountMissedSlots(): Scanning Day: %(scanDay)s Hour: %(scanHour)s minute: %(scanMinute)s - Status: %(slotActive)s"
                        % {
                            "scanDay": str(scanTime)[0],
                            "scanHour": str(scanTime)[1:3],
                            "scanMinute": str(scanTime)[3:6],
                            "slotActive": sourceSchedule[scanTime],
                        }
                    )

        self.log.info(
            "alertsCapture.getCountMissedSlots(): Number of missed captures in round 1: %(missedCaptureRoundOne)s"
            % {"missedCaptureRoundOne": missedCaptureRoundOne}
        )

        if sourceTimeWeek != captureTimeWeek:
            # Scan all capture times backward, and count number of slots until it get a match between capture slot and capture time, if no match it keeps going
            for scanTime in reversed(sorted(sourceSchedule)):
                if sourceSchedule[scanTime] == "Y":
                    if scanTime == captureTime:
                        break
                    if scanTime >= captureTime:
                        missedCaptureRoundTwo += 1
                        self.log.debug(
                            "alertsCapture.getCountMissedSlots(): Scanning Day: %(scanDay)s Hour: %(scanHour)s minute: %(scanMinute)s - Status: %(slotActive)s"
                            % {
                                "scanDay": str(scanTime)[0],
                                "scanHour": str(scanTime)[1:3],
                                "scanMinute": str(scanTime)[3:6],
                                "slotActive": sourceSchedule[scanTime],
                            }
                        )

        self.log.info(
            "alertsCapture.getCountMissedSlots(): Number of missed captures in round 2: %(missedCaptureRoundTwo)s"
            % {"missedCaptureRoundTwo": missedCaptureRoundTwo}
        )

        missedCapture = (
            missedCaptureRoundOne + missedCaptureRoundTwo + missedPicturesInDiffWeek
        )

        """
        for scanDay in reversed(sorted(sourceSchedule)):
            for scanHour in reversed(sorted(sourceSchedule[scanDay])):
                for scanMinute in reversed(sorted(sourceSchedule[scanDay][scanHour])):
                    if sourceSchedule[scanDay][scanHour][scanMinute] == "Y":
                        if sourceTimeDayOfWeek == scanDay and scanHour == sourceTimeHour and scanMinute <= sourceTimeMinute:
                            missedCapture += 1

                        self.log.info("alertsCapture.getCountMissedSlots(): Scanning Day: %(scanDay)s Hour: %(scanHour)s minute: %(scanMinute)s - Status: %(slotActive)s" % {'scanDay': scanDay, 'scanHour': scanHour, 'scanMinute': scanMinute, 'slotActive': sourceSchedule[scanDay][scanHour][scanMinute]})
        """
        return missedCapture

    def getSourceSchedule(self, sourceId):
        """Verify if schedule exists for the source"""
        sourceScheduleFile = (
            self.dirEtc + "config-source" + str(sourceId) + "-schedule.json"
        )
        self.log.debug(
            "alertsCapture.getSourceSchedule(): Check if file exists: %(sourceScheduleFile)s "
            % {"sourceScheduleFile": sourceScheduleFile}
        )
        if os.path.isfile(sourceScheduleFile):
            try:
                with open(sourceScheduleFile) as sourceSchedule:
                    sourceScheduleObj = json.load(sourceSchedule)
                    sourceScheduleNum = self.convertScheduleToFlat(sourceScheduleObj)
                    return sourceScheduleNum
            except Exception:
                self.log.error(
                    "alertsCapture.getSourceSchedule(): File appears corrupted: %(sourceScheduleFile)s "
                    % {"sourceScheduleFile": sourceScheduleFile}
                )
        else:
            return {}

    def convertScheduleToNumericalIndex(self, sourceSchedule):
        self.log.debug("alertsCapture.convertScheduleToNumericalIndex(): Start")
        self.log.info(
            "alertsCapture.convertScheduleToNumericalIndex(): Converting object to numerical index"
        )
        sourceScheduleNum = {}
        for scanDay in sourceSchedule:
            scanDayNum = int(scanDay)
            sourceScheduleNum[scanDayNum] = {}
            for scanHour in sourceSchedule[scanDay]:
                scanHourNum = int(scanHour)
                sourceScheduleNum[scanDayNum][scanHourNum] = {}
                for scanMinute in sourceSchedule[scanDay][scanHour]:
                    scanMinuteNum = int(scanMinute)
                    sourceScheduleNum[scanDayNum][scanHourNum][
                        scanMinuteNum
                    ] = sourceSchedule[scanDay][scanHour][scanMinute]
        return sourceScheduleNum

    # As a tentative to simplify the core, return the schedule as a flat array
    def convertScheduleToFlat(self, sourceSchedule):
        self.log.debug("alertsCapture.convertScheduleToNumericalIndex(): Start")
        self.log.info(
            "alertsCapture.convertScheduleToNumericalIndex(): Converting object to flat array"
        )
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
                    sourceScheduleFlat[fullKey] = sourceSchedule[scanDay][scanHour][
                        scanMinute
                    ]
        return sourceScheduleFlat
