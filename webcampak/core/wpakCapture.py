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
from builtins import object
import os
import time
import gettext

from .wpakConfigObj import Config
from .wpakFileUtils import fileUtils
from .wpakTimeUtils import timeUtils
from .wpakTransferUtils import transferUtils
from .wpakPhidgetsUtils import phidgetsUtils

from .capture.wpakCaptureUtils import captureUtils
from .capture.wpakCaptureEmails import captureEmails
from .capture.wpakCaptureObj import captureObj
from .capture.wpakSensorsObj import sensorsObj

from .capture.drivers.wpakCaptureGphoto import captureGphoto
from .capture.drivers.wpakCaptureIPCam import captureIPCam
from .capture.drivers.wpakCaptureWebfile import captureWebfile
from .capture.drivers.wpakCaptureTestPicture import captureTestPicture
from .capture.drivers.wpakCaptureWpak import captureWpak
from .capture.drivers.wpakCaptureRtsp import captureRtsp
from .capture.drivers.wpakCapturePhidget import capturePhidget

from .wpakPictureTransformations import pictureTransformations
from .wpakFTPUtils import FTPUtils


# This class is used to capture a picture or sensors from a source
class Capture(object):
    """ This class is used to capture from a source
    
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
        self.currentSourceId = sourceId
        self.setSourceId(sourceId)

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
        self.dirCurrentSource = self.dirSources + 'source' + self.currentSourceId + '/'
        self.dirCurrentSourceTmp = self.dirSources + 'source' + self.currentSourceId + '/' + \
                                   self.configPaths.getConfig('parameters')['dir_source_tmp']
        self.dirCurrentSourceCapture = self.dirSources + 'source' + self.currentSourceId + '/' + self.dirSourceCapture
        self.dirCurrentSourcePictures = self.dirSources + 'source' + self.currentSourceId + '/' + \
                                        self.configPaths.getConfig('parameters')['dir_source_pictures']
        self.dirCurrentSourceLogs = self.dirLogs + 'source' + self.currentSourceId + '/'

        self.setupLog()
        self.log.info("===START===")
        self.log.info("capture(): Start")

        self.configGeneral = Config(self.log, self.dirConfig + 'config-general.cfg')
        self.configSource = Config(self.log, self.dirEtc + 'config-source' + str(self.getSourceId()) + '.cfg')
        self.configSourceFTP = Config(self.log,
                                      self.dirEtc + 'config-source' + str(self.currentSourceId) + '-ftpservers.cfg')

        self.dirCurrentLocaleMessages = self.dirLocale + self.configSource.getConfig(
            'cfgsourcelanguage') + "/" + self.dirLocaleMessage

        self.initGetText(self.dirLocale, self.configGeneral.getConfig('cfgsystemlang'),
                         self.configGeneral.getConfig('cfggettextdomain'))

        self.timeUtils = timeUtils(self)
        self.fileUtils = fileUtils(self)
        self.phidgetsUtils = phidgetsUtils(self)
        self.FTPUtils = FTPUtils(self)
        self.transferUtils = transferUtils(self)

        self.setScriptStartTime(self.timeUtils.getCurrentSourceTime(self.configSource))

        # By default, the picture date corresponds to the time the script started
        self.log.info("capture(): " + _("Set Capture Time to script start time (default at script startup)"))
        self.setCaptureTime(self.getScriptStartTime())

        fileCaptureDetails = self.dirSources + 'source' + self.currentSourceId + '/' + self.dirSourceLive + 'last-capture.json'
        fileCaptureLog = self.dirCurrentSourceCapture + self.getCaptureTime().strftime("%Y%m%d") + ".jsonl"

        self.log.info("capture(): " + _("Create Capture Status object and set script start date"))
        self.currentCaptureDetails = captureObj(self.log, fileCaptureLog)
        self.currentCaptureDetails.setCaptureFile(fileCaptureDetails)
        self.currentCaptureDetails.setCaptureValue('scriptStartDate', self.getScriptStartTime().isoformat())

        self.log.info("capture(): " + _("Load previous Capture Status Object (if available)"))
        self.lastCaptureDetails = captureObj(self.log)
        self.lastCaptureDetails.setCaptureFile(fileCaptureDetails)
        self.lastCaptureDetails.loadCaptureFile()

        self.captureUtils = captureUtils(self)
        self.captureEmails = captureEmails(self)
        self.pictureTransformations = pictureTransformations(self)
        self.captureUtils.setPictureTransformations(self.pictureTransformations)

        self.log.info("capture(): " + _("Initializing the following capture driver: %(captureDriver)s") % {
            'captureDriver': self.configSource.getConfig('cfgsourcetype')})
        if self.configSource.getConfig('cfgsourcetype') == "gphoto":
            # If the source is a gphoto camera
            self.captureDriver = captureGphoto(self)
        elif self.configSource.getConfig('cfgsourcetype') == "testpicture":
            # The source is using a test picture, randomly modified
            self.captureDriver = captureTestPicture(self)
        elif self.configSource.getConfig('cfgsourcetype') == "ipcam" or (
                self.configSource.getConfig('cfgsourcetype') == "wpak" and self.configSource.getConfig(
                'cfgsourcewpaktype') == "rec"):
            # If the source is an IP Camera
            self.captureDriver = captureIPCam(self)
        elif self.configSource.getConfig('cfgsourcetype') == "webfile":
            # If the source is a Web File
            self.captureDriver = captureWebfile(self)
        elif self.configSource.getConfig('cfgsourcetype') == "wpak" and self.configSource.getConfig(
                'cfgsourcewpaktype') == "get":
            # If the source is another source of the same Webcampak
            self.captureDriver = captureWpak(self)
        elif self.configSource.getConfig('cfgsourcetype') == "rtsp":
            # If the source is a RTSP stream
            self.captureDriver = captureRtsp(self)

        self.captureFilename = None

    def setupLog(self):
        """ Setup logging to file"""
        if not os.path.exists(self.dirCurrentSourceLogs):
            os.makedirs(self.dirCurrentSourceLogs)
        logFilename = self.dirCurrentSourceLogs + "capture.log"
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

    # Setters and Getters
    def setScriptStartTime(self, scriptStartTime):
        self.log.info("capture.setScriptStartTime(): " + _("Script Start Time set to: %(scriptStartTime)s") % {
            'scriptStartTime': scriptStartTime.isoformat()})
        self.scriptStartTime = scriptStartTime

    def getScriptStartTime(self):
        return self.scriptStartTime

    def setCaptureFilename(self, captureFilename):
        self.captureFilename = captureFilename

    def getCaptureFilename(self):
        return self.captureFilename

    def setSourceId(self, sourceId):
        self.sourceId = sourceId

    def getSourceId(self):
        return self.sourceId

    def setCaptureTime(self, captureTime=None):
        if captureTime == None:
            self.captureTime = self.timeUtils.getCurrentSourceTime(self.configSource)
        else:
            self.captureTime = captureTime
        self.log.info("capture.setCaptureTime(): " + _("Capture Time set to: %(captureTime)s") % {
            'captureTime': str(self.captureTime)})
        return self.captureTime

    def getCaptureTime(self):
        return self.captureTime

    def run(self):
        """ Initiate the capture process for the source """
        self.log.info("capture.run(): " + _("Initiate capture process for source: %(currentSourceId)s") % {
            'currentSourceId': str(self.sourceId)})

        # There might be a need to delay the capture by a couple of seconds
        if self.configSource.getConfig('cfgcapturedelay') != "0":
            self.log.info("capture.run(): " + _("Delaying capture by %(CaptureDelay)s seconds.") % {
                'CaptureDelay': str(self.configSource.getConfig('cfgcapturedelay'))})
            time.sleep(int(self.configSource.getConfig('cfgcapturedelay')))
            if self.configSource.getConfig('cfgcapturedelaydate') != "script":
                self.setCaptureTime()

        if self.configSource.getConfig('cfgnocapture') == "yes":
            self.log.info("capture.run(): " + _("Capture manually disabled via administration panel"))
        elif self.configSource.getConfig('cfgsourceactive') != "yes":
            self.log.info("capture.run(): " + _("Source is not active, not proceeding with capture"))
        elif self.captureUtils.isWithinTimeframe() == False:
            self.log.info("capture.run(): " + _("Capture calendar is active but capture not in the correct timeframe"))
        elif self.captureUtils.checkInterval() == False:
            self.log.info("capture.run(): " + _("Not enough time since last picture was captured, not proceeding"))
        else:
            # Capture the picture and return an array containing one or more files to be processed
            # If multiple files are being processed, the captureDate value is the one of the latest picture captured
            capturedPictures = self.captureDriver.capture()

            # Used to count the number of times pictures are being processed, 
            # since we only want to generate hotlink images once per capture cycle  
            processedPicturesCount = 0
            if capturedPictures != False:
                for currentPicture in capturedPictures:
                    self.log.info("capture.run(): " + _("Begin processing of picture: %(currentPicture)s") % {
                        'currentPicture': currentPicture})

                    # Set picture filename
                    self.setCaptureFilename(os.path.splitext(os.path.basename(currentPicture))[0])
                    self.pictureTransformations.setFilesourcePath(currentPicture)
                    self.pictureTransformations.setFiledestinationPath(currentPicture)

                    # Process pictures (crop, resize, watermark, legend, ...)
                    if processedPicturesCount == 0 or self.configSource.getConfig(
                            'cfgsourcecamiplimiterotation') != "yes":
                        self.captureUtils.modifyPictures(True)
                    else:  # Only generate the hotlink for the first picture being processed
                        self.captureUtils.modifyPictures(False)

                        # Copy pictures to live/ directory as last-capture.jpg or last-capture.raw
                    if self.configSource.getConfig('cfghotlinkmax') != "no":
                        self.captureUtils.createLivePicture(self.getCaptureFilename())

                    # Archive picture to its definitive location
                    self.captureUtils.archivePicture(self.getCaptureFilename())

                    # Create hotlinks and send those by FTP if enabled
                    self.captureUtils.generateHotlinks()

                    # Send file to first remote FTP Server
                    self.captureUtils.sendPicture(self.configSource.getConfig('cfgftpmainserverid'),
                                                  self.configSource.getConfig('cfgftpmainserverretry'),
                                                  self.configSource.getConfig('cfgftpmainserverraw'),
                                                  self.captureFilename)

                    # Send file to second remote FTP Server
                    self.captureUtils.sendPicture(self.configSource.getConfig('cfgftpsecondserverid'),
                                                  self.configSource.getConfig('cfgftpsecondserverretry'),
                                                  self.configSource.getConfig('cfgftpsecondserverraw'),
                                                  self.captureFilename)

                    # Copy file to first internal source
                    if self.configSource.getConfig('cfgcopymainenable') == "yes":
                        self.captureUtils.copyPicture(self.configSource.getConfig('cfgcopymainsourceid'),
                                                      self.configSource.getConfig('cfgcopymainsourceraw'),
                                                      self.captureFilename)

                    # Copy file to second internal source
                    if self.configSource.getConfig('cfgcopysecondenable') == "yes":
                        self.captureUtils.copyPicture(self.configSource.getConfig('cfgcopysecondsourceid'),
                                                      self.configSource.getConfig('cfgcopysecondsourceraw'),
                                                      self.captureFilename)

                    # Automtically purge old pictures
                    self.captureUtils.purgePictures(self.getCaptureFilename())

                    storedJpgSize = self.captureUtils.getArchivedSize(self.getCaptureFilename(), "jpg")
                    storedRawSize = self.captureUtils.getArchivedSize(self.getCaptureFilename(), "raw")
                    self.currentCaptureDetails.setCaptureValue('storedJpgSize',
                                                               self.currentCaptureDetails.getCaptureValue(
                                                                   'storedJpgSize') + storedJpgSize)
                    self.currentCaptureDetails.setCaptureValue('storedRawSize',
                                                               self.currentCaptureDetails.getCaptureValue(
                                                                   'storedRawSize') + storedRawSize)
                    self.currentCaptureDetails.setCaptureValue('totalCaptureSize',
                                                               self.currentCaptureDetails.getCaptureValue(
                                                                   'totalCaptureSize') + int(
                                                                   storedJpgSize + storedRawSize))
                    processedPicturesCount = processedPicturesCount + 1

                self.log.info("capture.run(): " + _("Capture process completed"))
                self.currentCaptureDetails.setCaptureValue('captureSuccess', True)
                if os.path.isfile(self.dirCache + "source" + self.currentSourceId + "-errorcount"):
                    os.remove(self.dirCache + "source" + self.currentSourceId + "-errorcount")
            else:
                self.log.info("capture.run(): " + _("Unable to capture picture"))
                self.captureUtils.generateFailedCaptureHotlink()
                self.currentCaptureDetails.setCaptureValue('captureSuccess', False)
                self.captureUtils.setCustomCounter('errorcount', int(self.captureUtils.getCustomCounter('errorcount')) + 1)

            if self.configSource.getConfig('cfgcapturedeleteafterdays') != "0":
                # Purge old pictures (by day)
                self.captureUtils.deleteOldPictures()
            if self.configSource.getConfig('cfgcapturemaxdirsize') != "0":
                # Purge old pictures (by size)
                self.captureUtils.deleteOverSize()

            if self.configGeneral.getConfig('cfgstatsactivate') == "yes":
                self.captureUtils.sendUsageStats()

            # if self.configSource.getConfig('cfgemailcapturestats') == "yes":
            #    self.captureEmails.sendCaptureStats()

            sensorFilename = self.getCaptureTime().strftime("%Y%m%d") + "-sensors.jsonl"
            fileCaptureLog = self.dirCurrentSourcePictures + self.getCaptureTime().strftime("%Y%m%d") + "/" + sensorFilename
            if self.configGeneral.getConfig('cfgphidgetactivate') == "yes" and self.configSource.getConfig(
                    'cfgphidgetactivate') == "yes":
                capturedSensors = capturePhidget(self).capture()
                currentSensorsDetails = sensorsObj(self.log, fileCaptureLog)
                currentSensorsDetails.setSensorsValue('date', self.getCaptureTime().isoformat())
                currentSensorsDetails.setSensorsValue('sensors', capturedSensors)
                # Record capture interval
                sourceCaptureInterval = int(self.configSource.getConfig('cfgcroncapturevalue'))
                if self.configSource.getConfig('cfgcroncaptureinterval') == "minutes":
                    sourceCaptureInterval = int(self.configSource.getConfig('cfgcroncapturevalue')) * 60
                currentSensorsDetails.setSensorsValue('interval', sourceCaptureInterval)
                currentSensorsDetails.archiveSensorsFile()

            #If the phidget sensor file exists, it is being sent throughout the chain.
            if (os.path.isfile(fileCaptureLog)):
                # Send file to first remote FTP Server
                self.captureUtils.sendSensor(self.configSource.getConfig('cfgftpmainserverid'),
                                              self.configSource.getConfig('cfgftpmainserverretry'),
                                              sensorFilename)

                # Send file to second remote FTP Server
                self.captureUtils.sendSensor(self.configSource.getConfig('cfgftpsecondserverid'),
                                              self.configSource.getConfig('cfgftpsecondserverretry'),
                                              sensorFilename)

                # Copy file to first internal source
                if self.configSource.getConfig('cfgcopymainenable') == "yes":
                    self.captureUtils.copySensor(self.configSource.getConfig('cfgcopymainsourceid'),
                                                  sensorFilename)

                # Copy file to second internal source
                if self.configSource.getConfig('cfgcopysecondenable') == "yes":
                    self.captureUtils.copySensor(self.configSource.getConfig('cfgcopysecondsourceid'),
                                                  sensorFilename)

            scriptEndDate = self.timeUtils.getCurrentSourceTime(self.configSource)
            totalCaptureTime = int((scriptEndDate - self.getScriptStartTime()).total_seconds() * 1000)
            self.log.info("capture.run(): " + _("Capture: Overall capture time: %(TotalCaptureTime)s ms") % {
                'TotalCaptureTime': str(totalCaptureTime)})
            self.currentCaptureDetails.setCaptureValue('scriptEndDate', scriptEndDate.isoformat())
            self.currentCaptureDetails.setCaptureValue('scriptRuntime', totalCaptureTime)
            self.currentCaptureDetails.setCaptureValue('processedPicturesCount', processedPicturesCount)

            # Two different files are being stored here:
            # - The last-capture file, which is only being stored id the capture is successful
            # - The capture archive, which contains all capture requests (successful or not)
            if capturedPictures != False:
                self.currentCaptureDetails.writeCaptureFile()
            self.currentCaptureDetails.archiveCaptureFile()
            self.log.info(
                "capture.run(): " + _("-----------------------------------------------------------------------"))
        self.log.info("===END===")
