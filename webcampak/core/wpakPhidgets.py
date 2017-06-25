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

from ctypes import *

from Phidgets.PhidgetException import PhidgetErrorCodes, PhidgetException
from Phidgets.Devices.InterfaceKit import InterfaceKit


class phidgets(object):
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir

        self.configGeneral = parentClass.configGeneral
        self.configSource = parentClass.configSource

        self.dirBin = parentClass.dirBin
        self.binPhidgets = self.dirBin + self.configGeneral.getConfig('cfgphidgetbin')

        self.interfaceKit = None

    def createInterfaceKit(self):
        """Documentation To be completed"""
        self.log.info("phidgets.createInterfaceKit(): " + _("Create an InterfaceKit object"))
        try:
            self.interfaceKit = InterfaceKit()
        except RuntimeError as e:
            self.log.error("phidgets.createInterfaceKit(): " + _("Unable to create (code %(Code)i, %(Details)s)") % {
                'Code': e.code, 'Details': e.details})

    def openPhidget(self):
        """Documentation To be completed"""
        self.log.info("phidgets.openPhidget(): " + _("Open Phidget using InterfaceKit"))
        try:
            self.interfaceKit.openPhidget()
        except PhidgetException as e:
            self.log.error(
                "phidgets.createInterfaceKit(): " + _("Unable to open InterfaceKit (code %(Code)i, %(Details)s)") % {
                    'Code': e.code, 'Details': e.details})

    def closePhidget(self):
        """Documentation To be completed"""
        self.log.info("phidgets.closePhidget(): " + _("Close Phidget using InterfaceKit"))
        try:
            self.interfaceKit.closePhidget()
        except PhidgetException as e:
            self.log.error(
                "phidgets.closePhidget(): " + _("Unable to close InterfaceKit (code %(Code)i, %(Details)s)") % {
                    'Code': e.code, 'Details': e.details})

    def attachPhidgetKit(self):
        """Documentation To be completed"""
        self.log.info("phidgets.attachPhidgetKit(): " + _("Attaching Phidget Kit"))
        try:
            self.interfaceKit.waitForAttach(1000)
            return True
        except PhidgetException as e:
            self.log.error("phidgets.attachPhidgetKit(): " + _(
                "Unable to connect to InterfaceKit (code %(Code)i, %(Details)s") % {'Code': e.code,
                                                                                     'Details': e.details})
            self.closePhidget()
            return False

    def getSensorRawValue(self, input):
        """Documentation To be completed"""
        inputlevel = None
        try:
            inputlevel = self.interfaceKit.getSensorRawValue(input)
        except PhidgetException as e:
            self.log.error("phidgets.getSensorValue(): " + _(
                "Unable to connect to obtain sensor value (code %(Code)i, %(Details)s") % {'Code': e.code,
                                                                                            'Details': e.details})
        return inputlevel

    def getSensorValue(self, sensor):
        """Documentation To be completed"""
        self.createInterfaceKit()
        self.openPhidget()
        self.attachPhidgetKit()
        try:
            inputlevel = self.interfaceKit.getSensorRawValue(sensor)
        except PhidgetException as e:
            self.log.error("phidgets.getSensorValue(): " + _(
                "Unable to connect to obtain sensor value (code %(Code)i, %(Details)s") % {'Code': e.code,
                                                                                            'Details': e.details})

        self.closePhidget()
        self.log.error("phidgets.getSensorValue(): " + _("Sensor Value: %(inputlevel)d") % {'inputlevel': inputlevel})

        return inputlevel

    def setOutputValue(self, outputPort, outputValue):
        """Documentation To be completed"""
        self.log.info("phidgets.setOutputValue(): " + _("Set Output Port: %(outputPort)s To: %(outputValue)s ") % {'outputPort': str(outputPort), 'outputValue': str(outputValue)})
        self.createInterfaceKit()
        self.openPhidget()
        self.attachPhidgetKit()
        try:
            self.interfaceKit.setOutputState(outputPort, outputValue)
        except PhidgetException as e:
            self.log.error("phidgets.setOutputValue(): " + _("Unable to connect to set output value"))

        currentOutputPort = None
        try:
            currentOutputPort = self.interfaceKit.getOutputState(outputPort)
        except PhidgetException as e:
            self.log.error("phidgets.setOutputValue(): " + _("Unable to get value from output port"))

        self.closePhidget()
        self.log.info("phidgets.setOutputValue(): " + _("Sensor Value: %(currentOutputPort)s") % {'currentOutputPort': str(currentOutputPort)})
        return currentOutputPort

    def setOutputRawValue(self, outputPort, outputValue):
        """Documentation To be completed"""
        self.log.info("phidgets.setOutputValue(): " + _("Set Output Port: %(outputPort)s To: %(outputValue)s ") % {'outputPort': str(outputPort), 'outputValue': str(outputValue)})
        try:
            self.interfaceKit.setOutputState(outputPort, outputValue)
        except PhidgetException as e:
            self.log.error("phidgets.setOutputValue(): " + _("Unable to connect to set output value"))
