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

from __future__ import print_function
from builtins import object
import subprocess
import json
import re
import logging

class Gphoto(object):
    """
        This class provide an abstraction layer for various gphoto2 calls
    """

    def __init__(self, log = logging):
        # if logging.__name__ == 'logging':
        #     logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
        self.__log = log

    @property
    def log(self):
        return self.__log

    @log.setter
    def log(self, logging_class):
        print('test')
        self.__log = logging_class

    def sys_call(self, command):
        try:
            self.log.debug('Gphoto.sys_call(): Calling: ' + json.dumps(command))
            output = subprocess.check_output(command, stderr=subprocess.STDOUT)
            self.log.debug(output.decode('utf-8'))
            return output
        except subprocess.CalledProcessError as e:
            self.log.debug('Gphoto.sys_call(): ' + e.output.decode('utf-8'))
            return False

    def get_cameras(self):
        list_cameras = []
        sys_command = [
            'gphoto2'
            , '--auto-detect'
        ]
        cmd_output = self.sys_call(sys_command)
        for line in cmd_output.split(b'\n'):
            result = re.compile('usb:...,...').search(line)
            if result is not None:
                camera_model = line.replace(result.group(0), '').strip()
                list_cameras.append({
                    'usb_port': result.group(0)
                    , 'camera_model': camera_model
                })
        if len(list_cameras) == 0:
            self.log.info('No Camera detected')
        return list_cameras

