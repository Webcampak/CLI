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
from datetime import tzinfo, timedelta, datetime
from pytz import timezone
import shutil
import pytz
import json
import dateutil.parser
import random
import time
import zlib
import gettext
import collections
import shlex, subprocess

from ..wpakConfigObj import Config


class videoUtils(object):
    """ This class contains various utilities functions used during the video creation process
    
    Args:
        videoClass: An instance of capture Class

        
    Attributes:
        tbc
    """

    def __init__(self, videoClass):
        self.log = videoClass.log
        self.config_dir = videoClass.config_dir
        self.currentSourceId = videoClass.currentSourceId
        self.videoType = videoClass.videoType
        self.videoClass = videoClass

        self.configPaths = videoClass.configPaths
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirCurrentSourceVideos = self.videoClass.dirCurrentSourceVideos
        self.dirCurrentSourcePictures = self.videoClass.dirCurrentSourcePictures
        self.dirCurrentSourceLive = self.videoClass.dirCurrentSourceLive
        self.dirCurrentSourceWatermarkDir = self.videoClass.dirCurrentSourceWatermarkDir

        self.configGeneral = videoClass.configGeneral
        self.configSource = videoClass.configSource
        self.configSourceVideo = videoClass.configSourceVideo

        self.fileUtils = videoClass.fileUtils
        self.timeUtils = videoClass.timeUtils
        self.transferUtils = videoClass.transferUtils

    # Getters and Setters
    def setPictureTransformations(self, pictureTransformations):
        """ Used to set pictures transformation class after captureutils init """
        self.pictureTransformations = pictureTransformations

    def formatDateLegend(self, inputDate, outputPattern):
        """ Function used format a date to be displayed (i.e. inserted as a legend)
        Args:
            inputDate: date object
            outputPattern: pattern to be used to represent the date, the pattern is actually a number (this should be optimized)
        
        Returns:
            String: date representation according to the selected pattern
        """
        if outputPattern == "1":
            return " " + inputDate.strftime("%d/%m/%Y - %Hh%M")
        elif outputPattern == "2":
            return " " + inputDate.strftime("%d/%m/%Y")
        elif outputPattern == "3":
            return " " + inputDate.strftime("%Hh%M")
        elif outputPattern == "4":
            return " " + inputDate.strftime("%A %d %B %Y - %Hh%M")
        elif outputPattern == "5":
            return " " + inputDate.strftime("%d %B %Y - %Hh%M")
        elif outputPattern == "6":  # US, 12h format
            return " " + inputDate.strftime("%m/%d/%Y - %Ih%M %p")
        elif outputPattern == "7":  # US, 24h format
            return " " + inputDate.strftime("%m/%d/%Y - %Hh%M")
        else:
            return ""

    def isCreationAllowed(self):
        """ Check if video creation is allowed, mainly for custom videos
        Args:
            None
        
        Returns:
            Boolean: True (creation allowed) or False (creation not allowed)
        """
        self.log.debug("videoUtils.isCreationAllowed(): " + _("Start"))

        AllowCreation = False
        if self.configSource.getConfig('cfgsourceactive') == "yes" and self.videoType == "video":
            AllowCreation = True
            if self.configSourceVideo.getConfig(
                    'cfgvideocodecH2641080pcreate') == "no" and self.configSourceVideo.getConfig(
                    'cfgvideocodecH264720pcreate') == "no" and self.configSourceVideo.getConfig(
                    'cfgvideocodecH264480pcreate') == "no" and self.configSourceVideo.getConfig(
                    'cfgvideocodecH264customcreate') == "no" and self.videoType != "videopost":
                AllowCreation = False
                self.log.info(
                    "videoUtils.isCreationAllowed(): " + _("Video: Error: No video format selected ... Cancelling ..."))
        elif self.videoType == "videocustom":
            currenthour = self.videoClass.getScriptStartTime().strftime("%H")
            currentday = self.videoClass.getScriptStartTime().strftime("%Y%m%d")
            videoName = self.configSourceVideo.getConfig('cfgcustomvidname')
            randomVideoName = videoName + str(random.randint(1, 1000))
            if self.configSourceVideo.getConfig('cfgcustomactive') == "plan04" and currenthour == "04":
                AllowCreation = True
            if os.path.isfile(self.dirCurrentSourceVideos + currentday + "_" + self.configSourceVideo.getConfig(
                    'cfgcustomvidname') + ".1080p.avi"):
                AllowCreation = True
                self.configSourceVideo.setConfig('cfgcustomvidname', randomVideoName)
                self.log.info("videoUtils.isCreationAllowed(): " + _(
                    "Video: Error: File exists: %(File)s - Creating a random filename ") % {
                                  'File': self.dirCurrentSourceVideos + currentday + "_" + self.configSourceVideo.getConfig(
                                      'cfgcustomvidname') + ".1080p.avi"})
            elif os.path.isfile(self.dirCurrentSourceVideos + currentday + "_" + self.configSourceVideo.getConfig(
                    'cfgcustomvidname') + ".720p.avi"):
                AllowCreation = True
                self.configSourceVideo.setConfig('cfgcustomvidname', randomVideoName)
                self.log.info("videoUtils.isCreationAllowed(): " + _(
                    "Video: Error: File exists: %(File)s - Creating a random filename ") % {
                                  'File': self.dirCurrentSourceVideos + currentday + "_" + self.configSourceVideo.getConfig(
                                      'cfgcustomvidname') + ".720p.avi"})
            elif os.path.isfile(self.dirCurrentSourceVideos + currentday + "_" + self.configSourceVideo.getConfig(
                    'cfgcustomvidname') + ".480p.avi"):
                AllowCreation = True
                self.configSourceVideo.setConfig('cfgcustomvidname', randomVideoName)
                self.log.info("videoUtils.isCreationAllowed(): " + _(
                    "Video: Error: File exists: %(File)s - Creating a random filename ") % {
                                  'File': self.dirCurrentSourceVideos + currentday + "_" + self.configSourceVideo.getConfig(
                                      'cfgcustomvidname') + ".480p.avi"})
            elif os.path.isfile(self.dirCurrentSourceVideos + currentday + "_" + self.configSourceVideo.getConfig(
                    'cfgcustomvidname') + ".H264-custom.avi"):
                AllowCreation = True
                self.configSourceVideo.setConfig('cfgcustomvidname', randomVideoName)
                self.log.info("videoUtils.isCreationAllowed(): " + _(
                    "Video: Error: File exists: %(File)s - Creating a random filename ") % {
                                  'File': self.dirCurrentSourceVideos + currentday + "_" + self.configSourceVideo.getConfig(
                                      'cfgcustomvidname') + ".H264-custom.avi"})
            else:
                AllowCreation = True
            if self.configSourceVideo.getConfig('cfgcustomactive') == "no":
                AllowCreation = False
                self.log.info(
                    "videoUtils.isCreationAllowed(): " + _("Video: Creation manually disabled ... Cancelling ..."))
        elif self.videoType == "videopost":
            currenthour = self.videoClass.getScriptStartTime().strftime("%H")
            currentday = self.videoClass.getScriptStartTime().strftime("%Y%m%d")
            if self.configSourceVideo.getConfig('cfgcustomactive') == "plan04" and currenthour == "04":
                AllowCreation = True
            elif self.configSourceVideo.getConfig('cfgcustomactive') == "planon":
                AllowCreation = True
            else:
                AllowCreation = False
                self.log.info(
                    "videoUtils.isCreationAllowed(): " + _("Video: Creation manually disabled ... Cancelling ..."))
        else:
            AllowCreation = False
            self.log.info("videoUtils.isCreationAllowed(): " + _("Video: Source disabled ... Cancelling ..."))
        return AllowCreation

    def addZero(self, number):
        """ Take a numbe and append a 0 if less than 10 """
        returnNb = int(number)
        if returnNb < 10:
            returnNb = "0" + str(returnNb)
        return str(returnNb)

    def identifyCustomStartEnd(self):
        """ Identify custom start and end dates for custom videos
        Args:
            None
        
        Returns:
            Boolean: True (creation allowed) or False (creation not allowed)
        """
        self.log.debug("videoUtils.identifyCustomStartEnd(): " + _("Start"))

        customstart = self.configSourceVideo.getConfig('cfgcustomstartyear') + self.addZero(
            self.configSourceVideo.getConfig('cfgcustomstartmonth')) + self.addZero(
            self.configSourceVideo.getConfig('cfgcustomstartday')) + self.addZero(
            self.configSourceVideo.getConfig('cfgcustomstarthour')) + self.addZero(
            self.configSourceVideo.getConfig('cfgcustomstartminute')) + "00"
        self.videoClass.setCustomVideoStart(customstart)
        customend = self.configSourceVideo.getConfig('cfgcustomendyear') + self.addZero(
            self.configSourceVideo.getConfig('cfgcustomendmonth')) + self.addZero(
            self.configSourceVideo.getConfig('cfgcustomendday')) + self.addZero(
            self.configSourceVideo.getConfig('cfgcustomendhour')) + self.addZero(
            self.configSourceVideo.getConfig('cfgcustomendminute')) + "59"
        self.videoClass.setCustomVideoEnd(customend)

        keepstart = int(self.addZero(self.configSourceVideo.getConfig('cfgcustomkeepstarthour')) + self.addZero(
            self.configSourceVideo.getConfig('cfgcustomkeepstartminute')))
        self.videoClass.setKeepStart(keepstart)
        keepend = int(self.addZero(self.configSourceVideo.getConfig('cfgcustomkeependhour')) + self.addZero(
            self.configSourceVideo.getConfig('cfgcustomkeependminute')))
        self.videoClass.setKeepEnd(keepend)

        #				keepstart = int(self.configSourceVideo.getConfig('cfgcustomkeepstarthour') + self.configSourceVideo.getConfig('cfgcustomkeepstartminute'))
        #				keepend = int(self.configSourceVideo.getConfig('cfgcustomkeependhour') + self.configSourceVideo.getConfig('cfgcustomkeependminute'))
        self.log.info(
            "videoUtils.identifyCustomStartEnd(): " + _("Creation from: %(customstart)s to: %(customend)s") % {
                'customstart': customstart, 'customend': customend})
        if keepstart != 0 or keepend != 0:
            self.log.info("videoUtils.identifyCustomStartEnd(): " + _(
                "Keeping only pictures between: %(keepstart)s and %(keepend)s") % {'keepstart': str(keepstart),
                                                                                   'keepend': str(keepend)})

    def prepareVideoDirectory(self, TargetVideoDir):
        """ Check if directory exists, if it does, delete it. Then re-create it.
        Args:
            TargetVideoDir: Videos creation directory path
        
        Returns:
            None
        """
        self.log.debug("videoUtils.prepareVideoDirectory(): " + _("Start"))
        if os.path.exists(TargetVideoDir):
            shutil.rmtree(TargetVideoDir)
        self.fileUtils.CheckDir(TargetVideoDir)

    def doesVideoFileExists(self, fileDayPrefix):
        """Returns True if the video file exists """
        self.log.debug("videoUtils.doesVideoFileExists(): " + _("Start"))
        for scanVideoFile in sorted(os.listdir(self.dirCurrentSourceVideos)):
            if fileDayPrefix[:8] == scanVideoFile[:8] and scanVideoFile[8] != "_":
                return True
        return False

    def compareImages(self, currentFile):
        """ Compare a picture with the previously copied picture.
            If both pictures are too similar the new picture is not copied.
            
            This operation is being performed through temporary files called filterA.jpg and filterB.jpg
            filterA.jpg is the previous file used to compare against.
            At the end of the process, filterB is being copied into filterA, therefore becomes the last file processed
        Args:
            currentFile: Current file being verified
        
        Returns:
            Boolean: True (Pictures are different) or False (Pictures are too similar, copy should be discarded)
        """
        if self.configSourceVideo.getConfig('cfgfilterwatermarkfile') != "":
            watermarkFile = None
            if os.path.isfile(self.dirCurrentSourceWatermarkDir + self.configSourceVideo.getConfig(
                    'cfgfilterwatermarkfile')):
                watermarkFile = self.dirCurrentSourceWatermarkDir + self.configSourceVideo.getConfig(
                    'cfgfilterwatermarkfile')
            elif os.path.isfile(self.dirWatermark + self.configSourceVideo.getConfig('cfgfilterwatermarkfile')):
                watermarkFile = self.dirWatermark + self.configSourceVideo.getConfig('cfgfilterwatermarkfile')
            if watermarkFile != None:
                self.pictureTransformations.setFilesourcePath(currentFile)
                self.pictureTransformations.setFiledestinationPath(self.videoClass.getProcessVideoDir() + "filterB.jpg")
                self.pictureTransformations.Watermark(0, 0, 0, watermarkFile)
            else:
                self.log.error(
                    "videoUtils.compareImages(): " + _("Unable to find watermark file:  %(watermarkFile)s") % {
                        'watermarkFile': self.configSource.getConfig("cfgpicwatermarkfile")})
        else:
            shutil.copy(currentFile, self.videoClass.getProcessVideoDir() + "filterB.jpg")
        if os.path.isfile(self.videoClass.getProcessVideoDir() + "filterA.jpg"):
            # puzzle-diff 20120123073003-puz.jpg 20120123073202-puz.jpg
            Command = "puzzle-diff " + self.videoClass.getProcessVideoDir() + "filterA.jpg " + self.videoClass.getProcessVideoDir() + "filterB.jpg"
            self.log.info("videoUtils.compareImages(): " + _("Executing command:  %(Command)s") % {'Command': Command})
            args = shlex.split(Command)
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, errors = p.communicate()
            self.log.debug('captureGphoto.triggerCapture() - OUTPUT: ' + output)
            self.log.debug('captureGphoto.triggerCapture() - ERRORS: ' + errors)
            PuzzleDiff = output.strip()
            if float(PuzzleDiff) < float(self.configSourceVideo.getConfig('cfgfiltervalue')):
                self.log.info("videoUtils.compareImages(): " + _(
                    "Difference with previous file: %(PuzzleDiff)s - Config: %(MaxDiff)s -- Skipping file") % {
                                  'PuzzleDiff': PuzzleDiff,
                                  'MaxDiff': self.configSourceVideo.getConfig('cfgfiltervalue')})
                os.remove(self.videoClass.getProcessVideoDir() + "filterB.jpg")
                return False
            else:
                self.log.info("videoUtils.compareImages(): " + _(
                    "Video: Filter: Difference with previous file: %(PuzzleDiff)s - Config: %(MaxDiff)s -- Copying file") % {
                                  'PuzzleDiff': PuzzleDiff,
                                  'MaxDiff': self.configSourceVideo.getConfig('cfgfiltervalue')})
                shutil.copy(self.videoClass.getProcessVideoDir() + "filterB.jpg",
                            self.videoClass.getProcessVideoDir() + "filterA.jpg")
                os.remove(self.videoClass.getProcessVideoDir() + "filterB.jpg")
                return True
        else:
            shutil.copy(self.videoClass.getProcessVideoDir() + "filterB.jpg",
                        self.videoClass.getProcessVideoDir() + "filterA.jpg")
            os.remove(self.videoClass.getProcessVideoDir() + "filterB.jpg")
            return True

    def countNumberOfFilesPerExtension(self, scanDirectory):
        """calculate the number of files per file extension """
        self.log.debug("videoUtils.countNumberOfFilesPerExtension(): " + _("Start"))
        extensionsCount = collections.defaultdict(int)
        for path, dirs, files in os.walk(scanDirectory):
            for filename in files:
                extensionsCount[os.path.splitext(filename)[1].lower()] += 1
        return extensionsCount

    def copyFilesToVideoDirectory(self):
        """ Copy files to video directory for creation
        Args:
            None
        
        Returns:
            None
        """
        self.log.info("fileUtils.copyFilesToVideoDirectory(): " + _("Copying files into temporary directory"))
        VideoTag = False
        filesCopied = 0
        for scanPictureDay in sorted(os.listdir(self.dirCurrentSourcePictures), reverse=True):
            if scanPictureDay[:2] == "20" and os.path.isdir(self.dirCurrentSourcePictures + scanPictureDay):
                extensionsCount = self.countNumberOfFilesPerExtension(self.dirCurrentSourcePictures + scanPictureDay)

                if scanPictureDay[:8] == self.videoClass.getScriptStartTime().strftime(
                        "%Y%m%d") and self.videoType == "video" and VideoTag == False:
                    self.log.info("videoUtils.copyFilesToVideoDirectory(): " + _(
                        "Date: %(currentDay)s: Error, you are trying to create a daily video of the current day, try creating a custom video instead") % {
                                      'currentDay': self.videoClass.getScriptStartTime().strftime("%Y%m%d")})
                elif self.doesVideoFileExists(
                        scanPictureDay[:8]) == True and self.videoType == "video" and VideoTag == False:
                    self.log.info("videoUtils.copyFilesToVideoDirectory(): " + _(
                        "Error, video file exists for the date: %(cfgdispday)s") % {'cfgdispday': scanPictureDay[:8]})
                elif extensionsCount['.jpg'] < 10:
                    self.log.info("videoUtils.copyFilesToVideoDirectory(): " + _(
                        "Error, not enough jpg files for date: %(cfgdispday)s (only %(nbjpgfiles)s files)") % {
                                      'cfgdispday': scanPictureDay[:8], 'nbjpgfiles': extensionsCount['.jpg']})
                else:
                    if self.videoType == "video" and VideoTag == False:
                        self.videoClass.setCustomVideoStart(scanPictureDay[:8] + "000000")
                        self.videoClass.setCustomVideoEnd(scanPictureDay[:8] + "235959")
                        self.videoClass.setVideoFilename(scanPictureDay[:8])
                        VideoTag = True
                    self.log.info("videoUtils.copyFilesToVideoDirectory(): " + _(
                        "Creation requested from: %(customstart)s to: %(customend)s ") % {
                                      'customstart': self.videoClass.getCustomVideoStart(),
                                      'customend': self.videoClass.getCustomVideoEnd()})
                    self.log.info("videoUtils.copyFilesToVideoDirectory(): " + _(
                        "Keeping pictures between: %(keepstart)s and: %(keepend)s ") % {
                                      'keepstart': self.videoClass.getKeepStart(),
                                      'keepend': self.videoClass.getKeepEnd()})
                    for scanPictureFile in sorted(os.listdir(self.dirCurrentSourcePictures + scanPictureDay),
                                                  reverse=True):
                        # Only keep file if they have a numerical filename
                        # Applying date restrictions where necessary
                        if os.path.splitext(scanPictureFile)[0].isdigit() == True and int(
                                os.path.splitext(scanPictureFile)[0]) > int(
                                self.videoClass.getCustomVideoStart()) and int(
                                os.path.splitext(scanPictureFile)[0]) < int(self.videoClass.getCustomVideoEnd()):
                            copyFile = False
                            keepstart = self.videoClass.getKeepStart()
                            keepend = self.videoClass.getKeepEnd()
                            if (self.videoType == "videocustom" or self.videoType == "videopost") and (
                                    keepstart != 0 or keepend != 0):
                                currentfilestamp = int(
                                    scanPictureFile[8] + scanPictureFile[9] + scanPictureFile[10] + scanPictureFile[11])
                                if currentfilestamp >= keepstart and currentfilestamp <= keepend:
                                    if self.configSourceVideo.getConfig(
                                            "cfgfilteractivate") == "yes":  # Activate filter to diff files
                                        copyFile = self.compareImages(
                                            self.dirCurrentSourcePictures + scanPictureDay + "/" + scanPictureFile)
                                    else:
                                        copyFile = True
                            else:
                                if self.configSourceVideo.getConfig(
                                        "cfgfilteractivate") == "yes":  # Activate filter to diff files
                                    copyFile = self.compareImages(
                                        self.dirCurrentSourcePictures + scanPictureDay + "/" + scanPictureFile)
                                else:
                                    copyFile = True

                            if self.videoType == "videocustom" or self.videoType == "videopost":
                                if self.configSourceVideo.getConfig(
                                        "cfgvidminintervalvalue") != "0":  # check time between two pictures
                                    # self.log.info("videoUtils.run(): " + _("Video: %(VideoType)s: Minimum interval between two pictures: %(cfgvidminintervalvalue)s %(cfgvidmininterval)s ") % {'VideoType': self.videoType, 'cfgvidminintervalvalue': self.configSourceVideo.getConfig("cfgvidminintervalvalue"), 'cfgvidmininterval': self.configSourceVideo.getConfig("cfgvidmininterval") } )
                                    SecondsBetweenPictures = self.fileUtils.SecondsBetweenPictures(TargetVideoDir,
                                                                                                   scanPictureFile)
                                    ReferenceInterval = int(self.configSourceVideo.getConfig("cfgvidminintervalvalue"))
                                    if SecondsBetweenPictures != None:
                                        if self.configSourceVideo.getConfig("cfgvidmininterval") == "minutes":
                                            ReferenceInterval = ReferenceInterval * 60
                                            if SecondsBetweenPictures < ReferenceInterval - 10:
                                                copyFile = False
                                        else:
                                            if SecondsBetweenPictures < ReferenceInterval:
                                                copyFile = False
                                        if copyFile == False:
                                            self.log.info("videoUtils.run(): " + _(
                                                "Video: %(VideoType)s: Discarding picture, minimum interval:  %(ReferenceInterval)s s - Current Difference: %(SecondsBetweenPictures)s, Current file: %(scanPictureFile)s ") % {
                                                              'VideoType': self.videoType,
                                                              'ReferenceInterval': str(ReferenceInterval),
                                                              'SecondsBetweenPictures': str(SecondsBetweenPictures),
                                                              'scanPictureFile': str(scanPictureFile)})

                            if copyFile == True:  # Copy files to temporary directory to be processed for video creation
                                filesCopied = filesCopied + 1
                                shutil.copy(self.dirCurrentSourcePictures + scanPictureDay + "/" + scanPictureFile,
                                            self.videoClass.getProcessVideoDir() + scanPictureFile)
                                self.log.info("videoUtils.copyFilesToVideoDirectory(): " + _(
                                    "Copy picture to temporary directory: %(scanPictureFile)s") % {
                                                  'VideoType': self.videoType, 'scanPictureFile': str(scanPictureFile)})
        return filesCopied

    def modifyPictures(self, filePath):
        """ Modify pictures in preparation of video creation:
            - Video effect
            - Watermark
            - Legend
            - Resize
            
        Args:
            filePath: a string, filepath of the picture to modify        
        Returns:
            None
        """
        self.log.debug("videoUtils.modifyPictures(): " + _("Start"))
        pictureTime = datetime.strptime(os.path.splitext(os.path.basename(filePath))[0], "%Y%m%d%H%M%S")

        self.log.info("videoUtils.modifyPictures(): " + _("Processing file: %(filePath)s - Date: %(pictureTime)s") % {
            'filePath': filePath, 'pictureTime': pictureTime.isoformat()})

        self.pictureTransformations.setFilesourcePath(filePath)
        self.pictureTransformations.setFiledestinationPath(filePath)

        if self.configSourceVideo.getConfig('cfgvideoeffect') == "sketch":
            self.log.info(
                "videoUtils.modifyPictures(): " + _("Adding sketch effect to: %(filePath)s ") % {'filePath': filePath})
            self.pictureTransformations.Sketch(self.videoClass.getProcessVideoDir())
        elif self.configSourceVideo.getConfig('cfgvideoeffect') == "tiltshift":
            self.log.info("videoUtils.modifyPictures(): " + _("Adding tiltshift effect to: %(filePath)s ") % {
                'filePath': filePath})
            self.pictureTransformations.TiltShift()
        elif self.configSourceVideo.getConfig('cfgvideoeffect') == "charcoal":
            self.log.info("videoUtils.modifyPictures(): " + _("Adding charcoal effect to: %(filePath)s ") % {
                'filePath': filePath})
            self.pictureTransformations.Charcoal()
        elif self.configSourceVideo.getConfig('cfgvideoeffect') == "colorin":
            self.log.info(
                "videoUtils.modifyPictures(): " + _("Adding colorin effect to: %(filePath)s ") % {'filePath': filePath})
            self.pictureTransformations.ColorIn()

        if self.configSourceVideo.getConfig('cfgwatermarkactivate') == "yes":
            self.log.info("videoUtils.modifyPictures(): " + _("Adding Watermark to: %(File)s ") % {'File': filePath})
            watermarkFile = None
            if os.path.isfile(self.dirCurrentSourceWatermarkDir + self.configSourceVideo.getConfig(
                    'cfgfilterwatermarkfile')):
                watermarkFile = self.dirCurrentSourceWatermarkDir + self.configSourceVideo.getConfig(
                    'cfgfilterwatermarkfile')
            elif os.path.isfile(self.dirWatermark + self.configSourceVideo.getConfig('cfgfilterwatermarkfile')):
                watermarkFile = self.dirWatermark + self.configSourceVideo.getConfig('cfgfilterwatermarkfile')
            if watermarkFile != None:
                self.pictureTransformations.setFilesourcePath(currentFile)
                self.pictureTransformations.setFiledestinationPath(self.videoClass.getProcessVideoDir() + "filterB.jpg")
                self.pictureTransformations.Watermark(self.configSourceVideo.getConfig('cfgwatermarkpositionx'),
                                                      self.configSourceVideo.getConfig('cfgwatermarkpositiony'),
                                                      self.configSourceVideo.getConfig('cfgwatermarkdissolve'),
                                                      watermarkFile)
        if self.configSourceVideo.getConfig('cfgvideopreimagemagicktxt') == "yes":
            self.log.info("videoUtils.modifyPictures(): " + _("Adding Legend to: %(File)s ") % {'File': filePath})
            self.pictureTransformations.Text(self.configSourceVideo.getConfig('cfgvideopreimgtextfont'),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtextsize'),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtextgravity'),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtextbasecolor'),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtextbaseposition'),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtext'),
                                             self.formatDateLegend(pictureTime, self.configSourceVideo.getConfig(
                                                 'cfgvideopreimgdateformat')),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtextovercolor'),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtextoverposition'))
        if self.configSourceVideo.getConfig('cfgvideopreresize') != "no":
            self.log.info("videoUtils.modifyPictures(): " + _("Video: ImageMagick: Resizing: %(File)s to %(Size)s") % {
                'File': filePath, 'Size': self.configSourceVideo.getConfig('cfgvideopreresizeres')})
            self.pictureTransformations.resize(self.configSourceVideo.getConfig('cfgvideopreresizeres'))

    def modifyPicturesPost(self, filePath):
        """ Modify pictures in preparation of video creation:
            - Rotate
            - Create Thumbnail
            - Crop
            - Resize
            - Video effect
            - Watermark
            - Legend
            
        Args:
            filePath: a string, filepath of the picture to modify        
        Returns:
            None
        """
        self.log.debug("videoUtils.modifyPictures(): " + _("Start"))
        self.log.info("videoUtils.modifyPictures(): " + _("Processing file: %(filePath)s ") % {'filePath': filePath})
        pictureTime = datetime.strptime(os.path.splitext(os.path.basename(filePath))[0], "%Y%m%d%H%M%S")
        self.log.info("videoUtils.modifyPictures(): " + _("Picture date: %(pictureTime)s ") % {
            'pictureTime': pictureTime.isoformat()})

        self.pictureTransformations.setFilesourcePath(filePath)
        self.pictureTransformations.setFiledestinationPath(filePath)

        if self.configSourceVideo.getConfig('cfgrotateactivate') == "yes":
            self.log.info(
                "videoUtils.modifyPicturesPost(): " + _("Rotating file: %(filePath)s by %(degrees)s degrees") % {
                    'filePath': filePath, 'degrees': self.configSourceVideo.getConfig('cfgrotateangle')})
            self.pictureTransformations.rotate(self.configSourceVideo.getConfig('cfgrotateangle'))

        if self.configSourceVideo.getConfig('cfgthumbnailactivate') == "yes" and self.configSourceVideo.getConfig(
                'cfgtransitionactivate') != "yes":
            self.log.info("videoUtils.modifyPicturesPost(): " + _("Creating thumbnail of file: %(filePath)s") % {
                'filePath': filePath})
            self.pictureTransformations.setFiledestinationPath(self.videoClass.getProcessVideoDir() + "thumbnail.jpg")
            self.pictureTransformations.crop(self.configSourceVideo.getConfig('cfgthumbnailsrccropsizewidth'),
                                             self.configSourceVideo.getConfig('cfgthumbnailsrccropsizeheight'),
                                             self.configSourceVideo.getConfig('cfgthumbnailsrccropxpos'),
                                             self.configSourceVideo.getConfig('cfgthumbnailsrccropypos'))
            self.pictureTransformations.setFilesourcePath(self.videoClass.getProcessVideoDir() + "thumbnail.jpg")
            self.pictureTransformations.resize(
                self.configSourceVideo.getConfig('cfgthumbnaildstsizewidth') + "x" + self.configSourceVideo.getConfig(
                    'cfgthumbnaildstsizeheight'))
            if self.configSourceVideo.getConfig('cfgthumbnailborder') == "yes":
                self.pictureTransformations.Border("#909090", "5", "5")
            self.log.info("videoUtils.modifyPicturesPost(): " + _("Thumbnail stored in: %(filePath)s") % {
                'filePath': self.videoClass.getProcessVideoDir() + "thumbnail.jpg"})

            self.pictureTransformations.setFilesourcePath(filePath)
            self.pictureTransformations.setFiledestinationPath(filePath)

        if self.configSourceVideo.getConfig('cfgtransitionactivate') != "yes" and self.configSourceVideo.getConfig(
                'cfgcropactivate') == "yes":
            self.log.info(
                "videoUtils.modifyPicturesPost(): " + _("Cropping file: %(filePath)s ") % {'filePath': filePath})
            self.pictureTransformations.crop(self.configSourceVideo.getConfig('cfgcropsizewidth'),
                                             self.configSourceVideo.getConfig('cfgcropsizeheight'),
                                             self.configSourceVideo.getConfig('cfgcropxpos'),
                                             self.configSourceVideo.getConfig('cfgcropypos'))

        if self.configSourceVideo.getConfig('cfgvideosizeactivate') == "yes":
            self.log.info("videoUtils.modifyPicturesPost(): " + _("Resizing file: %(filePath)s to: %(Size)s") % {
                'filePath': filePath, 'Size': self.configSourceVideo.getConfig('cfgvideopreresizeres')})
            self.pictureTransformations.resize(
                self.configSourceVideo.getConfig('cfgvideosizewidth') + "x" + self.configSourceVideo.getConfig(
                    'cfgvideosizeheight'))

        if self.configSourceVideo.getConfig('cfgvideoeffect') == "sketch":
            self.log.info("videoUtils.modifyPicturesPost(): " + _("Adding sketch effect to: %(filePath)s ") % {
                'filePath': filePath})
            self.pictureTransformations.Sketch(self.videoClass.getProcessVideoDir())
        elif self.configSourceVideo.getConfig('cfgvideoeffect') == "tiltshift":
            self.log.info("videoUtils.modifyPicturesPost(): " + _("Adding tiltshift effect to: %(filePath)s ") % {
                'filePath': filePath})
            self.pictureTransformations.TiltShift()
        elif self.configSourceVideo.getConfig('cfgvideoeffect') == "charcoal":
            self.log.info("videoUtils.modifyPicturesPost(): " + _("Adding charcoal effect to: %(filePath)s ") % {
                'filePath': filePath})
            self.pictureTransformations.Charcoal()
        elif self.configSourceVideo.getConfig('cfgvideoeffect') == "colorin":
            self.log.info("videoUtils.modifyPicturesPost(): " + _("Adding colorin effect to: %(filePath)s ") % {
                'filePath': filePath})
            self.pictureTransformations.ColorIn()

        if self.configSourceVideo.getConfig('cfgthumbnailactivate') == "yes":
            self.log.info("videoUtils.modifyPicturesPost(): " + _("Inserting thumbnail into: %(filePath)s") % {
                'filePath': filePath})
            self.pictureTransformations.Watermark(self.configSourceVideo.getConfig('cfgwatermarkpositionx'),
                                                  self.configSourceVideo.getConfig('cfgwatermarkpositiony'),
                                                  self.configSourceVideo.getConfig('cfgwatermarkdissolve'),
                                                  self.videoClass.getProcessVideoDir() + "thumbnail.jpg")
            self.log.info("videoUtils.modifyPicturesPost(): " + _(
                "Insertion completed, deleting thumbnail stored at: %(filePath)s") % {
                              'filePath': self.videoClass.getProcessVideoDir() + "thumbnail.jpg"})
            os.remove(self.videoClass.getProcessVideoDir() + "thumbnail.jpg")

        if self.configSourceVideo.getConfig('cfgwatermarkactivate') == "yes":
            self.log.info(
                "videoUtils.modifyPicturesPost(): " + _("Adding Watermark to: %(File)s ") % {'File': filePath})
            watermarkFile = None
            if os.path.isfile(self.dirCurrentSourceWatermarkDir + self.configSourceVideo.getConfig(
                    'cfgfilterwatermarkfile')):
                watermarkFile = self.dirCurrentSourceWatermarkDir + self.configSourceVideo.getConfig(
                    'cfgfilterwatermarkfile')
            elif os.path.isfile(self.dirWatermark + self.configSourceVideo.getConfig('cfgfilterwatermarkfile')):
                watermarkFile = self.dirWatermark + self.configSourceVideo.getConfig('cfgfilterwatermarkfile')
            if watermarkFile != None:
                self.pictureTransformations.setFilesourcePath(currentFile)
                self.pictureTransformations.setFiledestinationPath(self.videoClass.getProcessVideoDir() + "filterB.jpg")
                self.pictureTransformations.Watermark(self.configSourceVideo.getConfig('cfgwatermarkpositionx'),
                                                      self.configSourceVideo.getConfig('cfgwatermarkpositiony'),
                                                      self.configSourceVideo.getConfig('cfgwatermarkdissolve'),
                                                      watermarkFile)

        if self.configSourceVideo.getConfig('cfgvideopreimagemagicktxt') == "yes":
            self.log.info("videoUtils.modifyPicturesPost(): " + _("Adding Legend to: %(File)s ") % {'File': filePath})
            self.pictureTransformations.Text(self.configSourceVideo.getConfig('cfgvideopreimgtextfont'),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtextsize'),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtextgravity'),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtextbasecolor'),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtextbaseposition'),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtext'),
                                             self.formatDateLegend(pictureTime, self.configSourceVideo.getConfig(
                                                 'cfgvideopreimgdateformat')),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtextovercolor'),
                                             self.configSourceVideo.getConfig('cfgvideopreimgtextoverposition'))

    def transitionPictures(self):
        """ Performs a progressive panning of view within a set of pictures
            
        Args:
            None
        Returns:
            None
        """
        self.log.debug("videoUtils.transitionPictures(): " + _("Start"))
        TransitionNbFiles = len(os.listdir(self.videoClass.getProcessVideoDir()))
        TrStartWidth = float(self.configSourceVideo.getConfig('cfgcropsizewidth'))
        TrStartHeight = float(self.configSourceVideo.getConfig('cfgcropsizeheight'))
        TrStartX = float(self.configSourceVideo.getConfig('cfgcropxpos'))
        TrStartY = float(self.configSourceVideo.getConfig('cfgcropypos'))
        TrEndWidth = float(self.configSourceVideo.getConfig('cfgtransitioncropsizewidth'))
        TrEndHeight = float(self.configSourceVideo.getConfig('cfgtransitioncropsizeheight'))
        TrEndX = float(self.configSourceVideo.getConfig('cfgtransitioncropxpos'))
        TrEndY = float(self.configSourceVideo.getConfig('cfgtransitioncropypos'))
        TrDiffWidth = TrStartWidth - TrEndWidth
        TrDiffHeight = TrStartHeight - TrEndHeight
        TrDiffX = TrStartX - TrEndX
        TrDiffY = TrStartY - TrEndY
        TrDiffStepWidth = TrDiffWidth / TransitionNbFiles
        TrDiffStepHeight = TrDiffHeight / TransitionNbFiles
        TrDiffStepX = TrDiffX / TransitionNbFiles
        TrDiffStepY = TrDiffY / TransitionNbFiles
        UpdatedCropWidth = TrStartWidth
        UpdatedCropHeight = TrStartHeight
        UpdatedCropX = TrStartX
        UpdatedCropY = TrStartY
        self.log.info("videoUtils.transitionPictures(): " + _(
            "Processing %(TransitionNbFiles)s pictures: W diff:%(TrDiffStepWidth)s H diff:%(TrDiffStepHeight)s X diff:%(TrDiffStepX)s Y diff:%(TrDiffStepY)s") % {
                          'TransitionNbFiles': str(TransitionNbFiles),
                          'TrDiffStepWidth': str(round(TrDiffStepWidth, 2)),
                          'TrDiffStepHeight': str(round(TrDiffStepHeight, 2)),
                          'TrDiffStepX': str(round(TrDiffStepX, 2)), 'TrDiffStepY': str(round(TrDiffStepY, 2))})
        for scanPictureFile in sorted(os.listdir(self.videoClass.getProcessVideoDir())):
            UpdatedCropWidth = UpdatedCropWidth - TrDiffStepWidth
            if TrDiffStepWidth < 0 and UpdatedCropWidth > TrEndWidth:
                UpdatedCropWidth = TrEndWidth
            if TrDiffStepWidth > 0 and UpdatedCropWidth < TrEndWidth:
                UpdatedCropWidth = TrEndWidth
            UpdatedCropHeight = UpdatedCropHeight - TrDiffStepHeight
            if TrDiffStepHeight < 0 and UpdatedCropHeight > TrEndHeight:
                UpdatedCropHeight = TrEndWidth
            if TrDiffStepHeight > 0 and UpdatedCropHeight < TrEndHeight:
                UpdatedCropHeight = TrEndWidth
            UpdatedCropX = UpdatedCropX - TrDiffStepX
            if TrDiffStepX < 0 and UpdatedCropX > TrEndX:
                UpdatedCropX = TrEndX
            if TrDiffStepX > 0 and UpdatedCropX < TrEndX:
                UpdatedCropX = TrEndX
            UpdatedCropY = UpdatedCropY - TrDiffStepY
            if TrDiffStepY < 0 and UpdatedCropY > TrEndY:
                UpdatedCropY = TrEndY
            if TrDiffStepY > 0 and UpdatedCropY < TrEndY:
                UpdatedCropY = TrEndY

            self.pictureTransformations.setFilesourcePath(self.videoClass.getProcessVideoDir() + scanPictureFile)
            self.pictureTransformations.setFiledestinationPath(self.videoClass.getProcessVideoDir() + scanPictureFile)

            if self.configSourceVideo.getConfig('cfgthumbnailactivate') == "yes":
                self.log.info("videoUtils.transitionPictures(): " + _("Creating thumbnail of file: %(filePath)s") % {
                    'filePath': filePath})
                self.pictureTransformations.setFiledestinationPath(
                    self.videoClass.getProcessVideoDir() + "thumbnail.jpg")
                self.pictureTransformations.crop(self.configSourceVideo.getConfig('cfgthumbnailsrccropsizewidth'),
                                                 self.configSourceVideo.getConfig('cfgthumbnailsrccropsizeheight'),
                                                 self.configSourceVideo.getConfig('cfgthumbnailsrccropxpos'),
                                                 self.configSourceVideo.getConfig('cfgthumbnailsrccropypos'))
                self.pictureTransformations.setFilesourcePath(self.videoClass.getProcessVideoDir() + "thumbnail.jpg")
                self.pictureTransformations.resize(self.configSourceVideo.getConfig(
                    'cfgthumbnaildstsizewidth') + "x" + self.configSourceVideo.getConfig('cfgthumbnaildstsizeheight'))
                if self.configSourceVideo.getConfig('cfgthumbnailborder') == "yes":
                    self.pictureTransformations.Border("#909090", "5", "5")
                self.log.info("videoUtils.transitionPictures(): " + _("Thumbnail stored in: %(filePath)s") % {
                    'filePath': self.videoClass.getProcessVideoDir() + "thumbnail.jpg"})

            self.pictureTransformations.setFilesourcePath(self.videoClass.getProcessVideoDir() + scanPictureFile)
            self.pictureTransformations.setFiledestinationPath(self.videoClass.getProcessVideoDir() + scanPictureFile)

            self.log.info("videoUtils.transitionPictures(): " + _(
                "Processing picture: %(File)s W:%(UpdatedCropWidth)s H:%(UpdatedCropHeight)s X:%(UpdatedCropX)s Y:%(UpdatedCropY)s") % {
                              'File': self.videoClass.getProcessVideoDir() + scanPictureFile,
                              'UpdatedCropWidth': str(int(UpdatedCropWidth)),
                              'UpdatedCropHeight': str(int(UpdatedCropHeight)), 'UpdatedCropX': str(int(UpdatedCropX)),
                              'UpdatedCropY': str(int(UpdatedCropY))})
            self.pictureTransformations.crop(self.configSourceVideo.getConfig('cfgthumbnailsrccropsizewidth'),
                                             self.configSourceVideo.getConfig('cfgthumbnailsrccropsizeheight'),
                                             self.configSourceVideo.getConfig('cfgthumbnailsrccropxpos'),
                                             self.configSourceVideo.getConfig('cfgthumbnailsrccropypos'))
            self.modifyPicturesPost(self.videoClass.getProcessVideoDir() + scanPictureFile)

            if self.configSourceVideo.getConfig("cfgmovefilestosource") != "no":
                # Verifier si une autre image existe, si oui, ne pas remplacer
                self.sourceDestinationDirectory = self.dirSources + 'source' + self.configSourceVideo.getConfig(
                    "cfgmovefilestosource") + '/' + self.configPaths.getConfig('parameters')[
                                                      'dir_source_pictures'] + scanPictureFile[0:8] + "/"
                self.fileUtils.CheckDir(self.sourceDestinationDirectory)
                if os.path.exists(self.sourceDestinationDirectory + scanPictureFile):
                    self.log.info(
                        "videoUtils.transitionPictures(): " + _("Error: File already exists %(DestinationFile)s") % {
                            'DestinationFile': self.sourceDestinationDirectory + scanPictureFile})
                else:
                    self.log.info("videoUtils.transitionPictures(): " + _("Copy file to: %(DestinationFile)s") % {
                        'DestinationFile': self.sourceDestinationDirectory + scanPictureFile})
                    shutil.copy(self.videoClass.getProcessVideoDir() + scanPictureFile,
                                self.sourceDestinationDirectory + scanPictureFile)
                    os.remove(self.videoClass.getProcessVideoDir() + scanPictureFile)

    def encodeVideo(self, VideoSourceFiles, VideoDestinationFile, VideoLogFile, VideoFPS, VideoCropScaleOptions,
                    VideoPass, VideoBitrate):
        """ Create the video using mencoder
            
        Args:
            VideoSourceFiles: 
            VideoDestinationFile: 
            VideoFPS: 
            VideoCropScaleOptions: 
            VideoPass: 
            VideoBitrate: 
        Returns:
            None
        """
        self.log.debug("videoUtils.encodeVideo(): " + _("Start"))
        self.log.info("videoUtils.transitionPictures(): " + _("Mencoder: Video compression, pass: %(Pass)s") % {
            'Pass': VideoPass})
        self.log.info("videoUtils.transitionPictures(): " + _("Mencoder: Source: %(VideoSourceFiles)s") % {
            'VideoSourceFiles': VideoSourceFiles})
        self.log.info("videoUtils.transitionPictures(): " + _("Mencoder: Destination: %(VideoDestinationFile)s") % {
            'VideoDestinationFile': VideoDestinationFile})
        Command = 'mencoder "mf://' + VideoSourceFiles + '" -mf fps=' + VideoFPS + ' ' + VideoCropScaleOptions + ' -ovc x264 -x264encopts pass=' + VideoPass + ':bitrate=' + VideoBitrate + ':subq=6:partitions=all:8x8dct:me=umh:frameref=5:bframes=3:b_pyramid=normal:weight_b -passlogfile ' + VideoLogFile + ' -o ' + VideoDestinationFile
        self.log.info("videoUtils.transitionPictures(): " + _("Running Command: %(Command)s") % {'Command': Command})
        args = shlex.split(Command)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()
        self.log.info(output)
        self.log.info(errors)

    def addAudio(self, AudioDir, AudioFile, TargetVideoDir, TargetVideoFilename):
        """ This function add an audio stream to a video file
            This function is also able to manage playlists containing a list of mp3 files (one per line)
        Args:
            AudioDir: 
            AudioFile: 
            TargetVideoDir: 
            TargetVideoFilename: 
        Returns:
            None
        """
        if AudioFile == "playlist.m3u":
            self.log.info("videoUtils.addAudio(): " + _("Video: Audio: Analyzing the playlist"))
            JoinMP3Files = ""
            PlaylistScan = open(AudioDir + AudioFile, 'r')
            for lines in PlaylistScan:
                JoinMP3Files = JoinMP3Files + " " + AudioDir + lines
            if JoinMP3Files != "":
                self.log.info("videoUtils.addAudio(): " + _("Video: Audio: Creation of the audio file"))
                Command = "mpgjoin -f --force " + JoinMP3Files + " -o " + AudioDir + "playlist.mp3 "
                self.log.info(
                    "videoUtils.addAudio(): " + _("Building mp3 file from playlist using command: %(Command)s") % {
                        'Command': Command})
                args = shlex.split(Command)
                p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, errors = p.communicate()
                self.log.info(output)
                self.log.info(errors)
                if os.path.isfile(AudioDir + "playlist.mp3"):
                    self.log.info("videoUtils.addAudio(): " + _("Video: Audio: Audiofile successfully created"))
                    AudioFile = "playlist.mp3"
                else:
                    self.log.info("videoUtils.addAudio(): " + _("Video: Audio: Failed to create the audio file"))
        self.log.info("videoUtils.addAudio(): " + _("Video: Audio: Inserting the audio track onto the video"))
        Command = "mencoder -oac copy -ovc copy -audiofile " + AudioDir + AudioFile + " " + TargetVideoDir + TargetVideoFilename + " -o " + TargetVideoDir + TargetVideoFilename + ".tmp >> " + self.Cfglogdir + self.Cfglogfile
        self.log.info(
            "videoUtils.addAudio(): " + _("Adding audio file using Command: %(Command)s") % {'Command': Command})
        args = shlex.split(Command)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()
        shutil.move(TargetVideoDir + TargetVideoFilename + ".tmp", TargetVideoDir + TargetVideoFilename)

        # Function: CreateMP4

    # Description; This function created a MP4 video from the larger video encoded and create a JPG thumbnail from this video
    #	Thumbnail is useful for flash player preview
    # Return: Nothing
    def createMP4(self, TargetVideoDir, TargetVideoFilename):
        """ This function created a MP4 video from the larger video encoded and create a JPG thumbnail from this video
            Thumbnail is useful for flash player preview
        Args:
            TargetVideoDir: 
            TargetVideoFilename: 
        Returns:
            None
        """
        self.log.info("videoUtils.createMP4(): " + _("Video: Flash: Creation of the MP4 video file: %(FlashFile)s") % {
            'FlashFile': TargetVideoDir + TargetVideoFilename + ".mp4"})

        # > ffmpeg -i input -pass 1 -c:v libx264 -preset medium -profile:v \
        # > baseline -b:v 300k -r 30000/1001 -vf scale=480:-1 -f mp4 -y /dev/null \
        # > && ffmpeg -i input -pass 2 -c:v libx264 -preset medium -profile:v \
        # > baseline -b:v 300k -r 30000/1001 -vf scale=480:-1 -c:a aac -strict \
        # > experimental -b:a 192k -ar 48000 output.mp4

        # Command = "ffmpeg -y -i " + TargetVideoDir + TargetVideoFilename + " -vcodec libx264 -b 2000k -g 300 -bf 3 -refs 6 -b_strategy 1 -coder 1 -qmin 10 -qmax 51 -sc_threshold 40 -flags +loop -cmp +chroma -me_range 16 -me_method umh -subq 7 -i_qfactor 0.71 -qcomp 0.6 -qdiff 4 -directpred 3 -flags2 +dct8x8+wpred+bpyramid+mixed_refs -trellis 1 -partitions +parti8x8+parti4x4+partp8x8+partp4x4+partb8x8 -acodec copy " + TargetVideoDir + TargetVideoFilename + ".mp4 "
        Command = "avconv -y -i " + TargetVideoDir + TargetVideoFilename + " -c:v libx264 -preset medium -c:a copy " + TargetVideoDir + TargetVideoFilename + ".mp4 "
        self.log.info(
            "videoUtils.createMP4(): " + _("Creating MP4 file using Command: %(Command)s") % {'Command': Command})

        # Command = "avconv -y -i " + TargetVideoDir + TargetVideoFilename + " -c:v h264 -preset medium -c:a copy " + TargetVideoDir + TargetVideoFilename + ".mp4 "
        args = shlex.split(Command)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()
        self.log.info(output)
        self.log.info(errors)

        shutil.copy(TargetVideoDir + TargetVideoFilename + ".mp4", TargetVideoDir + TargetVideoFilename + ".mp4.bak")

        self.log.info(
            "videoUtils.createMP4(): " + _("Video: Flash: Inserting markers on MP4 video file: %(FlashFile)s") % {
                'FlashFile': TargetVideoDir + TargetVideoFilename + ".mp4"})
        Command = "MP4Box -inter 500 " + TargetVideoDir + TargetVideoFilename + ".mp4 "
        self.log.info(
            "videoUtils.createMP4(): " + _("Creating MP4 markers using Command: %(Command)s") % {'Command': Command})
        args = shlex.split(Command)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()
        self.log.info(output)
        self.log.info(errors)
        if os.path.isfile(TargetVideoDir + TargetVideoFilename + ".mp4"):
            if os.path.getsize(TargetVideoDir + TargetVideoFilename + ".mp4") > 500000:
                self.log.info("videoUtils.createMP4(): " + _("Proper file size: %(FlashFile)s") % {
                    'FlashFile': TargetVideoDir + TargetVideoFilename + ".mp4"})
                os.remove(TargetVideoDir + TargetVideoFilename + ".mp4.bak")
        else:
            self.log.info("videoUtils.createMP4(): " + _("Video: Flash: Invalid file size: %(FlashFile)s") % {
                'FlashFile': TargetVideoDir + TargetVideoFilename + ".mp4"})
            shutil.move(TargetVideoDir + TargetVideoFilename + ".mp4.bak",
                        TargetVideoDir + TargetVideoFilename + ".mp4")

        self.log.info("videoUtils.createMP4(): " + _(
            "Video: Flash: Creation of a preview pictures, located 2 seconds from the beginning of the video"))
        # Command = "ffmpeg -itsoffset -2 -i " + TargetVideoDir + TargetVideoFilename + " -vcodec mjpeg -vframes 1 -an -f rawvideo " + TargetVideoDir + TargetVideoFilename + ".jpg "
        Command = "avconv -itsoffset -2 -i " + TargetVideoDir + TargetVideoFilename + " -vcodec mjpeg -vframes 1 -an -f rawvideo " + TargetVideoDir + TargetVideoFilename + ".jpg "
        self.log.info("videoUtils.createMP4(): " + _("Creating preview pictures using Command: %(Command)s") % {
            'Command': Command})
        args = shlex.split(Command)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()
        self.log.info(output)
        self.log.info(errors)
        if os.path.getsize(TargetVideoDir + TargetVideoFilename + ".jpg") > 20000:
            self.log.info("videoUtils.createMP4(): " + _("Video: Flash: Preview successfully created"))
        else:
            self.log.info("videoUtils.createMP4(): " + _(
                "Video: Flash: Preview failed to be created, trying to create a new one located 2 seconds from the beginning of the video"))
            if os.path.isfile(TargetVideoDir + TargetVideoFilename + ".jpg"):
                os.remove(TargetVideoDir + TargetVideoFilename + ".jpg")
            # Command = "ffmpeg -itsoffset -7 -i " + TargetVideoDir + TargetVideoFilename + " -vcodec mjpeg -vframes 1 -an -f rawvideo " + TargetVideoDir + TargetVideoFilename + ".jpg "
            Command = "avconv -itsoffset -7 -i " + TargetVideoDir + TargetVideoFilename + " -vcodec mjpeg -vframes 1 -an -f rawvideo " + TargetVideoDir + TargetVideoFilename + ".jpg "
            self.log.info("videoUtils.createMP4(): " + _(
                "Re-trying to create preview pictures, 2 seconds into the video using Command: %(Command)s") % {
                              'Command': Command})
            args = shlex.split(Command)
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, errors = p.communicate()
            self.log.info(output)
            self.log.info(errors)

    def createVideos(self, videoformats):
        self.log.debug("videoUtils.createVideos(): " + _("Start"))

        TargetVideoFilename = self.videoClass.getVideoFilename() + "." + videoformats + ".avi"
        TargetLiveVideoFilename = "live." + videoformats + ".avi"
        self.log.info(
            "videoUtils.createVideos(): " + _("Processing format: %(videoformats)s - preparing parameters ") % {
                'videoformats': videoformats})
        CropOptions = ""
        ScaleOptions = ""
        CropScaleOptions = ""
        if self.configSourceVideo.getConfig(
                                "cfgvideocodecH264" + videoformats + "width") != "" and self.configSourceVideo.getConfig(
                                "cfgvideocodecH264" + videoformats + "height") == "":
            ScaleOptions = "scale=" + self.configSourceVideo.getConfig(
                "cfgvideocodecH264" + videoformats + "width") + ":-3"
        elif self.configSourceVideo.getConfig(
                                "cfgvideocodecH264" + videoformats + "width") == "" and self.configSourceVideo.getConfig(
                                "cfgvideocodecH264" + videoformats + "height") != "":
            ScaleOptions = "scale=-3:" + self.configSourceVideo.getConfig("cfgvideocodecH264" + videoformats + "height")
        elif self.configSourceVideo.getConfig(
                                "cfgvideocodecH264" + videoformats + "width") != "" and self.configSourceVideo.getConfig(
                                "cfgvideocodecH264" + videoformats + "height") != "":
            ScaleOptions = "scale=" + self.configSourceVideo.getConfig(
                "cfgvideocodecH264" + videoformats + "width") + ":" + self.configSourceVideo.getConfig(
                "cfgvideocodecH264" + videoformats + "height")
        if self.configSourceVideo.getConfig(
                                "cfgvideocodecH264" + videoformats + "cropwidth") != "" and self.configSourceVideo.getConfig(
                                "cfgvideocodecH264" + videoformats + "cropheight") != "":
            CropOptions = "crop=" + self.configSourceVideo.getConfig(
                "cfgvideocodecH264" + videoformats + "cropwidth") + ":" + self.configSourceVideo.getConfig(
                "cfgvideocodecH264" + videoformats + "cropheight") + ":" + self.configSourceVideo.getConfig(
                "cfgvideocodecH264" + videoformats + "cropx") + ":" + self.configSourceVideo.getConfig(
                "cfgvideocodecH264" + videoformats + "cropy")
        if ScaleOptions != "" and CropOptions == "":
            CropScaleOptions = "-vf " + ScaleOptions
        elif ScaleOptions == "" and CropOptions != "":
            CropScaleOptions = "-vf " + CropOptions
        elif ScaleOptions != "" and CropOptions != "":
            CropScaleOptions = "-vf " + ScaleOptions + "," + CropOptions

        self.log.info("videoUtils.createVideos(): " + _(
            "Video: %(VideoType)s: Format: %(videoformats)s - Compression of the first pass with mencoder") % {
                          'VideoType': self.videoType, 'videoformats': videoformats})
        self.encodeVideo(self.videoClass.getprocessVideoFiles(),
                         self.videoClass.getProcessVideoDir() + TargetVideoFilename,
                         self.videoClass.getProcessVideoDir() + "currentvid.log",
                         self.configSourceVideo.getConfig("cfgvideocodecH264" + videoformats + "fps"), CropScaleOptions,
                         "1", self.configSourceVideo.getConfig("cfgvideocodecH264" + videoformats + "bitrate"))
        if self.configSourceVideo.getConfig("cfgvideocodecH264" + videoformats + "2pass") == "yes":
            self.log.info("videoUtils.createVideos(): " + _(
                "Video: %(VideoType)s: Format: %(videoformats)s - Compression of the second pass with mencoder") % {
                              'VideoType': self.videoType, 'videoformats': videoformats})
            self.encodeVideo(self.videoClass.getprocessVideoFiles(),
                             self.videoClass.getProcessVideoDir() + TargetVideoFilename,
                             self.videoClass.getProcessVideoDir() + "currentvid.log",
                             self.configSourceVideo.getConfig("cfgvideocodecH264" + videoformats + "fps"),
                             CropScaleOptions, "2",
                             self.configSourceVideo.getConfig("cfgvideocodecH264" + videoformats + "bitrate"))

        if os.path.getsize(self.videoClass.getProcessVideoDir() + TargetVideoFilename) > 50000:
            self.log.info("videoUtils.createVideos(): " + _("Mencoder: Video creation completed: %(VideoFile)s") % {
                'VideoFile': self.videoClass.getProcessVideoDir() + TargetVideoFilename})
            if self.configSourceVideo.getConfig("cfgvideoaddaudio") == "yes" and self.configSourceVideo.getConfig(
                    "cfgvideoaudiofile") != "":
                if os.path.isfile(self.Cfgselfaudiodir + self.configSourceVideo.getConfig("cfgvideoaudiofile")):
                    self.addAudio(self.Cfgselfaudiodir, self.configSourceVideo.getConfig("cfgvideoaudiofile"),
                                  self.videoClass.getProcessVideoDir(), TargetVideoFilename)
                elif os.path.isfile(self.Cfgaudiodir + self.configSourceVideo.getConfig("cfgvideoaudiofile")):
                    self.addAudio(self.Cfgaudiodir, self.configSourceVideo.getConfig("cfgvideoaudiofile"),
                                  self.videoClass.getProcessVideoDir(), TargetVideoFilename)
            if self.configSourceVideo.getConfig("cfgvideocodecH264" + videoformats + "createflv") == "yes":
                self.createMP4(self.videoClass.getProcessVideoDir(), TargetVideoFilename)

            if os.path.isfile(self.videoClass.getProcessVideoDir() + TargetVideoFilename):
                self.log.info(
                    "videoUtils.createVideos(): " + _("Video: %(VideoType)s: Copy of the video file into archives") % {
                        'VideoType': self.videoType})
                shutil.copy(self.videoClass.getProcessVideoDir() + TargetVideoFilename,
                            self.dirCurrentSourceVideos + TargetVideoFilename)
                self.log.info("videoUtils.createVideos(): " + _(
                    "Video: %(VideoType)s: Copy of the video file into live directory") % {'VideoType': self.videoType})
                shutil.copy(self.videoClass.getProcessVideoDir() + TargetVideoFilename,
                            self.dirCurrentSourceLive + TargetLiveVideoFilename)
                os.remove(self.videoClass.getProcessVideoDir() + TargetVideoFilename)
            if os.path.isfile(self.videoClass.getProcessVideoDir() + TargetVideoFilename + ".mp4"):
                self.log.info("videoUtils.createVideos(): " + _(
                    "Video: %(VideoType)s: Copy of the MP4 video file into archives") % {'VideoType': self.videoType})
                shutil.copy(self.videoClass.getProcessVideoDir() + TargetVideoFilename + ".mp4",
                            self.dirCurrentSourceVideos + TargetVideoFilename + ".mp4")
                self.log.info("videoUtils.createVideos(): " + _(
                    "Video: %(VideoType)s: Copy of the MP4 video file into live directory") % {
                                  'VideoType': self.videoType})
                shutil.copy(self.videoClass.getProcessVideoDir() + TargetVideoFilename + ".mp4",
                            self.dirCurrentSourceLive + TargetLiveVideoFilename + ".mp4")
                os.remove(self.videoClass.getProcessVideoDir() + TargetVideoFilename + ".mp4")
            if os.path.isfile(self.videoClass.getProcessVideoDir() + TargetVideoFilename + ".jpg"):
                self.log.info("videoUtils.createVideos(): " + _(
                    "Video: %(VideoType)s: Copy of the JPG preview file into archives") % {'VideoType': self.videoType})
                shutil.copy(self.videoClass.getProcessVideoDir() + TargetVideoFilename + ".jpg",
                            self.dirCurrentSourceVideos + TargetVideoFilename + ".jpg")
                self.log.info("videoUtils.createVideos(): " + _(
                    "Video: %(VideoType)s: Copy of the JPG preview file into live directory") % {
                                  'VideoType': self.videoType})
                shutil.copy(self.videoClass.getProcessVideoDir() + TargetVideoFilename + ".jpg",
                            self.dirCurrentSourceLive + TargetLiveVideoFilename + ".jpg")
                os.remove(self.videoClass.getProcessVideoDir() + TargetVideoFilename + ".jpg")

            return TargetVideoFilename
        else:
            self.log.info("video.run(): " + _("Video: %(VideoType)s: Error while creating video: %(VideoFile)s") % {
                'VideoType': self.videoType, 'VideoFile': self.videoClass.getProcessVideoDir() + TargetVideoFilename})
            return False

    def sendVideos(self, TargetVideoFilename, videoformats):
        self.log.debug("videoUtils.sendVideos(): " + _("Start"))
        TargetLiveVideoFilename = "live." + videoformats + ".avi"
        if self.configSourceVideo.getConfig("cfgftpmainserveraviid") != "":
            self.log.info("videoUtils.sendVideos(): " + _("Video: %(VideoType)s: Sending file via FTP: %(FTPFile)s") % {
                'VideoType': self.videoType, 'FTPFile': self.dirCurrentSourceVideos + TargetVideoFilename})
            self.transferUtils.transferFile(self.videoClass.getScriptStartTime(),
                                            self.dirCurrentSourceVideos + TargetVideoFilename, TargetVideoFilename,
                                            self.configSourceVideo.getConfig('cfgftpmainserveraviid'),
                                            self.configSourceVideo.getConfig('cfgftpmainserveraviretry'))
        if self.configSourceVideo.getConfig("cfgftpmainservermp4id") != "":
            self.log.info("videoUtils.sendVideos(): " + _("Video: %(VideoType)s: Sending file via FTP: %(FTPFile)s") % {
                'VideoType': self.videoType, 'FTPFile': self.dirCurrentSourceVideos + TargetVideoFilename + ".mp4"})
            self.transferUtils.transferFile(self.videoClass.getScriptStartTime(),
                                            self.dirCurrentSourceVideos + TargetVideoFilename + ".mp4",
                                            TargetVideoFilename + ".mp4",
                                            self.configSourceVideo.getConfig('cfgftpmainservermp4id'),
                                            self.configSourceVideo.getConfig('cfgftpmainservermp4retry'))
            self.log.info("videoUtils.sendVideos(): " + _("Video: %(VideoType)s: Sending file via FTP: %(FTPFile)s") % {
                'VideoType': self.videoType, 'FTPFile': self.dirCurrentSourceVideos + TargetVideoFilename + ".jpg"})
            self.transferUtils.transferFile(self.videoClass.getScriptStartTime(),
                                            self.dirCurrentSourceVideos + TargetVideoFilename + ".jpg",
                                            TargetVideoFilename + ".jpg",
                                            self.configSourceVideo.getConfig('cfgftpmainservermp4id'),
                                            self.configSourceVideo.getConfig('cfgftpmainservermp4retry'))

        if self.configSourceVideo.getConfig("cfgftphotlinkserveraviid") != "":
            self.log.info("videoUtils.sendVideos(): " + _("Video: %(VideoType)s: Sending file via FTP: %(FTPFile)s") % {
                'VideoType': self.videoType, 'FTPFile': self.dirCurrentSourceVideos + TargetVideoFilename})
            self.transferUtils.transferFile(self.videoClass.getScriptStartTime(),
                                            self.dirCurrentSourceLive + TargetLiveVideoFilename,
                                            TargetLiveVideoFilename,
                                            self.configSourceVideo.getConfig('cfgftphotlinkserveraviid'),
                                            self.configSourceVideo.getConfig('cfgftphotlinkserveraviretry'))
        if self.configSourceVideo.getConfig("cfgftphotlinkservermp4id") != "":
            self.log.info("videoUtils.sendVideos(): " + _("Video: %(VideoType)s: Sending file via FTP: %(FTPFile)s") % {
                'VideoType': self.videoType, 'FTPFile': self.dirCurrentSourceVideos + TargetVideoFilename + ".mp4"})
            self.transferUtils.transferFile(self.videoClass.getScriptStartTime(),
                                            self.dirCurrentSourceLive + TargetLiveVideoFilename + ".mp4",
                                            TargetLiveVideoFilename + ".mp4",
                                            self.configSourceVideo.getConfig('VideoType'),
                                            self.configSourceVideo.getConfig('cfgftphotlinkservermp4retry'))
            self.log.info(
                "videoUtilss.sendVideos(): " + _("Video: %(VideoType)s: Sending file via FTP: %(FTPFile)s") % {
                    'VideoType': self.videoType, 'FTPFile': self.dirCurrentSourceVideos + TargetVideoFilename + ".jpg"})
            self.transferUtils.transferFile(self.videoClass.getScriptStartTime(),
                                            self.dirCurrentSourceLive + TargetLiveVideoFilename + ".jpg",
                                            TargetLiveVideoFilename + ".jpg",
                                            self.configSourceVideo.getConfig('VideoType'),
                                            self.configSourceVideo.getConfig('cfgftphotlinkservermp4retry'))
