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
from wpakXferJob import xferJob
from utils.wpakFTPTransfer import FTP_Transfer


class Transfer:
    def __init__(self, log, config_paths = None, source = None):
        self.log = log
        self.config_paths = config_paths
        self.__source = source

        # self.log = parentClass.log
        # self.config_dir = parentClass.config_dir
        # self.configPaths = parentClass.configPaths
        #
        # self.currentSourceId = parentClass.currentSourceId
        #
        # self.configSourceFTP = parentClass.configSourceFTP
        #
        # self.FTPUtils = parentClass.FTPUtils
        # self.fileUtils = parentClass.fileUtils
        #
        # self.dirEtc = parentClass.dirEtc
        # self.dirCurrentSource = parentClass.dirCurrentSource
        # self.dirXferQueue = parentClass.dirXferQueue

    @property
    def source(self):
        return self.__source

    @source.setter
    def source(self, source):
        self.__source = source

    def transfer_file(self, transferDate, sourceFilePath, destinationFilePath, serverId, maxRetries):
        """This function transfer the file, to a remote server, it can either transfer using xfer or direct FTP
        
        Args:
            transferDate: a date object, date object to be used for the xfer job filename
            sourceFilePath: a string, filepath on the local filesystem
            destinationFilePath: a string, filepath on the remote server
            serverId: an int, ID of the remote server in the file config-sourceX-ftpservers.cfg (X being the source ID)
            maxRetries: an int, number of times the tranfer should be retried before being considered failed.
        
        """
        self.log.info('Source ID: ' + str(self.source.id))

        # print self.currentSourceId
        # print self.dirEtc
        # frpServerConfigFile = self.dirEtc + "config-source" + str(self.currentSourceId) + "-ftpservers.cfg"
        # print frpServerConfigFile
        # ftpServerConfig = Config(self.log, self.dirEtc + "config-source" + str(self.currentSourceId) + "-ftpservers.cfg")
        #xferEnable = self.configSourceFTP.getConfig('cfgftpserverslist' + str(serverId))[6]
        if self.source.servers[serverId].xfer_enable == "yes":
            self.log.info("transferUtils.transferFile(): " + _("Transferring file through XFer mechanism"))
            xferJobDirectory = transferDate.strftime("%Y%m%d")
            xferJobFilenameDate = transferDate.strftime("%Y%m%d%H%M%S")
            xferJobFileMd5 = hashlib.sha224(
                'S' + str(self.currentSourceId) + 'local' + str(self.currentSourceId) + 'ftp' + str(
                    serverId) + sourceFilePath).hexdigest()
            xferJobFileName = xferJobFilenameDate + "-" + str(self.currentSourceId) + "-" + xferJobFileMd5 + ".json"

            self.log.info("transferUtils.transferFile(): " + _("Job Directory: %(xferJobDirectory)s") % {
                'xferJobDirectory': xferJobDirectory})
            self.log.info("transferUtils.transferFile(): " + _("Job Filename: %(xferJobFileName)s") % {
                'xferJobFileName': xferJobFileName})

            xferFtpServerHash = self.FTPUtils.calculateFTPServerHash(self.configSourceFTP, serverId)
            self.log.info("transferUtils.transferFile(): " + _("FTP Server Hash: %(xferFtpServerHash)s") % {
                'xferFtpServerHash': xferFtpServerHash})

            newXferJob = xferJob()
            newXferJob.setStatus("queued")
            newXferJob.setHash(xferJobFileMd5)
            newXferJob.setDateQueued(transferDate.isoformat())
            newXferJob.setSourceSourceId(str(self.currentSourceId))
            newXferJob.setSourceType("filesystem")
            # We remove the current source directory from the source file path, 
            # The xfer system will be looking at source ID to determine filepath
            sourceFilePath = sourceFilePath.replace(self.dirCurrentSource, '')
            newXferJob.setSourceFilePath(sourceFilePath)
            newXferJob.setDestinationSourceId(str(self.currentSourceId))
            newXferJob.setDestinationType("ftp")
            newXferJob.setDestinationFtpServerId(str(serverId))
            newXferJob.setDestinationFtpServerHash(xferFtpServerHash)
            newXferJob.setDestinationFilePath(destinationFilePath)
            newXferJob.setRetries(maxRetries)
            newXferJobFile = self.dirXferQueue + xferJobDirectory + "/" + xferJobFileName
            self.log.info("transferUtils.transferFile(): " + _("Saving Job file to: %(newXferJobFile)s") % {
                'newXferJobFile': newXferJobFile})
            self.fileUtils.CheckFilepath(newXferJobFile)
            newXferJob.writeXferJobFile(newXferJobFile)
        else:
            self.log.info("transferUtils.transfer_file(): " + _("Transferring file through direct FTP"))
            self.log.info("transferUtils.transfer_file(): " + _("Local file: %(sourceFilePath)s") % {'sourceFilePath': sourceFilePath})
            self.log.info("transferUtils.transfer_file(): " + _("Remote file: %(destinationFilePath)s") % {'destinationFilePath': destinationFilePath})
            currentFTP = FTP_Transfer(self.log, config_paths = self.config_paths, ftp_server = self.source.servers[serverId])
            if currentFTP.connect() is True:
                currentFTP.put(sourceFilePath, destinationFilePath)
                currentFTP.close()
            else:
                self.log.error(
                    "transferUtils.transferFile(): " + _("Unable to establish connection with the remote FTP server"))
