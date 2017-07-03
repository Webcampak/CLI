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
from webcampak.core.objects.wpakXfer import Xfer

class Transfer:
    def __init__(self, log, config_paths = None, source = None):
        self.log = log
        self.config_paths = config_paths
        self.__source = source
        self.dir_xfer_queue = self.config_paths.getConfig('parameters')['dir_xfer'] + 'queued/'

        # self.log = parentClass.log
        # self.config_dir = parentClass.config_dir
        # self.configPaths = parentClass.configPaths
        #
        # self.source.id = parentClass.currentSourceId
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

    def transfer_file(self, transfer_date, source_filepath, destination_filepath, remote_server, max_retries):
        """This function transfer the file, to a remote server, it can either transfer using xfer or direct FTP
        
        Args:
            transfer_date: a date object, date object to be used for the xfer job filename
            source_filepath: a string, filepath on the local filesystem
            destination_filepath: a string, filepath on the remote server
            remote_server.id: a server object, built previously from the file config-sourceX-ftpservers.cfg (X being the source ID)
            max_retries: an int, number of times the tranfer should be retried before being considered failed.
        
        """
        self.log.info('Transfer file for Source ID: ' + str(self.source.id))
        if remote_server.xfer_enable == 'yes':
            self.log.info('Transfer.transferFile(): ' + _('Transferring file through XFer mechanism'))
            xfer_job_directory = transfer_date.strftime('%Y%m%d')
            xfer_job_filename_date = transfer_date.strftime('%Y%m%d%H%M%S')
            xfer_job_file_md5 = hashlib.sha224('S' + str(self.source.id) + 'local' + str(self.source.id) + 'ftp' + str(remote_server.id) + source_filepath).hexdigest()
            xfer_job_filename = xfer_job_filename_date + '-' + str(self.source.id) + '-' + xfer_job_file_md5 + '.json'
            xfer_job_filepath = self.dir_xfer_queue + xfer_job_directory + '/' + xfer_job_filename

            self.log.info('transferUtils.transfer_file(): ' + _('Job Directory: %(xfer_job_directory)s') % {'xfer_job_directory': xfer_job_directory})
            self.log.info('transferUtils.transfer_file(): ' + _('Job Filename: %(xfer_job_filename)s') % {'xfer_job_filename': xfer_job_filename})
            self.log.info('transferUtils.transfer_file(): ' + _('FTP Server Hash: %(server_hash)s') % {'server_hash': remote_server.hash()})


            new_xfer_job = Xfer(self.log
                             , xfer_filepath=xfer_job_filepath
                             , dir_schemas=self.config_paths.getConfig('parameters')['dir_schemas'])
            new_xfer_job.xfer['status'] = 'queued'
            new_xfer_job.xfer['hash'] = xfer_job_file_md5
            new_xfer_job.xfer['retries'] = max_retries
            new_xfer_job.xfer['date_queued'] = transfer_date.isoformat()
            new_xfer_job.xfer['source']['sourceid'] = self.source.id
            new_xfer_job.xfer['source']['type'] = 'filesystem'
            # We remove the current source directory from the source file path,
            # The xfer system will be looking at source ID to determine filepath
            source_filepath = source_filepath.replace(self.source.path, '')
            new_xfer_job.xfer['source']['filepath'] = source_filepath
            new_xfer_job.xfer['destination']['sourceid'] = self.source.id
            new_xfer_job.xfer['destination']['type'] = 'ftp'
            new_xfer_job.xfer['destination']['ftpserverid'] = remote_server.id
            new_xfer_job.xfer['destination']['ftpserverhash'] = remote_server.hash()
            new_xfer_job.xfer['destination']['filepath'] = destination_filepath

            self.log.info('transferUtils.transfer_file(): ' + _('Saving Job file to: %(xfer_job_filepath)s') % {'xfer_job_filepath': xfer_job_filepath})
            new_xfer_job.save()
        else:
            self.log.info('transferUtils.transfer_file(): ' + _('Transferring file through direct FTP'))
            self.log.info('transferUtils.transfer_file(): ' + _('Local file: %(source_filepath)s') % {'source_filepath': source_filepath})
            self.log.info('transferUtils.transfer_file(): ' + _('Remote file: %(destination_filepath)s') % {'destination_filepath': destination_filepath})
            currentFTP = FTP_Transfer(self.log, config_paths = self.config_paths, ftp_server = remote_server)
            if currentFTP.connect() is True:
                currentFTP.put(source_filepath, destination_filepath)
                currentFTP.close()
            else:
                self.log.error('transferUtils.transfer_file(): ' + _('Unable to establish connection with the remote FTP server'))
