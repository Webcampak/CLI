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

import hashlib

from ...wpakPhidgets import phidgets


class capturePhidget(object):
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir

        self.configPaths = parentClass.configPaths
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']
        self.dirCache = self.configPaths.getConfig('parameters')['dir_cache']
        self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']
        self.dirResources = self.configPaths.getConfig('parameters')['dir_resources']
        self.dirBin = self.configPaths.getConfig('parameters')['dir_bin']

        self.configGeneral = parentClass.configGeneral
        self.configSource = parentClass.configSource
        self.currentSourceId = parentClass.getSourceId()

        self.dirCurrentSourceTmp = self.dirSources + 'source' + self.currentSourceId + '/' + \
                                   self.configPaths.getConfig('parameters')['dir_source_tmp']
        self.dirCurrentSourcePictures = self.dirSources + 'source' + self.currentSourceId + '/' + \
                                        self.configPaths.getConfig('parameters')['dir_source_pictures']
        self.captureDate = parentClass.getCaptureTime().strftime("%Y%m%d%H%M%S")
        self.captureDay = parentClass.getCaptureTime().strftime("%Y%m%d")
        self.captureTimestamp = parentClass.getCaptureTime().strftime("%s")
        self.captureFilename = self.captureDate + ".txt"

        self.fileUtils = parentClass.fileUtils
        self.pictureTransformations = parentClass.pictureTransformations
        self.phidgetsUtils = parentClass.phidgetsUtils

    # Function: Capture
    # Description; This function is used to capture a sensor values
    # Return: Nothing
    def capture(self):
        self.log.info("capturePhidget.capture(): " + _("Start capturing sensor values"))
        # Get a list of all sensors for the source
        allSensors = self.getConfigSensors()
        capturedSensors = {}
        if len(allSensors) > 0:
            phidgetsClass = phidgets(self)
            phidgetsClass.createInterfaceKit()
            phidgetsClass.openPhidget()
            if phidgetsClass.attachPhidgetKit() == True:
                for currentSensor in allSensors:
                    # cfgphidgetsensor1="1","2","Inside Temperature","FF0000"
                    sensorType = currentSensor[0]
                    sensorPort = int(currentSensor[1])
                    sensorLegend = currentSensor[2]
                    sensorColor = currentSensor[3]
                    if sensorType != '' and sensorPort != '':
                        # cfgphidgetsensortype1="Temperature", "-30", "80", "(SensorValue / 4.095) * 0.22222 - 61.111"
                        sensorTypeConfig = self.configGeneral.getConfig('cfgphidgetsensortype' + str(sensorType))
                        sensorTypeName = sensorTypeConfig[0]
                        sensorTypeFormula = sensorTypeConfig[3]
                        self.log.info("capturePhidget.capture(): " + _(
                            "Capturing sensor: %(sensorTypeName)s from port: %(sensorPort)s") % {
                                          'sensorTypeName': str(sensorTypeName), 'sensorPort': str(sensorPort)})
                        SensorValue = int(phidgetsClass.getSensorRawValue(sensorPort))
                        sensorCalculatedValue = round(eval(sensorTypeFormula), 1)
                        self.log.info("capturePhidget.capture(): " + _(
                            "Captured value, RAW: %(SensorValue)s Interpreted: %(sensorCalculatedValue)s") % {
                                          'SensorValue': str(SensorValue),
                                          'sensorCalculatedValue': str(sensorCalculatedValue)})

                        currentSensor = {}
                        sensorHash = hashlib.sha224(sensorLegend + sensorTypeName).hexdigest()
                        currentSensor['legend'] = sensorLegend
                        currentSensor['type'] = sensorTypeName
                        currentSensor['value'] = sensorCalculatedValue
                        currentSensor['valueRaw'] = SensorValue
                        currentSensor['color'] = sensorColor
                        capturedSensors[sensorHash] = currentSensor
                phidgetsClass.closePhidget()
        if len(capturedSensors) > 0:
            return capturedSensors
        else:
            return None

    # Function: getConfigSensors
    # Description; This function find all sensors in the config file
    # Return: An array containing all sensors
    def getConfigSensors(self):
        fullSourceConfig = self.configSource.getFullConfig()
        sensorsCfg = []
        for configIdx in fullSourceConfig:
            if "cfgphidgetsensor" in configIdx and configIdx != "cfgphidgetsensornb" and "cfgphidgetsensorinsert" not in configIdx and "cfgphidgetsensorsgraph" not in configIdx:
                if fullSourceConfig[configIdx][0] != '' and fullSourceConfig[configIdx][1] != '':
                    sensorsCfg.append(fullSourceConfig[configIdx])
        return sensorsCfg
