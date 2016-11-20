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
import dateutil.parser
import time
import gettext
import json
import rrdtool

from wpakConfigObj import Config
from wpakFileUtils import fileUtils
from wpakTimeUtils import timeUtils
from wpakTransferUtils import transferUtils

from wpakFTPUtils import FTPUtils


# This class is used to generate a RRD graph from a source
class statsRrd(object):
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
        self.log.info("statsRrd(): Start")

        self.configGeneral = Config(self.log, self.dirConfig + 'config-general.cfg')
        self.configSource = Config(self.log, self.dirEtc + 'config-source' + str(self.currentSourceId) + '.cfg')
        self.configSourceFTP = Config(self.log,
                                      self.dirEtc + 'config-source' + str(self.currentSourceId) + '-ftpservers.cfg')

        self.dirCurrentLocaleMessages = self.dirLocale + self.configSource.getConfig(
            'cfgsourcelanguage') + "/" + self.dirLocaleMessage

        self.initGetText(self.dirLocale, self.configGeneral.getConfig('cfgsystemlang'),
                         self.configGeneral.getConfig('cfggettextdomain'))

        self.timeUtils = timeUtils(self)
        self.fileUtils = fileUtils(self)
        self.FTPUtils = FTPUtils(self)
        self.transferUtils = transferUtils(self)

    def setupLog(self):
        """ Setup logging to file"""
        if not os.path.exists(self.dirCurrentSourceLogs):
            os.makedirs(self.dirCurrentSourceLogs)
        logFilename = self.dirCurrentSourceLogs + "statsrrd.log"
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
        self.log.debug("statsrrd.initGetText(): Start")
        try:
            t = gettext.translation(cfggettextdomain, dirLocale, [cfgsystemlang], fallback=True)
            _ = t.ugettext
            t.install()
            self.log.info("statsrrd.initGetText(): " + _(
                "Initialized gettext with Domain: %(cfggettextdomain)s - Language: %(cfgsystemlang)s - Path: %(dirLocale)s")
                          % {'cfggettextdomain': cfggettextdomain, 'cfgsystemlang': cfgsystemlang,
                             'dirLocale': dirLocale})
        except:
            self.log.error("No translation file available")

    def run(self):
        """ Initiate rrd graph creation for the source """
        if self.configSource.getConfig('cfgphidgetsensorsgraph') == "yes" and self.configSource.getConfig(
                'cfgsourceactive') == "yes":
            self.log.info("statsrrd.run(): " + _("Initiate RRD Graph creation for source: %(currentSourceId)s") % {
                'currentSourceId': str(self.currentSourceId)})

            # List Capture files contained in the directory
            allSensorsFiles = []
            for dirpath, dirnames, filenames in os.walk(self.dirCurrentSourcePictures):
                for filename in [f for f in filenames if f.endswith("sensors.jsonl")]:
                    allSensorsFiles.append(os.path.join(dirpath, filename))
            allSensorsFiles.sort(reverse=True)

            processedCpt = 0
            for currentCaptureFile in allSensorsFiles:
                self.log.info("statsrrd.run(): " + _("Processing: %(currentCaptureFile)s") % {
                    'currentCaptureFile': currentCaptureFile})
                processedCpt = processedCpt + 1

                # List all sensors contained in the file
                sensors = self.getSensorsFromFile(currentCaptureFile)
                sensorsDay = self.getSensorDayFromFile(currentCaptureFile)
                captureInterval = self.getCaptureIntervalFromFile(currentCaptureFile)
                if captureInterval != None:
                    self.log.info("statsrrd.run(): " + _("Capture interval: %(captureInterval)s seconds") % {'captureInterval': captureInterval})

                    # {"scriptEndDate": "2016-09-29T04:59:43.956108+02:00", "totalCaptureSize": 10945697, "captureSuccess": true, "scriptRuntime": 2531, "storedRawSize": 0
                    # , "scriptStartDate": "2016-09-29T04:59:41.424850+02:00", "processedPicturesCount": 1, "storedJpgSize": 10945697, "captureDate": "2016-09-29T04:59:41.472365+02:00"
                    # , "sensors": {"789275965fe98d9ad9275648a21b095982d673a189f5cb3fad8155f9": {"type": "Temperature", "legend": "Outside Tempe abcd", "value": 25.8, "valueRaw": 1601}, "574eb9c9ee7e0bbe610a7aab0e359864fdd7810d113edee1da80a5af": {"type": "Temperature", "legend": "Inside Temperature", "value": 25.8, "valueRaw": 1601}, "fbdde0c3fe0b6aecc5f1027262ec79813f2cf77c9361642c4a7d57a3": {"type": "Luminosity", "legend": "Humidity", "value": 460.8, "valueRaw": 1887}}}

                    for currentSensor in sensors:
                        if os.path.isfile(self.dirCurrentSourcePictures + sensorsDay + "/sensor-" + currentSensor + ".rrd") == False or processedCpt <= 1:
                            self.log.info("statsrrd.run(): " + _("Currently processing Sensor: %(currentSensor)s") % {
                                'currentSensor': currentSensor})

                            ValueTable = {}
                            SensorLegend = "UNAVAILABLE"
                            SensorColor = "#FF0000"
                            for line in open(currentCaptureFile).readlines():
                                try:
                                    currentCaptureLine = json.loads(line)
                                except Exception:
                                    self.log.error("statsrrd.run(): Unable to decode JSON line: " + line)
                                    break
                                sensorDate = dateutil.parser.parse(currentCaptureLine['date'])
                                currentTimestamp = int(time.mktime(sensorDate.timetuple()))
                                ValueTable[currentTimestamp] = "NaN"
                                if 'sensors' in currentCaptureLine:
                                    if currentCaptureLine['sensors'] != None:
                                        if currentSensor in currentCaptureLine['sensors']:
                                            ValueTable[currentTimestamp] = currentCaptureLine['sensors'][currentSensor][
                                                'value']
                                            SensorLegend = currentCaptureLine['sensors'][currentSensor]['legend']
                                            if 'color' in currentCaptureLine['sensors'][currentSensor]:
                                                SensorColor = currentCaptureLine['sensors'][currentSensor]['color']

                            ValueTableKeys = ValueTable.keys()
                            ValueTableKeys.sort()

                            self.log.info("statsrrd.run(): " + _("Preparing the RRD base file: %(SensorRRDFile)s") % {
                                'SensorRRDFile': str(
                                    self.dirCurrentSourcePictures + sensorsDay + "/sensor-" + currentSensor + ".rrd")})

                            rrdstart = str(int(min(ValueTableKeys)))
                            # rrdstart = str(int(min(ValueTableKeys)))
                            rrdend = str(max(ValueTableKeys))
                            ret = rrdtool.create(
                                str(self.dirCurrentSourcePictures + str(sensorsDay) + "/sensor-" + currentSensor + ".rrd") \
                                , "--step", str(captureInterval) \
                                , "--start" \
                                , rrdstart \
                                , "DS:GRAPHAREA:GAUGE:600:U:U" \
                                , "RRA:AVERAGE:0.5:1:" + str(len(ValueTable)))

                            for i in xrange(len(ValueTableKeys)):
                                self.log.info("statsrrd.run(): " + _(
                                    "Adding Timestamp: %(currentTimestamp)s - Value: %(currentValue)s") % {
                                                  'currentTimestamp': str(ValueTableKeys[i]),
                                                  'currentValue': str(ValueTable[ValueTableKeys[i]]),})
                                if i == 0:
                                    currentTimestamp = int(ValueTableKeys[i])
                                else:
                                    currentTimestamp = currentTimestamp + captureInterval
                                    ret = rrdtool.update(str(self.dirCurrentSourcePictures + str(
                                        sensorsDay) + "/sensor-" + currentSensor + ".rrd"),
                                                         str(int(currentTimestamp)) + ':' + str(
                                                             ValueTable[ValueTableKeys[i]]))

                            ret = rrdtool.graph(
                                str(self.dirCurrentSourcePictures + str(sensorsDay) + "/sensor-" + currentSensor + ".png") \
                                , "--start" \
                                , rrdstart \
                                , "--end" \
                                , rrdend \
                                , "--vertical-label=" + str(SensorLegend) \
                                , "DEF:GRAPHAREA=" + str(self.dirCurrentSourcePictures + str(
                                    sensorsDay) + "/sensor-" + currentSensor + ".rrd") + ":GRAPHAREA:AVERAGE" \
                                , "AREA:GRAPHAREA" + str(SensorColor) + ":" + str(SensorLegend))

                            self.log.info("statsrrd.run(): " + _("PNG Graph created: %(pnggraph)s") % {'pnggraph': str(self.dirCurrentSourcePictures + str(sensorsDay) + "/sensor-" + currentSensor + ".png")})

                            if self.configSource.getConfig('cfgftpphidgetserverid') != "":
                                currentTime = self.timeUtils.getCurrentSourceTime(self.configSource)
                                self.transferUtils.transferFile(currentTime, self.dirCurrentSourcePictures + str(
                                    sensorsDay) + "/sensor-" + currentSensor + ".rrd", "sensor-" + currentSensor + ".rrd",
                                                                self.configSource.getConfig('cfgftpphidgetserverid'),
                                                                self.configSource.getConfig('cfgftpphidgetserverretry'))
                                self.transferUtils.transferFile(currentTime, self.dirCurrentSourcePictures + str(
                                    sensorsDay) + "/sensor-" + currentSensor + ".png", "sensor-" + currentSensor + ".png",
                                                                self.configSource.getConfig('cfgftpphidgetserverid'),
                                                                self.configSource.getConfig('cfgftpphidgetserverretry'))

        else:
            self.log.info(
                "statsrrd.run(): " + _("Creation of the RRD Graph disabled for source: %(currentSourceId)s") % {
                    'currentSourceId': str(self.currentSourceId)})

    def getSensorsFromFile(self, currentCaptureFile):
        """ Scan a file to identify all sensor values it contains
            Args:
                None

            Returns:
                Dict: number of occurence for each of the sensors contained in the file
        """
        self.log.debug("statsrrd.getSensorsFromFile(): " + _("Start"))
        sensors = {}
        for line in open(currentCaptureFile).readlines():
            # currentCaptureLine = json.loads(line, object_pairs_hook=OrderedDict)
            try:
                currentCaptureLine = json.loads(line)
            except Exception:
                self.log.error("statsrrd.getSensorsFromFile(): Unable to decode JSON line: " + line)
                break
            if 'sensors' in currentCaptureLine:
                if currentCaptureLine['sensors'] != None:
                    # print currentCaptureLine['sensors']
                    for sensorId in currentCaptureLine['sensors']:
                        if sensorId in sensors:
                            sensors[sensorId] += 1
                        else:
                            sensors[sensorId] = 1
        return sensors

    def getSensorDayFromFile(self, currentCaptureFile):
        """ Scan a file and returns its day
            Args:
                None

            Returns:
                String: YYYYMMDD date
        """
        self.log.debug("statsrrd.getDayFromFile(): " + _("Start"))
        date = None
        for line in open(currentCaptureFile).readlines():
            try:
                currentSensorLine = json.loads(line)
            except Exception:
                self.log.error("statsrrd.getSensorDayFromFile(): Unable to decode JSON line: " + line)
                break
            if 'date' in currentSensorLine:
                currentSensorDate = dateutil.parser.parse(currentSensorLine['date'])
                return currentSensorDate.strftime("%Y%m%d")
        return date

    def getCaptureIntervalFromFile(self, currentCaptureFile):
        """ Scan a file and returns the capture interval used for the capture
            Args:
                None

            Returns:
                Number: Capture interval in seconds
        """
        self.log.debug("statsrrd.getCaptureIntervalFromFile(): " + _("Start"))
        date = None
        for line in open(currentCaptureFile).readlines():
            try:
                currentSensorLine = json.loads(line)
            except Exception:
                self.log.error("statsrrd.getCaptureIntervalFromFile(): Unable to decode JSON line: " + line)
                break
            if 'interval' in currentSensorLine:
                return currentSensorLine['interval']
        return date
