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
import sys

from wpakConfigObj import Config
from wpakTimeUtils import timeUtils
from wpakFileUtils import fileUtils
from wpakTransferUtils import transferUtils

from video.wpakVideoUtils import videoUtils
from video.wpakVideoEmails import videoEmails
from video.wpakVideoObj import videoObj

from wpakPictureTransformations import pictureTransformations
from wpakFTPUtils import FTPUtils

class Video:
    """ This class is used to deal with video creation for the source
    
    Args:
        log: A class, the logging interface
        appConfig: A class, the app config interface
        config_dir: A string, filesystem location of the configuration directory
    	sourceId: Source ID of the source to generate a video for
    	videoType: Type of video to generate
        
    Attributes:
        tbc
    """        
    def __init__(self, log, appConfig, config_dir, sourceId, videoType):
        self.log = log
        self.appConfig = appConfig
        self.config_dir = config_dir
        self.currentSourceId = sourceId
        self.videoType = videoType
        
        self.configPaths = Config(self.log, self.config_dir + 'param_paths.yml')
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']        
        self.dirLocale = self.configPaths.getConfig('parameters')['dir_locale']
        self.dirLocaleMessage = self.configPaths.getConfig('parameters')['dir_locale_message']        
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']
        self.dirXferQueue = self.configPaths.getConfig('parameters')['dir_xfer'] + 'queued/'
        self.dirStats = self.configPaths.getConfig('parameters')['dir_stats']                
        self.dirCache = self.configPaths.getConfig('parameters')['dir_cache']        
        self.dirEmails = self.configPaths.getConfig('parameters')['dir_emails']                
        self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']  
                
        self.dirCurrentSource = self.dirSources + 'source' + self.currentSourceId +'/'
        self.dirCurrentSourceVideos = self.dirSources + 'source' + self.currentSourceId +'/' + self.configPaths.getConfig('parameters')['dir_source_videos']        
        self.dirCurrentSourcePictures = self.dirSources + 'source' + self.currentSourceId +'/' + self.configPaths.getConfig('parameters')['dir_source_pictures']        
        self.dirCurrentSourceLive = self.dirSources + 'source' + self.currentSourceId +'/' + self.configPaths.getConfig('parameters')['dir_source_live']        
        self.dirCurrentSourceWatermarkDir = self.dirSources + 'source' + self.currentSourceId +'/' + self.configPaths.getConfig('parameters')['dir_source_watermark']
        self.dirCurrentSourceResourcesVideos = self.dirSources + 'source' + self.currentSourceId +'/' + self.configPaths.getConfig('parameters')['dir_source_resources_videos']
        self.dirCurrentSourceLogs = self.dirLogs + 'source' + self.currentSourceId +'/'                        

        self.setupLog()
        
        self.configGeneral = Config(self.log, self.dirEtc + 'config-general.cfg')
        self.configSource = Config(self.log, self.dirEtc + 'config-source' + str(self.currentSourceId) + '.cfg')
        self.configSourceFTP = Config(self.log, self.dirEtc + 'config-source' + str(self.currentSourceId) + '-ftpservers.cfg')
        self.configSourceVideo = Config(self.log, self.dirEtc + 'config-source' + str(self.currentSourceId) + '-' + self.videoType + '.cfg')    
           
        self.dirCurrentLocaleMessages = self.dirLocale + self.configSource.getConfig('cfgsourcelanguage') + "/" + self.dirLocaleMessage           
           
        self.initGetText(self.dirLocale, self.configGeneral.getConfig('cfgsystemlang'), self.configGeneral.getConfig('cfggettextdomain'))           
        
        self.timeUtils = timeUtils(self)
        self.fileUtils = fileUtils(self)
        self.FTPUtils = FTPUtils(self)
        self.transferUtils = transferUtils(self)
        
        self.setScriptStartTime(self.timeUtils.getCurrentSourceTime(self.configSource))

        fileVideoLog = self.dirCurrentSourceResourcesVideos + self.getScriptStartTime().strftime("%Y%m") + ".jsonl"
        self.currentVideoDetails = videoObj(self.log, fileVideoLog)
        self.currentVideoDetails.setVideoValue('scriptStartDate', self.getScriptStartTime().isoformat())
        self.currentVideoDetails.setVideoValue('type', self.videoType)

        self.customVideoStart = None
        self.customVideoEnd = None
        self.keepStart = None
        self.keepEnd = None
        self.videoFilename = None
        self.processVideoDir = None
        self.processVideoFiles = None
        
        self.videoUtils = videoUtils(self)
        self.videoEmails = videoEmails(self)
        self.pictureTransformations = pictureTransformations(self)
        self.videoUtils.setPictureTransformations(self.pictureTransformations)        
           
    def setupLog(self):      
        """ Setup logging to file """
        if not os.path.exists(self.dirCurrentSourceLogs):
            os.makedirs(self.dirCurrentSourceLogs)  
        logFilename = self.dirCurrentSourceLogs + "video-" + self.videoType + ".log"
        self.appConfig.set(self.log._meta.config_section, 'file', logFilename)
        self.appConfig.set(self.log._meta.config_section, 'rotate', True)
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
        self.log.debug("capture.initGetText(): Start")     
        try:
            t = gettext.translation(cfggettextdomain, dirLocale, [cfgsystemlang], fallback=True)
            _ = t.ugettext
            t.install()
            self.log.info("video.initGetText(): " + _("Initialized gettext with Domain: %(cfggettextdomain)s - Language: %(cfgsystemlang)s - Path: %(dirLocale)s")
                                                    % {'cfggettextdomain': cfggettextdomain, 'cfgsystemlang': cfgsystemlang, 'dirLocale': dirLocale} )        
        except:
            self.log.error("No translation file available")

    # Setters and Getters
    def setScriptStartTime(self, scriptStartTime):
        self.log.info("video.setScriptStartTime(): " + _("Script Start Time set to: %(scriptStartTime)s") % {'scriptStartTime': scriptStartTime.isoformat()} )        
        self.scriptStartTime = scriptStartTime
        
    def getScriptStartTime(self):
        return self.scriptStartTime
    
    def getCustomVideoStart(self):
        return self.customVideoStart     

    def setCustomVideoStart(self, customVideoStart):
        self.customVideoStart = customVideoStart 
    
    def getCustomVideoEnd(self):
        return self.customVideoEnd
    
    def setCustomVideoEnd(self, customVideoEnd):
        self.customVideoEnd = customVideoEnd

    def getKeepStart(self):
        return self.keepStart
    
    def setKeepStart(self, keepStart):
        self.keepStart = keepStart    
        
    def getKeepEnd(self):
        return self.keepStart
    
    def setKeepEnd(self, keepEnd):
        self.keepEnd = keepEnd            

    def getVideoFilename(self):
        return self.videoFilename
    
    def setVideoFilename(self, videoFilename):
        self.videoFilename = videoFilename            

    def getProcessVideoDir(self):
        return self.processVideoDir
    
    def setProcessVideoDir(self, processVideoDir):
        self.processVideoDir = processVideoDir              

    def getprocessVideoFiles(self):
        return self.processVideoFiles
    
    def setProcessVideoFiles(self, processVideoFiles):
        self.processVideoFiles = processVideoFiles               
            
    def run(self):
        # Load the config containing all paths and the general config file
        self.log.info("video.run(): Starting Video creation process")
        
        if self.videoUtils.isCreationAllowed() == False:
            self.log.info("video.run(): " + _("Video creation is currently not allowed for the source"))
        else:
            self.log.info("video.run(): " + _("Video creation allowed, starting the process"))
            if self.videoType == "videocustom" or self.videoType == "videopost":
                self.configSourceVideo.setConfig('cfgcustomactive', 'no')
                self.videoUtils.identifyCustomStartEnd()
                self.setVideoFilename(self.getScriptStartTime().strftime("%Y%m%d") + "_" + self.configSourceVideo.getConfig('cfgcustomvidname'))

            self.setProcessVideoDir(self.dirCurrentSourcePictures + "process-" + self.videoType + "/")
            self.setProcessVideoFiles(self.dirCurrentSourcePictures + "process-" + self.videoType + "/20*.jpg")
            
            self.videoUtils.prepareVideoDirectory(self.getProcessVideoDir())
            filesCopied = self.videoUtils.copyFilesToVideoDirectory()            
            self.currentVideoDetails.setVideoValue('sourceFiles', filesCopied)

            if filesCopied > 0:
                for scanPictureFile in sorted(os.listdir(self.getProcessVideoDir()), reverse=True):															
                    if self.fileUtils.CheckJpegFile(self.getProcessVideoDir() + scanPictureFile) == True:
                        self.log.info("video.run(): " + _("---------------------------------------------------------------------------------"))
                        if self.videoType == "videopost" and self.configSourceVideo.getConfig('cfgtransitionactivate') != "yes":
                            if self.configSourceVideo.getConfig('cfgrotateactivate') == "yes" or self.configSourceVideo.getConfig('cfgcropactivate') == "yes" or self.configSourceVideo.getConfig('cfgvideosizeactivate') == "yes" or self.configSourceVideo.getConfig('cfgwatermarkactivate') == "yes" or self.configSourceVideo.getConfig('cfgvideopreimagemagicktxt') == "yes" or self.configSourceVideo.getConfig('cfgvideoeffect') != "no" or self.configSourceVideo.getConfig('cfgthumbnailactivate') != "no":
                                self.videoUtils.modifyPicturesPost(self.getProcessVideoDir() + scanPictureFile)                                
                            if self.configSourceVideo.getConfig("cfgmovefilestosource") != "no":
                                    # Verifier si une autre image existe, si oui, ne pas remplacer
                                    self.sourceDestinationDirectory = self.dirSources + 'source' + self.configSourceVideo.getConfig("cfgmovefilestosource") +'/' + self.configPaths.getConfig('parameters')['dir_source_pictures'] + scanPictureFile[0:8] + "/"                                  
                                    self.fileUtils.CheckDir(self.sourceDestinationDirectory)
                                    if os.path.exists(self.sourceDestinationDirectory + scanPictureFile):
                                        self.log.info("video.run(): " + _("Error: File already exists %(DestinationFile)s") % {'DestinationFile': self.sourceDestinationDirectory + scanPictureFile} )
                                    else:
                                        self.log.info("video.run(): " + _("Copy file to: %(DestinationFile)s") % {'DestinationFile': self.sourceDestinationDirectory + scanPictureFile} )
                                        shutil.copy(self.getProcessVideoDir() + scanPictureFile, self.sourceDestinationDirectory + scanPictureFile)
                                        if self.configSourceVideo.getConfig("cfgvidminintervalvalue") == "0":
                                            os.remove(self.getProcessVideoDir() + scanPictureFile)
                        elif self.videoType == "videocustom" or self.videoType == "video": 
                            self.videoUtils.modifyPictures(self.getProcessVideoDir() + scanPictureFile)
                            CreationError = False					
                    else:
                        self.log.info("video.run(): " + _("Video: %(VideoType)s: Picture format incorrect, deleting ....") % {'VideoType': self.videoType} )
                        if os.path.isfile(self.getProcessVideoDir() + scanPictureFile):
                            os.remove(self.getProcessVideoDir() + scanPictureFile)				


                #Apply transition effect (if enabled)
                if self.videoType == "videopost" and self.configSourceVideo.getConfig('cfgtransitionactivate') == "yes":
                    self.videoUtils.transitionPictures()

                self.log.info("video.run(): " + _("All pictures have been copied to target directory") % {'VideoType': self.videoType} )

                for videoformats in self.configGeneral.getConfig('cfgvideoformats'):
                    self.log.info("video.run(): " + _("Starting to process video format: %(videoformats)s") % {'videoformats': videoformats} )
                    formatDictionary = {}
                    formatDictionary['name'] = videoformats
                    formatStartTime = self.timeUtils.getCurrentSourceTime(self.configSource)
                    if self.configSourceVideo.getConfig("cfgvideocodecH264" + videoformats + "create") == "yes" and self.videoType != "videopost":
                        TargetVideoFilename = self.videoUtils.createVideos(videoformats)  
                        if TargetVideoFilename != False:
                            self.log.info("video.run(): " + _("Processing completed for: %(TargetVideoFilename)s") % {'TargetVideoFilename': TargetVideoFilename} )
                            if os.path.isfile(self.dirCurrentSourceVideos + TargetVideoFilename):
                                formatDictionary['avi'] = os.path.getsize(self.dirCurrentSourceVideos + TargetVideoFilename)
                            if os.path.isfile(self.dirCurrentSourceVideos + TargetVideoFilename + ".mp4"):
                                formatDictionary['mp4'] = os.path.getsize(self.dirCurrentSourceVideos + TargetVideoFilename + ".mp4")                            
                            self.videoUtils.sendVideos(TargetVideoFilename, videoformats)
                            if self.videoType == "videocustom" and self.configSourceVideo.getConfig("cfgvideoemailactivate") == "yes":
                                self.videoEmails.sendVideoSuccess(TargetVideoFilename)
                        else:
                            self.log.error("video.run(): " + _("Error for creating video for format: %(videoformats)s") % {'videoformats': videoformats} )   
                    formatEndTime = self.timeUtils.getCurrentSourceTime(self.configSource)
                    totalProcessingTime = int((formatEndTime-formatStartTime).total_seconds()*1000)
                    formatDictionary['runtime'] = totalProcessingTime
                    self.currentVideoDetails.addFormat(formatDictionary)
                                                        
                self.log.info("video.run(): " + _("Video processing completed"))
            else: 
                self.log.info("video.run(): " + _("No files available for processing, exiting"))

            scriptEndDate = self.timeUtils.getCurrentSourceTime(self.configSource)
            totalCaptureTime = int((scriptEndDate-self.getScriptStartTime()).total_seconds()*1000)
            self.log.info("video.run(): " + _("Video: Overall processing time: %(TotalCaptureTime)s ms") % {'TotalCaptureTime': str(totalCaptureTime)} )
            self.currentVideoDetails.setVideoValue('scriptEndDate', scriptEndDate.isoformat())
            self.currentVideoDetails.setVideoValue('scriptRuntime', totalCaptureTime)            
            self.currentVideoDetails.archiveVideoFile()
            self.log.info("video.run(): " + _("-----------------------------------------------------------------------"))
            
