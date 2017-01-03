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
        if self.configGeneral.getConfig('cfgphidgetactivate') == "yes":
            phidgetPort = self.configSource.getConfig('cfgphidgetcameraport')
            if phidgetPort == "":
                phidgetPort = 0
            phidgetsClass = phidgets(self)
            #Note: Phidgets relays are installed in NC (Normally Closed) position, therefore we need to set output value to True to turn off the camera (Open circuit)
            outputValue = phidgetsClass.setOutputValue(phidgetPort, True)
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget port set to: %(outputValue)s") % {'outputValue': str(outputValue)})
            self.log.info("phidgetsUtils.restartCamera(): " + _("Pausing fot 5 seconds to let the camera drain all power"))
            time.sleep(10)
            outputValue = phidgetsClass.setOutputValue(phidgetPort, False)
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidget port set to: %(outputValue)s") % {'outputValue': str(outputValue)})
        else:
            self.log.info("phidgetsUtils.restartCamera(): " + _("Phidgets board not enabled"))
