#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2010-2017 Eurotechnia (support@webcampak.com)
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

import os
import json
import subprocess

class Time:
    @staticmethod
    def get_source_time(source):
        print('test')
        # We capture the current date and time, this value is used through the whole software
        # If capture is configured to be delayed there are two option, use script start date or capture date

    # def getCurrentSourceTime(self, sourceConfig):
    #     self.log.debug("timeUtils.getCurrentSourceTime(): " + _("Start"))
    #     if sourceConfig.getConfig(
    #             'cfgcapturetimezone') != "":  # Update the timezone from UTC to the source's timezone
    #         self.log.info("timeUtils.getCurrentSourceTime(): " + _("Source Timezone is: %(sourceTimezone)s") % {
    #             'sourceTimezone': sourceConfig.getConfig('cfgcapturetimezone')})
    #         sourceTimezone = tz.gettz(sourceConfig.getConfig('cfgcapturetimezone'))
    #         cfgnowsource = datetime.now(sourceTimezone)
    #     else:
    #         cfgnowsource = datetime.utcnow()
    #     self.log.info("timeUtils.getCurrentSourceTime(): " + _("Current source time: %(cfgnowsource)s") % {
    #         'cfgnowsource': cfgnowsource.isoformat()})
    #     return cfgnowsource
    #
