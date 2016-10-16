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

from wpakConfigObj import Config
from wpakFileUtils import fileUtils

# This class is used to initialize transfer queues and dispatch files to the queue
# It reads files from the global queue directory, starting from the oldest ones, and stops one all threads are full
# Each transfer queue (or thread) can hold up to "self.maxFilesPerThread" files 

class FTPUtils:
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir
        self.configPaths = parentClass.configPaths
        
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']

    # Calculate the FTP server hash
    # Hash is an md5 of the remote host and the username
    def calculateFTPServerHash(self, ftpServerConfig, serverId):
        self.log.debug("FTPUtils.calculateFTPServerHash(): Start")
        FTPServer = ftpServerConfig.getConfig('cfgftpserverslist' + str(serverId))[1]
        FTPUsername = ftpServerConfig.getConfig('cfgftpserverslist' + str(serverId))[2]
        
        return hashlib.sha224(FTPServer + FTPUsername).hexdigest()
                
        """
                # 
        $identifiedFtpServer = null;
        foreach ($sourceconfigurationFTPServers as $idx=>$ftpServer) {
            if ($ftpServer['ID'] == $serverId) {
                $identifiedFtpServer = $ftpServer;
            }
        }
        return md5($identifiedFtpServer['HOST'] . $identifiedFtpServer['USERNAME']); 
        """
                

        