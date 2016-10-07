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
import datetime
import random
import time
import gettext
from dateutil import tz
from collections import OrderedDict
import json
from os.path import basename
import rrdtool

from wpakConfigObj import Config
from wpakFileUtils import fileUtils
from wpakTimeUtils import timeUtils
from wpakTransferUtils import transferUtils
from wpakPhidgetsUtils import phidgetsUtils

from capture.wpakCaptureUtils import captureUtils
from capture.wpakCaptureEmails import captureEmails
from capture.wpakCaptureObj import captureObj

from capture.drivers.wpakCaptureGphoto import captureGphoto
from capture.drivers.wpakCaptureIPCam import captureIPCam
from capture.drivers.wpakCaptureWebfile import captureWebfile
from capture.drivers.wpakCaptureTestPicture import captureTestPicture
from capture.drivers.wpakCaptureWpak import captureWpak
from capture.drivers.wpakCaptureRtsp import captureRtsp
from capture.drivers.wpakCapturePhidget import capturePhidget

from wpakPictureTransformations import pictureTransformations
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
        self.dirCurrentSource = self.dirSources + 'source' + self.currentSourceId +'/'        
        self.dirCurrentSourceTmp = self.dirSources + 'source' + self.currentSourceId +'/' + self.configPaths.getConfig('parameters')['dir_source_tmp']
        self.dirCurrentSourceCapture = self.dirSources + 'source' + self.currentSourceId +'/' + self.dirSourceCapture       
        self.dirCurrentSourcePictures = self.dirSources + 'source' + self.currentSourceId +'/' + self.configPaths.getConfig('parameters')['dir_source_pictures']        
        self.dirCurrentSourceLogs = self.dirLogs + 'source' + self.currentSourceId +'/'        
                
        self.setupLog()
        self.log.info("===START===")
        self.log.info("statsRrd(): Start")
        
        self.configGeneral = Config(self.log, self.dirConfig + 'config-general.cfg')
        self.configSource = Config(self.log, self.dirEtc + 'config-source' + str(self.currentSourceId) + '.cfg')
        self.configSourceFTP = Config(self.log, self.dirEtc + 'config-source' + str(self.currentSourceId) + '-ftpservers.cfg')        

        self.dirCurrentLocaleMessages = self.dirLocale + self.configSource.getConfig('cfgsourcelanguage') + "/" + self.dirLocaleMessage

        self.initGetText(self.dirLocale, self.configGeneral.getConfig('cfgsystemlang'), self.configGeneral.getConfig('cfggettextdomain'))
                
        self.timeUtils = timeUtils(self)
        self.fileUtils = fileUtils(self)
        self.FTPUtils = FTPUtils(self)

    def setupLog(self):      
        """ Setup logging to file"""  
        if not os.path.exists(self.dirCurrentSourceLogs):
            os.makedirs(self.dirCurrentSourceLogs)  
        logFilename = self.dirCurrentSourceLogs + "statsrrd.log"
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
        self.log.debug("statsrrd.initGetText(): Start")
        try:
            t = gettext.translation(cfggettextdomain, dirLocale, [cfgsystemlang], fallback=True)
            _ = t.ugettext
            t.install()
            self.log.info("statsrrd.initGetText(): " + _("Initialized gettext with Domain: %(cfggettextdomain)s - Language: %(cfgsystemlang)s - Path: %(dirLocale)s")
                                                    % {'cfggettextdomain': cfggettextdomain, 'cfgsystemlang': cfgsystemlang, 'dirLocale': dirLocale} )        
        except:
            self.log.error("No translation file available")
            
    def run(self):
        """ Initiate rrd graph creation for the source """
        if self.configSource.getConfig('cfgphidgetsensorsgraph') == "yes":
            self.log.info("statsrrd.run(): " + _("Initiate RRD Graph creation for source: %(currentSourceId)s") % {'currentSourceId': str(self.currentSourceId)} )

            # List Capture files contained in the directory
            allCaptureFiles = []
            for dirpath, dirnames, filenames in os.walk(self.dirCurrentSourceCapture):
                for filename in [f for f in filenames if f.endswith(".jsonl")]:
                    allCaptureFiles.append(os.path.join(dirpath, filename))
            allCaptureFiles.sort(reverse=True)

            processedCpt = 0
            for currentCaptureFile in allCaptureFiles:
                self.log.info("statsrrd.run(): " + _("Processing: %(currentCaptureFile)s") % {'currentCaptureFile': currentCaptureFile} )
                processedCpt = processedCpt + 1

                #List all sensors contained in the file
                sensors = self.getSensorsFromFile(currentCaptureFile)

                #{"scriptEndDate": "2016-09-29T04:59:43.956108+02:00", "totalCaptureSize": 10945697, "captureSuccess": true, "scriptRuntime": 2531, "storedRawSize": 0
                # , "scriptStartDate": "2016-09-29T04:59:41.424850+02:00", "processedPicturesCount": 1, "storedJpgSize": 10945697, "captureDate": "2016-09-29T04:59:41.472365+02:00"
                # , "sensors": {"789275965fe98d9ad9275648a21b095982d673a189f5cb3fad8155f9": {"type": "Temperature", "legend": "Outside Tempe abcd", "value": 25.8, "valueRaw": 1601}, "574eb9c9ee7e0bbe610a7aab0e359864fdd7810d113edee1da80a5af": {"type": "Temperature", "legend": "Inside Temperature", "value": 25.8, "valueRaw": 1601}, "fbdde0c3fe0b6aecc5f1027262ec79813f2cf77c9361642c4a7d57a3": {"type": "Luminosity", "legend": "Humidity", "value": 460.8, "valueRaw": 1887}}}

                currentCaptureDay = os.path.splitext(basename(currentCaptureFile))[0]

                for currentSensor in sensors:
                    if os.path.isfile(self.dirCurrentSourcePictures + currentCaptureDay + "/sensor-" + currentSensor + ".rrd") == False or processedCpt <= 1:
                        self.log.info("statsrrd.run(): " + _("Currently processing Sensor: %(currentSensor)s") % {'currentSensor': currentSensor} )

                        ValueTable = {}
                        #ValueKeys = []
                        ValueTableKeys = []
                        ValueKeysDiff = []
                        ValueInsertTable = {}
                        if self.configSource.getConfig('cfgcroncaptureinterval') == "minutes":
                            DefinedInterval = int(self.configSource.getConfig('cfgcroncapturevalue')) * 60
                        elif self.configSource.getConfig('cfgcroncaptureinterval') == "seconds":
                            DefinedInterval = int(self.configSource.getConfig('cfgcroncapturevalue'))


                        SensorLegend = "UNAVAILABLE"
                        for line in open(currentCaptureFile).readlines():
                            currentCaptureLine = json.loads(line)
                            sensorDate = dateutil.parser.parse(currentCaptureLine['scriptStartDate'])
                            currentTimestamp = int(time.mktime(sensorDate.timetuple()))
                            ValueTable[currentTimestamp] = "NaN"
                            if 'sensors' in currentCaptureLine:
                                if currentCaptureLine['sensors'] != None:
                                    if currentSensor in currentCaptureLine['sensors']:
                                        ValueTable[currentTimestamp] = currentCaptureLine['sensors'][currentSensor]['value']
                                        SensorLegend = currentCaptureLine['sensors'][currentSensor]['legend']

                        ValueTableKeys = ValueTable.keys()
                        ValueTableKeys.sort()

                        self.log.info("statsrrd.run(): " + _("Preparing the RRD base file: %(SensorRRDFile)s") % {'SensorRRDFile': str(self.dirCurrentSourcePictures + currentCaptureDay + "/sensor-" + currentSensor + ".rrd")} )

                        rrdstart = str(int(min(ValueTableKeys)))
                        #rrdstart = str(int(min(ValueTableKeys)))
                        rrdend = str(max(ValueTableKeys))
                        ret = rrdtool.create(str(self.dirCurrentSourcePictures + str(currentCaptureDay) + "/sensor-" + currentSensor + ".rrd")\
                                             , "--step", str(DefinedInterval)\
                                             , "--start"\
                                             , rrdstart\
                                             , "DS:GRAPHAREA:GAUGE:600:U:U"\
                                             , "RRA:AVERAGE:0.5:1:" + str(len(ValueTable)))

                        for i in xrange(len(ValueTableKeys)):
                            self.log.info("statsrrd.run(): " + _("Adding Timestamp: %(currentTimestamp)s - Value: %(currentValue)s") % {'currentTimestamp': str(ValueTableKeys[i]), 'currentValue': str(ValueTable[ValueTableKeys[i]]), } )
                            if i == 0:
                                CurrentTimestamp = int(ValueTableKeys[i])
                            else:
                                CurrentTimestamp = CurrentTimestamp + DefinedInterval
                                ret = rrdtool.update(str(self.dirCurrentSourcePictures + str(currentCaptureDay) + "/sensor-" + currentSensor + ".rrd"), str(int(CurrentTimestamp)) + ':' + str(ValueTable[ValueTableKeys[i]]))

                        ret = rrdtool.graph(str(self.dirCurrentSourcePictures + str(currentCaptureDay) + "/sensor-" + currentSensor + ".png")\
                                            , "--start"\
                                            , rrdstart\
                                            , "--end"\
                                            , rrdend\
                                            , "--vertical-label="+ str(SensorLegend)\
                                            , "DEF:GRAPHAREA=" + str(self.dirCurrentSourcePictures + str(currentCaptureDay) + "/sensor-" + currentSensor + ".rrd") + ":GRAPHAREA:AVERAGE" \
                                            , "AREA:GRAPHAREA#FF0000:" + str(SensorLegend))

            """
            cptdir = 0
            for listpictdir in sorted(os.listdir(self.Cfgpictdir), reverse=True): # Browse all directories
                if listpictdir[:2] == "20" and os.path.isdir(self.Cfgpictdir + listpictdir):
                    cptdir = cptdir + 1
                    self.Debug.Display(_("Graph: RRD: Processing %(CurrentDirectory)s directory") % {'CurrentDirectory': str(listpictdir)} )
                    if os.path.isfile(self.Cfgpictdir + listpictdir + "/" + self.G.getConfig('cfgphidgetcapturefile')):
                        self.Debug.Display(_("Graph: RRD: %(SensorFile)s found") % {'SensorFile': self.G.getConfig('cfgphidgetcapturefile')} )
                        for ListSourceSensors in range(1,int(self.configSource.getConfig('cfgphidgetsensornb')) + 1):
                            if self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] != "":
                                if os.path.isfile(self.Cfgpictdir + listpictdir + "/" + self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + ".rrd") == False or cptdir <= 1:
                                    print("Graph: RRD: RRD file: Start parsing values")
                                    ValueTable = {}
                                    #ValueKeys = []
                                    ValueTableKeys = []
                                    ValueKeysDiff = []
                                    ValueInsertTable = {}
                                    if self.configSource.getConfig('cfgcroncaptureinterval') == "minutes":
                                        DefinedInterval = int(self.configSource.getConfig('cfgcroncapturevalue')) * 60
                                    elif self.configSource.getConfig('cfgcroncaptureinterval') == "seconds":
                                        DefinedInterval = int(self.configSource.getConfig('cfgcroncapturevalue'))

                                    Sensors = Config(self.Cfgpictdir + listpictdir + "/" + self.G.getConfig('cfgphidgetcapturefile'))
                                    for capturetime in Sensors.getFullConfig():
                                        if Sensors.getSensor(capturetime, self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0]) == False:
                                            ValueTable[Sensors.getSensor(capturetime, "Timestamp")] = "NaN"
                                        else:
                                            ValueTable[Sensors.getSensor(capturetime, "Timestamp")] = Sensors.getSensor(capturetime, self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0])
                                    NumberOfValues = len(ValueTable)
                                    print("Number of Values source: " + str(NumberOfValues))
                                    #print ValueTable.keys()
                                    cpt = 0
                                    ValueTableKeys = ValueTable.keys()
                                    ValueTableKeys.sort()
                                    #print ValueTableKeys
                                    cpt = 0

                                    self.Debug.Display(_("Graph: RRD: RRD file: begninning creation of %(SensorRRDFile)s file ...") % {'SensorRRDFile': self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + ".rrd"} )

                                    rrdstart = str(int(min(ValueTableKeys)))
                                    #rrdstart = str(int(min(ValueTableKeys)))
                                    rrdend = str(max(ValueTableKeys))
                                    ret = rrdtool.create(self.Cfgpictdir + listpictdir + "/" + self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + ".rrd", "--step", str(DefinedInterval), "--start", rrdstart,
                                                         "DS:"+ self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + ":GAUGE:600:U:U",
                                                         "RRA:AVERAGE:0.5:1:" + str(len(Sensors.getFullConfig())))
                                    if ret:
                                        print(rrdtool.error())

                                    for i in xrange(len(ValueTableKeys)):
                                        #print "Timestamp: " +  ValueTableKeys[i] + " - Value: " + ValueTable[ValueTableKeys[i]]
                                        if i == 0:
                                            CurrentTimestamp = int(ValueTableKeys[i])
                                        else:
                                            CurrentTimestamp = CurrentTimestamp + DefinedInterval
                                            ret = rrdtool.update(self.Cfgpictdir + listpictdir + "/" + self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + ".rrd", str(int(CurrentTimestamp)) + ':' + ValueTable[ValueTableKeys[i]])
                                            #print "Timestamp:" + str(i) + "/" + str(len(Sensors.getFullConfig())) + ":" + str(CurrentTimestamp) + ":" + str(rrdtool.error())
                                            #print "Timestamp: " +  str(CurrentTimestamp) + " - Value: " + ValueTable[ValueTableKeys[i]]

                                    ret = rrdtool.graph(self.Cfgpictdir + listpictdir + "/Sensor-" + self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + ".png", "--start", rrdstart, "--end", rrdend, "--vertical-label="+ self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[2],
                                                        "DEF:" + self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + "=" + self.Cfgpictdir + listpictdir + "/" + self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + ".rrd" + ":" + self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + ":AVERAGE",
                                                        "AREA:" + self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + "#" + self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[3]+ ":" + self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[2],
                                                        )
                                    if ret:
                                        print(rrdtool.error())

                                    cfgdispday = self.Cfgnow.strftime("%Y%m%d")

                                    if self.configSource.getConfig('cfgftpphidgetserverid') != "" and os.path.isfile(self.Cfgpictdir + listpictdir + "/Sensor-" + self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + ".png") and cfgdispday == listpictdir:
                                        FTPResult = FTPClass.FTPUpload(self.Cfgcurrentsource, self.configSource.getConfig('cfgftpphidgetserverid'), listpictdir + "/", self.Cfgpictdir + listpictdir + "/", "Sensor-" + self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + ".png", self.Debug, self.configSource.getConfig('cfgftpphidgetserverretry'))
                                else:
                                    self.Debug.Display(_("Graph: RRD: RRD file: %(SensorRRDFile)s found, cancelling ...") % {'SensorRRDFile': self.configSource.getConfig('cfgphidgetsensor' + str(ListSourceSensors))[0] + ".rrd"} )
                    else:
                        self.Debug.Display(_("Graph: RRD: %(SensorFile)s not found, moving to next directory") % {'SensorFile': self.G.getConfig('cfgphidgetcapturefile')} )

            """
        else:
            self.log.info("statsrrd.run(): " + _("Creation of the RRD Graph disabled for source: %(currentSourceId)s") % {'currentSourceId': str(self.currentSourceId)} )

    def getSensorsFromFile(self, currentCaptureFile):
        """ Scan a file to identify all sensor values it contains
            Args:
                None

            Returns:
                Dict: number of occurence for each of the sensors contained in the file
        """
        self.log.debug("xferUtils.checkThreadUUID(): " + _("Start"))
        sensors = {}
        for line in open(currentCaptureFile).readlines():
            #currentCaptureLine = json.loads(line, object_pairs_hook=OrderedDict)
            currentCaptureLine = json.loads(line)
            if 'sensors' in currentCaptureLine:
                if currentCaptureLine['sensors'] != None:
                    #print currentCaptureLine['sensors']
                    for sensorId in currentCaptureLine['sensors']:
                        if sensorId in sensors:
                            sensors[sensorId] += 1
                        else:
                            sensors[sensorId] = 1
        return sensors





     
               