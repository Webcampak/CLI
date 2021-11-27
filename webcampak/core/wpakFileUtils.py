#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2010-2012 Infracom & Eurotechnia (support@webcampak.com)
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
from __future__ import division
from builtins import str
from builtins import object
from past.utils import old_div
import os
import shlex, subprocess
import re
import datetime
from dateutil import tz
import time


class fileUtils(object):
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir
        self.configPaths = parentClass.configPaths
        self.configGeneral = parentClass.configGeneral

        # self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirSources = self.configPaths.getConfig("parameters")["dir_sources"]
        self.dirCache = self.configPaths.getConfig("parameters")["dir_cache"]
        # self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']

    # Function: CheckDir
    # Description; This function is used to check if a directory/file exists, if not it create it (with appropriate path)
    ## filepath: File path
    # Return: Nothing
    @staticmethod
    def CheckDir(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    @staticmethod
    def CheckFilepath(filepath):
        d = os.path.dirname(filepath)
        if not os.path.exists(d):
            os.makedirs(d)
        return filepath

        # Function: CheckDirSize

    # Description; This function is used to get the size of a directory and its subdirectories in MB
    ## Directory: Directory
    # Return: Directory size
    @staticmethod
    def CheckDirSize(Directory):
        size = 0
        for (current, subDirs, files) in os.walk(Directory):
            size = size + sum(
                os.path.getsize(os.path.join(current, files)) for files in files
            )
        return old_div(size, (1024 * 1024))

    # Function: CheckDirDu
    # Description; This function runs a "du" agains the specified directory
    ## source: Source Directory
    # Return: Directory size
    @staticmethod
    def CheckDirDu(source):
        DuCommand = "du -sb " + source
        args = shlex.split(DuCommand)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()
        print(output)
        print(errors)
        return str(re.findall(b"\d+", output)[0])

    # Function: CheckJpegFile
    # Description; This function is used to check if a file is a JPEG picture (not only by extension) and does not contains errors
    ## Filename: Filename
    # Return: True or False
    # @staticmethod
    def CheckJpegFile(self, Filename):
        Command = "jpeginfo " + Filename
        import shlex, subprocess

        args = shlex.split(Command)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()
        if "ERROR" in output:
            return False
        else:
            return True

    # Function: ReturnTimestampFromFile
    # Description; This function is used to return a datetime from a jpg file using Webcampak naming convention
    ## Filename: Filename
    # Return: timestamp
    @staticmethod
    def ReturnTimestampFromFile(Filename):
        f = Filename
        cfgnow = datetime.datetime(
            *time.strptime(
                f[0]
                + f[1]
                + f[2]
                + f[3]
                + "/"
                + f[4]
                + f[5]
                + "/"
                + f[6]
                + f[7]
                + "/"
                + f[8]
                + f[9]
                + "/"
                + f[10]
                + f[11]
                + "/"
                + f[12]
                + f[13],
                "%Y/%m/%d/%H/%M/%S",
            )[0:6]
        )
        return cfgnow

    """Returns a human readable size"""

    @staticmethod
    def sizeof_fmt(num, suffix="B"):
        if num != None:
            num = int(str(num.decode("UTF-8")))
            for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
                if abs(num) < 1024.0:
                    return "%3.1f%s%s" % (num, unit, suffix)
                num /= 1024.0
            return "%.1f%s%s" % (num, "Yi", suffix)
        else:
            return "n/a"

    # Function: SecondsSinceLastCapture
    # Description; This function is used to return the number of seconds since last picture captured from a source
    ## Directory: Directory where pictures are located
    # Return: datetime
    # @staticmethod
    def SecondsSinceLastCapture(self, sourcePicturesDirectory, Timezone):
        self.log.debug("fileUtils.SecondsSinceLastCapture(): Start")
        for listpictdir in sorted(os.listdir(sourcePicturesDirectory), reverse=True):
            if listpictdir[:2] == "20" and os.path.isdir(
                sourcePicturesDirectory + listpictdir
            ):
                for listpictfiles in sorted(
                    os.listdir(sourcePicturesDirectory + listpictdir), reverse=True
                ):
                    if (
                        listpictfiles[:2] == "20"
                        and self.CheckJpegFile(
                            sourcePicturesDirectory + listpictdir + "/" + listpictfiles
                        )
                        == True
                    ):
                        self.log.info(
                            "fileUtils.SecondsSinceLastCapture(): Last Picture: %(lastScannedPicture)s"
                            % {
                                "lastScannedPicture": str(
                                    sourcePicturesDirectory
                                    + listpictdir
                                    + "/"
                                    + listpictfiles
                                )
                            }
                        )

                        # print("Last picture: " + sourcePicturesDirectory + listpictdir + "/" + listpictfiles)
                        initDateTime = datetime.datetime.utcnow()
                        if (
                            Timezone != ""
                        ):  # Update the timezone from UTC to the source's timezone
                            sourceTimezone = tz.gettz(Timezone)
                            initDateTime = initDateTime.replace(tzinfo=tz.gettz("UTC"))
                            initDateTime = initDateTime.astimezone(sourceTimezone)
                            fileDateTime = self.ReturnTimestampFromFile(listpictfiles)
                            fileDateTime = fileDateTime.replace(tzinfo=sourceTimezone)
                            self.log.info(
                                "fileUtils.SecondsSinceLastCapture(): File Date: %(fileDate)s"
                                % {"fileDate": str(fileDateTime)}
                            )
                            # fileDateTime = initDateTime.replace(tzinfo=sourceTimezone)
                            # print "Filedate:" + str(fileDateTime)
                        timedifference = initDateTime - fileDateTime
                        return timedifference
                        break
                break

    # Function: SecondsBetweenPictures
    # Description; This function is used to return the number of seconds between last picture of a directory and a specified picture file
    ## Directory: Directory where pictures are located
    ## CurrentFile: Filename to be tested against
    # Return: seconds
    def SecondsBetweenPictures(self, Directory, CurrentFile):
        self.log.debug("fileUtils.SecondsBetweenPictures(): Start")
        for listpictfiles in sorted(os.listdir(Directory), reverse=False):
            if (
                listpictfiles[:2] == "20"
                and self.CheckJpegFile(Directory + "/" + listpictfiles) == True
            ):
                # print "Last picture: " + Directory + "/" + listpictfiles
                # print "Timestamp" + str(FileManager.ReturnTimestampFromFile(CurrentFile))
                timedifference = self.ReturnTimestampFromFile(
                    listpictfiles
                ) - self.ReturnTimestampFromFile(CurrentFile)
                # print "TimeDifference" + str(timedifference.seconds)
                self.log.info(
                    "fileUtils.SecondsSinceLastCapture(): Time difference in seconds %(timedifference)s"
                    % {"timedifference": str(timedifference.seconds)}
                )

                return timedifference.seconds
                break
