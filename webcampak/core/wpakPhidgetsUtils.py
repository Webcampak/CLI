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

from wpakPhidgets import phidgets
from webcampak.core.gphoto.wpakGphoto import Gphoto

class phidgetsUtils(object):
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir

        self.configGeneral = parentClass.configGeneral
        self.configSource = parentClass.configSource

        self.dirBin = parentClass.dirBin
        self.binPhidgets = self.dirBin + self.configGeneral.getConfig('cfgphidgetbin')

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
            for camera in Gphoto(self.log).get_cameras():
                self.log.info("phidgetsUtils.restartCamera(): " + _("Camera: %(camera_model)s connected to USB: %(usb_port)s") % {'usb_port': camera['usb_port'], 'camera_model': camera['camera_model']})

            self.log.info("phidgetsUtils.restartCamera(): " + _("Pausing fot %(phidget_camera_pause)s seconds to let the camera drain all power") % {'phidget_camera_pause': str(phidget_camera_pause)})
            time.sleep(int(phidget_camera_pause))

            phidgetsClass.setOutputRawValue(int(phidget_camera_relayport), False)
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget port set to False"))
            time.sleep(2)

            for camera in Gphoto(self.log).get_cameras():
                self.log.info("phidgetsUtils.restartCamera(): " + _("Camera: %(camera_model)s connected to USB: %(usb_port)s") % {'usb_port': camera['usb_port'], 'camera_model': camera['camera_model']})

            relay_state = phidgetsClass.getSensorRawValue(int(phidget_camera_sensorport))
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget Relay Sensor value: %(relay_state)s") % {'relay_state': str(relay_state)})

            phidgetsClass.closePhidget()
        else:
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidgets board not enabled"))
