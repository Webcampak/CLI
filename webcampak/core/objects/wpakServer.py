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

import dateutil.parser


class Server(object):
    """ Builds an object containing the source itself, its ID, and configuration settings"""

    # def __init__(self):


    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, id):
        self.__id = id

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def host(self):
        return self.__host

    @host.setter
    def host(self, host):
        self.__host = host

    @property
    def username(self):
        return self.__username

    @username.setter
    def username(self, username):
        self.__username = username

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, password):
        self.__password = password

    @property
    def directory(self):
        return self.__directory

    @directory.setter
    def directory(self, directory):
        self.__directory = directory

    @property
    def ftp_active(self):
        return self.__ftp_active

    @ftp_active.setter
    def ftp_active(self, ftp_active):
        self.__ftp_active = ftp_active

    @property
    def xfer_enable(self):
        return self.__xfer_enable

    @xfer_enable.setter
    def xfer_enable(self, xfer_enable):
        self.__xfer_enable = xfer_enable

    @property
    def xfer_threads(self):
        return self.__xfer_threads

    @xfer_threads.setter
    def xfer_threads(self, xfer_threads):
        self.__xfer_threads = xfer_threads

    def export(self):
        return {
            'id': self.id
            , 'name': self.name
            , 'host': self.host
            , 'username': self.username
            , 'password': self.password
            , 'directory': self.directory
            , 'ftp_active': self.ftp_active
            , 'xfer_enable': self.xfer_enable
            , 'xfer_threads': self.xfer_threads
        }
