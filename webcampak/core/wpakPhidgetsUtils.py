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

import time
import os
import socket

from wpakPhidgets import phidgets
from webcampak.core.gphoto.wpakGphoto import Gphoto
from wpakEmailObj import emailObj
from wpakDbUtils import dbUtils

class phidgetsUtils(object):
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir

        self.configGeneral = parentClass.configGeneral
        self.configSource = parentClass.configSource

        self.captureClass = parentClass
        self.dirLocale = parentClass.dirLocale
        self.dirLocaleMessage = parentClass.dirLocaleMessage
        self.dirCurrentLocaleMessages = parentClass.dirCurrentLocaleMessages
        self.dirEmails = parentClass.dirEmails
        self.fileUtils = parentClass.fileUtils

        self.currentSourceId = parentClass.currentSourceId

        self.dirBin = parentClass.dirBin
        self.binPhidgets = self.dirBin + self.configGeneral.getConfig('cfgphidgetbin')

    def scan_ports(self):
        """Scan all ports one by one to get their possible values"""
        self.log.debug("phidgetsUtils.scan_ports(): " + _("Start"))
        phidgetsClass = phidgets(self)
        phidgetsClass.createInterfaceKit()
        phidgetsClass.openPhidget()
        phidgetsClass.attachPhidgetKit()
        for current_port in range(0, 8):
            sensor_value = phidgetsClass.getSensorRawValue(current_port)
            self.log.info("phidgetsUtils.scan_ports(): " + _("Scanning port: %(current_port)s, RAW value: %(sensor_value)s") % {'current_port': str(current_port), 'sensor_value': str(sensor_value)})
            if sensor_value is not None:
                sensor_temperature = (sensor_value/4.095) * 0.22222 - 61.111
                sensor_luminosity = (sensor_value/4.095)
                sensor_pressure = ((sensor_value / 4.095)/4) + 10
                sensor_humidity = ((sensor_value / 4.095) * 0.1906) - 40.2
                self.log.info("phidgetsUtils.scan_ports(): " + _("Scanning port: %(current_port)s, Temperature value: %(sensor_temperature)s") % {'current_port': str(current_port), 'sensor_temperature': str(sensor_temperature)})
                self.log.info("phidgetsUtils.scan_ports(): " + _("Scanning port: %(current_port)s, Luminosity value: %(sensor_luminosity)s") % {'current_port': str(current_port), 'sensor_luminosity': str(sensor_luminosity)})
                self.log.info("phidgetsUtils.scan_ports(): " + _("Scanning port: %(current_port)s, Pressure value: %(sensor_pressure)s") % {'current_port': str(current_port), 'sensor_pressure': str(sensor_pressure)})
                self.log.info("phidgetsUtils.scan_ports(): " + _("Scanning port: %(current_port)s, Humidity value: %(sensor_humidity)s") % {'current_port': str(current_port), 'sensor_humidity': str(sensor_humidity)})
        phidgetsClass.closePhidget()

    def email_user_restart(self, before_cameras, after_cameras):
        """Send an email to source users to inform them about camera restart"""
        email_content = self.dirCurrentLocaleMessages + "emailOnlineContent.txt"
        email_subject = self.dirCurrentLocaleMessages + "emailOnlineSubject.txt"
        if os.path.isfile(email_content) == False:
            email_content = self.dirLocale + "en_US.utf8/" + self.dirLocaleMessage + "emailOnlineContent.txt"
            email_subject = self.dirLocale + "en_US.utf8/" + self.dirLocaleMessage + "emailOnlineSubject.txt"
        self.log.info("phidgetsUtils.email_user_restart(): " + _("Using message subject file: %(email_subject)s") % {
            'email_subject': email_subject})
        self.log.info("phidgetsUtils.email_user_restart(): " + _("Using message content file: %(email_content)s") % {
            'email_content': email_content})

        if os.path.isfile(email_content) and os.path.isfile(email_subject):
            emailContentFile = open(email_content, 'r')
            emailContent = emailContentFile.read()
            before_cameras_email = ''
            for camera in before_cameras:
                before_cameras_email = before_cameras_email + camera['usb_port'] + ' - ' + camera['camera_model'] + '/n'
            if before_cameras_email == '':
                before_cameras_email = 'N/A'
            emailContent = emailContent.replace("#CAMERASBEFORE#", before_cameras_email)
            after_cameras_email = ''
            for camera in after_cameras:
                after_cameras_email = before_cameras_email + camera['usb_port'] + ' - ' + camera['camera_model'] + '/n'
            if before_cameras_email == '':
                after_cameras_email = 'N/A'
            emailContent = emailContent.replace("#CAMERASAFTER#", after_cameras_email)
            emailContentFile.close()
            emailSubjectFile = open(email_subject, 'r')
            emailSubject = emailSubjectFile.read()
            emailSubjectFile.close()
            emailSubject = emailSubject.replace("#CURRENTHOSTNAME#", socket.gethostname())
            emailSubject = emailSubject.replace("#CURRENTSOURCE#", self.currentSourceId)
            newEmail = emailObj(self.log, self.dirEmails, self.fileUtils)
            newEmail.setFrom({'email': self.configGeneral.getConfig('cfgemailsendfrom')})
            db = dbUtils(self.captureClass)
            newEmail.setTo(db.getSourceEmailUsers(self.currentSourceId))
            db.closeDb()
            newEmail.setBody(emailContent)
            newEmail.setSubject(emailSubject)
            newEmail.writeEmailObjectFile()
        else:
            self.log.debug(
                "captureEmails.sendCaptureSuccess(): " + _("Unable to find default translation files to be used"))

    def restartCamera(self):
        """Restart a gphoto camera based on configured ports"""
        self.log.debug("phidgetsUtils.restartCamera(): " + _("Start"))
        phidget_activated = self.configGeneral.getConfig('cfgphidgetactivate')
        phidget_camera_relayport = self.configSource.getConfig('cfgphidgetcamerarelayport')
        if phidget_camera_relayport == "":
            phidget_camera_relayport = 0
        phidget_camera_sensorport = self.configSource.getConfig('cfgphidgetcamerasensorport')
        phidget_camera_pause = self.configSource.getConfig('cfgphidgetcamerapause')
        self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget Enabled: %(phidgetEnabled)s") % {'phidgetEnabled': str(phidget_activated)})
        self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget Camera Relay Port: %(phidget_camera_relayport)s") % {'phidget_camera_relayport': str(phidget_camera_relayport)})
        self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget Camera Sensor Port: %(phidget_camera_sensorport)s") % {'phidget_camera_sensorport': str(phidget_camera_sensorport)})
        self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget Camera Pause: %(phidget_camera_pause)s seconds") % {'phidget_camera_pause': str(phidget_camera_pause)})

        for camera in Gphoto(self.log).get_cameras():
            self.log.info("phidgetsUtils.restartCamera(): " + _("Camera: %(camera_model)s connected to USB: %(usb_port)s") % {'usb_port': camera['usb_port'], 'camera_model': camera['camera_model']})

        if phidget_activated == "yes":
            phidgetsClass = phidgets(self)
            #Note: Phidgets relays are installed in NC (Normally Closed) position, therefore we need to set output value to True to turn off the camera (Open circuit)

            phidgetsClass.createInterfaceKit()
            phidgetsClass.openPhidget()
            phidgetsClass.attachPhidgetKit()

            relay_state = phidgetsClass.getSensorRawValue(int(phidget_camera_sensorport))
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget Relay Sensor value: %(relay_state)s") % {'relay_state': str(relay_state)})

            phidgetsClass.setOutputRawValue(int(phidget_camera_relayport), True)
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget port set to True"))
            time.sleep(2)
            relay_state = phidgetsClass.getSensorRawValue(int(phidget_camera_sensorport))

            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget Relay Sensor value: %(relay_state)s") % {'relay_state': str(relay_state)})
            before_restart = Gphoto(self.log).get_cameras()
            for camera in before_restart:
                self.log.info("phidgetsUtils.restartCamera(): " + _("Camera: %(camera_model)s connected to USB: %(usb_port)s") % {'usb_port': camera['usb_port'], 'camera_model': camera['camera_model']})

            self.log.info("phidgetsUtils.restartCamera(): " + _("Pausing fot %(phidget_camera_pause)s seconds to let the camera drain all power") % {'phidget_camera_pause': str(phidget_camera_pause)})
            time.sleep(int(phidget_camera_pause))

            phidgetsClass.setOutputRawValue(int(phidget_camera_relayport), False)
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget port set to False"))
            time.sleep(2)

            after_restart = Gphoto(self.log).get_cameras()
            for camera in after_restart:
                self.log.info("phidgetsUtils.restartCamera(): " + _("Camera: %(camera_model)s connected to USB: %(usb_port)s") % {'usb_port': camera['usb_port'], 'camera_model': camera['camera_model']})

            relay_state = phidgetsClass.getSensorRawValue(int(phidget_camera_sensorport))
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget Relay Sensor value: %(relay_state)s") % {'relay_state': str(relay_state)})

            phidgetsClass.closePhidget()
            self.email_user_restart(before_restart, after_restart)

        else:
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidgets board not enabled"))
