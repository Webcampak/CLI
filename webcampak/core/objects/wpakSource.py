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
from webcampak.core.wpakConfigObj import Config
from webcampak.core.objects.wpakServer import Server
from webcampak.core.objects.wpakSourceConfiguration import SourceConfiguration


class Source(object):
    """ Builds an object containing the source itself, its ID, and configuration settings"""

    def __init__(self, log, source_id = None, config_paths = None):
        self.log = log
        self.config_paths = config_paths

        self.__id = source_id
        self.__servers = {}
        self.__path = self.config_paths.getConfig('parameters')['dir_sources'] + 'source' + str(self.id) + '/'
        self.__cfg_filepath = self.config_paths.getConfig('parameters')['dir_etc'] + 'config-source' + str(self.id) + '.yml'
        self.load_servers()

        #Load Source Configuration
        self.cfg = SourceConfiguration(self.log, cfg_filepath=self.cfg_filepath, config_paths = self.config_paths)

    @property
    def id(self):
        return self.__id

    @id.setter
    def id(self, id):
        self.__id = id

    @property
    def servers(self):
        return self.__servers

    @servers.setter
    def servers(self, servers):
        self.__servers = servers

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, path):
        self.__path = path

    @property
    def cfg(self):
        return self.__cfg

    @cfg.setter
    def cfg(self, cfg):
        self.__cfg = cfg

    @property
    def cfg_filepath(self):
        return self.__cfg_filepath

    @cfg_filepath.setter
    def cfg_filepath(self, cfg_filepath):
        self.__cfg_filepath = cfg_filepath

    def load_servers(self):
        cfg_servers = Config(self.log, self.config_paths.getConfig('parameters')['dir_etc'] + 'config-source' + str(self.id) + '-ftpservers.cfg')
        for i in range(1, int(cfg_servers.getConfig('cfgftpserverslistnb')) + 1):
            self.log.info('Source Object - Loading Server: ' + str(i))
            self.servers[i] = Server()
            self.servers[i].id = i
            self.servers[i].name = cfg_servers.getConfig('cfgftpserverslist' + str(i))[0]
            self.servers[i].host = cfg_servers.getConfig('cfgftpserverslist' + str(i))[1]
            self.servers[i].username = cfg_servers.getConfig('cfgftpserverslist' + str(i))[2]
            self.servers[i].password = cfg_servers.getConfig('cfgftpserverslist' + str(i))[3]
            self.servers[i].directory = cfg_servers.getConfig('cfgftpserverslist' + str(i))[4]
            self.servers[i].ftp_active = cfg_servers.getConfig('cfgftpserverslist' + str(i))[5]
            self.servers[i].xfer_enable = cfg_servers.getConfig('cfgftpserverslist' + str(i))[6]
            self.servers[i].xfer_threads = cfg_servers.getConfig('cfgftpserverslist' + str(i))[7]

            self.log.info(self.servers[i].export())
