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
from builtins import str
from builtins import range
from builtins import object
import os, uuid
import shutil
import re

from .wpakConfigObj import Config
from .wpakFileUtils import fileUtils
from .wpakTimeUtils import timeUtils


# This class is used to initialize transfer queues and dispatch files to the queue
# It reads files from the global queue directory, starting from the oldest ones, and stops one all threads are full
# Each transfer queue (or thread) can hold up to "self.maxFilesPerThread" files


class systemCronJobs(object):
    def __init__(self, log, appConfig, config_dir):
        self.log = log
        self.appConfig = appConfig
        self.config_dir = config_dir
        self.configPaths = Config(self.log, self.config_dir + "param_paths.yml")

        self.dirLogs = self.configPaths.getConfig("parameters")["dir_logs"]
        self.dirEtc = self.configPaths.getConfig("parameters")["dir_etc"]
        self.dirConfig = self.configPaths.getConfig("parameters")["dir_config"]
        self.dirCache = self.configPaths.getConfig("parameters")["dir_cache"]
        self.dirInit = self.configPaths.getConfig("parameters")["dir_init"]
        self.dirBin = self.configPaths.getConfig("parameters")["dir_bin"]

        self.setupLog()

        self.configGeneral = Config(self.log, self.dirConfig + "config-general.cfg")

        self.timeUtils = timeUtils(self)

    def setupLog(self):
        """Setup logging to file"""
        systemLogs = self.dirLogs + "system/"
        if not os.path.exists(systemLogs):
            os.makedirs(systemLogs)
        logFilename = systemLogs + "cron.log"
        self.appConfig.set(self.log._meta.config_section, "file", logFilename)
        self.appConfig.set(self.log._meta.config_section, "rotate", True)
        self.appConfig.set(self.log._meta.config_section, "max_bytes", 512000)
        self.appConfig.set(self.log._meta.config_section, "max_files", 10)
        self.log._setup_file_log()

    # Function: update
    # Description: Update System crontab
    # Return: Nothing
    def update(self):
        self.log.info("systemCronJobs.update(): Update System crontab")
        self.log.info("systemCronJobs.update(): Deleting previous temporary cron file")

        if os.path.isfile(self.dirCache + "crontab"):
            os.remove(self.dirCache + "crontab")

        fileUtils.CheckFilepath(self.dirCache + "crontab")

        if os.path.isfile(self.dirInit + "crontab.init"):
            self.log.info(
                "systemCronJobs.update(): Adding default crontab.init content"
            )
            shutil.copy(self.dirInit + "crontab.init", self.dirCache + "crontab")

        cronttabFile = open(self.dirCache + "crontab", "a")

        for scanfile in sorted(os.listdir(self.dirEtc), reverse=False):
            if re.findall("config-source[0-9]+.cfg", scanfile):
                if scanfile[-1] != "~":
                    sources = re.findall("\d+", scanfile)[0]
                    self.log.info(
                        "systemCronJobs.update(): Processing source %(SourceNumber)s: Captures"
                        % {"SourceNumber": str(sources)}
                    )
                    currentSourceConfig = Config(
                        self.log, self.dirEtc + "config-source" + str(sources) + ".cfg"
                    )
                    cronttabFile.write("#Tasks source:" + str(sources) + "\n")
                    newcronhours = "*"
                    newcrondays = "*"
                    if (
                        currentSourceConfig.getConfig("cfgcroncaptureinterval")
                        == "minutes"
                    ):
                        cronttabFile.write(
                            "*/"
                            + currentSourceConfig.getConfig("cfgcroncapturevalue")
                            + " "
                            + newcronhours
                            + " * * "
                            + newcrondays
                            + " /usr/local/bin/webcampak capture -s "
                            + str(sources)
                            + "\n"
                        )
                    elif (
                        currentSourceConfig.getConfig("cfgcroncaptureinterval")
                        == "seconds"
                    ):
                        cronttabFile.write(
                            "* "
                            + newcronhours
                            + " * * "
                            + newcrondays
                            + " /usr/local/bin/webcampak capture -s "
                            + str(sources)
                            + "\n"
                        )
                        i = 0
                        for secloop in range(1, 30):
                            i = i + int(
                                currentSourceConfig.getConfig("cfgcroncapturevalue")
                            )
                            if i < 60:
                                cronttabFile.write(
                                    "* "
                                    + newcronhours
                                    + " * * "
                                    + newcrondays
                                    + " sleep "
                                    + str(i)
                                    + " && /usr/local/bin/webcampak capture -s "
                                    + str(sources)
                                    + "\n"
                                )
                    self.log.info(
                        "systemCronJobs.update(): Processing source %(SourceNumber)s: Videos"
                        % {"SourceNumber": str(sources)}
                    )
                    cronttabFile.write(
                        currentSourceConfig.getConfig("cfgcrondailyminute")
                        + " "
                        + currentSourceConfig.getConfig("cfgcrondailyhour")
                        + " * * * /usr/local/bin/webcampak video daily -s "
                        + str(sources)
                        + " \n"
                    )
                    self.log.info(
                        "systemCronJobs.update(): Processing source %(SourceNumber)s: Videos Custom "
                        % {"SourceNumber": str(sources)}
                    )
                    if (
                        currentSourceConfig.getConfig("cfgcroncustominterval")
                        == "minutes"
                    ):
                        cronttabFile.write(
                            "*/"
                            + currentSourceConfig.getConfig("cfgcroncustomvalue")
                            + " * * * * flock -xn "
                            + self.dirCache
                            + "createcustom"
                            + str(sources)
                            + ".lock /usr/local/bin/webcampak video custom -s "
                            + str(sources)
                            + " \n"
                        )
                        cronttabFile.write(
                            "*/"
                            + currentSourceConfig.getConfig("cfgcroncustomvalue")
                            + " * * * * flock -xn "
                            + self.dirCache
                            + "createpost"
                            + str(sources)
                            + ".lock /usr/local/bin/webcampak video videopost -s "
                            + str(sources)
                            + " \n"
                        )
                    elif (
                        currentSourceConfig.getConfig("cfgcroncustominterval")
                        == "hours"
                    ):
                        cronttabFile.write(
                            "* */"
                            + currentSourceConfig.getConfig("cfgcroncustomvalue")
                            + " * * * flock -xn "
                            + self.dirCache
                            + "createcustom"
                            + str(sources)
                            + ".lock /usr/local/bin/webcampak video custom -s "
                            + str(sources)
                            + " \n"
                        )
                        cronttabFile.write(
                            "* */"
                            + currentSourceConfig.getConfig("cfgcroncustomvalue")
                            + " * * * flock -xn "
                            + self.dirCache
                            + "createpost"
                            + str(sources)
                            + ".lock /usr/local/bin/webcampak video videopost -s "
                            + str(sources)
                            + " \n"
                        )
                    self.log.info(
                        "systemCronJobs.update(): Processing source %(SourceNumber)s: RRD Graph "
                        % {"SourceNumber": str(sources)}
                    )
                    # cronttabFile.write("*/5 * * * * python " + self.dirBin + "webcampak.py -t rrdgraph -s " + str(sources) + " > " + self.dirLogs + "cronlog-" + str(sources) + "-rrdgraph \n")
                    cronttabFile.write(
                        "*/5 * * * * /usr/local/bin/webcampak stats rrd -s "
                        + str(sources)
                        + " \n"
                    )

                    cronttabFile.write(" " + "\n")
        cronttabFile.close()

        self.log.info("systemCronJobs.update(): Updating the crontab file")

        import shlex, subprocess

        Command = "crontab " + self.dirCache + "crontab"
        args = shlex.split(Command)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()
        self.log.info("systemFtpAccounts.create(): Crontab Create Output: ")
        self.log.info(output)
        self.log.info("systemFtpAccounts.create(): Crontab Create Errors: ")
        self.log.info(errors)

        self.log.info("systemCronJobs.update(): Listing content of the crontab file")

        import shlex, subprocess

        Command = "crontab -l "
        args = shlex.split(Command)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()
        self.log.info("systemFtpAccounts.create(): Crontab List Output: ")
        self.log.info(output)
        self.log.info("systemFtpAccounts.create(): Crontab List Errors: ")
        self.log.info(errors)
