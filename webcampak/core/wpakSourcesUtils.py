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

import os
from wpakConfigObj import Config


class sourcesUtils:
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir
        self.configPaths = parentClass.configPaths

        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']

        self.configGeneral = parentClass.configGeneral

    def getSourcesIds(self):
        self.log.info("sourcesUtils.getSources(): " + _("Start"))
        sourcesIds = []
        for sourcesDir in os.listdir(self.dirSources):
            sourcesDir = sourcesDir.strip('source')
            sourcesIds.append(int(sourcesDir))
        sourcesIds.sort()
        return sourcesIds

    def getActiveSourcesIds(self):
        self.log.info("sourcesUtils.getActiveSourcesIds(): " + _("Start"))
        sourcesIds = self.getSourcesIds()
        activeSourcesIds = []
        for currentSource in sourcesIds:
            configSource = Config(self.log, self.dirEtc + 'config-source' + str(currentSource) + '.cfg')
            if configSource.getConfig('cfgsourceactive') == "yes":
                self.log.info("sourcesUtils.getActiveSourcesIds(): " + _("Source: %(currentSource)s is active.") % {
                    'currentSource': str(currentSource)})
                activeSourcesIds.append(currentSource)
            else:
                self.log.info("sourcesUtils.getActiveSourcesIds(): " + _("Source: %(currentSource)s is inactive.") % {
                    'currentSource': str(currentSource)})
        activeSourcesIds.sort()
        return activeSourcesIds
