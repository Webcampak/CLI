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

import os, uuid, signal
import shutil
from ftplib import FTP

from webcampak.core.wpakConfigObj import Config
from webcampak.core.wpakFileUtils import fileUtils

# This class is used to initialize transfer queues and dispatch files to the queue
# It reads files from the global queue directory, starting from the oldest ones, and stops one all threads are full
# Each transfer queue (or thread) can hold up to "self.maxFilesPerThread" files 

class FTP_Transfer:
    def __init__(self, log, config_paths = None, ftp_server = None):
        self.log = log
        self.config_paths = config_paths

        self.dir_etc = self.config_paths.getConfig('parameters')['dir_etc']
        self.__ftp_server = ftp_server
        self.__ftp_session = None

    @property
    def ftp_session(self):
        return self.__ftp_session

    @ftp_session.setter
    def ftp_session(self, ftp_session):
        self.__ftp_session = ftp_session

    @property
    def ftp_server(self):
        return self.__ftp_server

    @ftp_server.setter
    def ftp_server(self, ftp_server):
        self.__ftp_server = ftp_server



            # Calculate the FTP server hash

    # # Hash is an md5 of the remote host and the username
    # def calculateFTPServerHash(self, ftpServerConfig):
    #     self.log.debug("FTP_Transfer.calculateFTPServerHash(): Start")
    #     FTPServer = f.getConfig('cfgftpserverslist' + str(serverId))[1]
    #     FTPUsername = f.getConfig('cfgftpserverslist' + str(serverId))[2]
    #
    #     return hashlib.sha224(FTPServer + FTPUsername).hexdigest()


    def connect(self):
        """Establish the initial connection to a remote FTP server"""
        self.log.info('FTP_Transfer.connect(): Connecting to server ID: ' + str(self.ftp_server.id))
        self.log.info('FTP_Transfer.connect(): Connecting to server HOST: ' + str(self.ftp_server.host))

        try:
            self.ftp_session = FTP(self.ftp_server.host)
        except:
            self.log.error('FTP_Transfer.connect(): Unable to connect to server')
            return False

        self.log.info('FTP_Transfer.connect(): Connecting to server USERNAME: ' + str(self.ftp_server.username))
        try:
            self.ftp_session.login(self.ftp_server.username, self.ftp_server.password)
        except:
            self.log.error('FTP_Transfer.connect(): Unable to connect to server (username/password error)')
            return False

        try:
            self.ftp_session.set_debuglevel(0)
        except:
            self.log.error("FTP_Transfer.connect(): Unable to set debug level")
            return False

        self.log.info('FTP_Transfer.connect(): Connecting to server FTP Active: ' + str(self.ftp_server.ftp_active))
        try:
            if self.ftp_server.ftp_active is True:
                self.ftp_session.set_pasv(False)
            else:
                self.ftp_session.set_pasv(True)
        except:
            self.log.error("FTP_Transfer.connect(): Unable to set Active Mode")
            return False

        self.log.info('FTP_Transfer.connect(): Connection Established')
        return True

    def put(self, local_filepath, remote_filepath):
        """Use the FTP PUT command to upload a file to the remote FTP server"""
        self.log.info("FTP_Transfer.put(): Local: " + local_filepath)
        localFilesize = os.path.getsize(local_filepath)
        self.log.info("FTP_Transfer.put(): Local Filesize: " + str(localFilesize))

        #Append the FTP path on the remote server
        remote_filepath = self.ftp_server.directory + remote_filepath
        self.log.info("FTP_Transfer.put(): Remote: " + remote_filepath)
        fileUUID = str(uuid.uuid4()) + ".tmp"
        tmpRemoteFilepath = os.path.dirname(remote_filepath) + "/" + str(fileUUID)

        self.log.info("FTP_Transfer.put(): Ensuring remote directory exists, if not creating: " + os.path.dirname(
            remote_filepath) + "/")
        self.create_path(os.path.dirname(remote_filepath) + "/")

        try:
            self.ftp_session.cwd(os.path.dirname(remote_filepath) + "/")
        except:
            self.log.info(
                "FTP_Transfer.put(): Unable to CD into newly created directory: " + os.path.dirname(remote_filepath))
            return False

        self.log.info("FTP_Transfer.put(): Starting upload in temporary file: " + tmpRemoteFilepath)
        loadedFile = file(local_filepath, 'rb')
        try:
            self.ftp_session.storbinary('STOR ' + fileUUID, loadedFile)
        except:
            self.log.info("FTP_Transfer.put(): Unable to upload file")

        try:
            remoteFilesize = self.ftp_session.size(tmpRemoteFilepath)
        except:
            self.log.info("FTP_Transfer.put(): Unable to get remote file size: " + tmpRemoteFilepath)
            return False

        self.log.info("FTP_Transfer.put(): Remote Filesize: " + str(remoteFilesize))

        if (localFilesize != remoteFilesize):
            self.log.info("FTP_Transfer.put(): Local and Remote Filesize are different, transfer considered failed")
            self.ftp_session.delete(fileUUID)
            return False

        self.log.info("FTP_Transfer.put(): Local and Remote Filesize are identical, transfer considered successful")
        self.log.info("FTP_Transfer.put(): Moving file to its definitive location: " + remote_filepath)
        self.ftp_session.cwd("/")
        self.ftp_session.rename(tmpRemoteFilepath, remote_filepath)
        self.log.info("FTP_Transfer.put(): Upload Successful")
        return True

    def create_path(self, ftp_dir):
        """Create a potentially missing directory or path on the remote server"""
        ftpdirectories = ftp_dir.split("/")
        cpt = 0
        currentdir = ""
        for j in ftpdirectories:
            if j != "":
                currentdir = currentdir + "/" + ftpdirectories[cpt]
                try:
                    self.ftp_session.cwd(currentdir)
                    self.ftp_session.cwd('..')
                except:
                    self.log.info("FTP_Transfer.create_path(): Creation of : " + str(currentdir))
                    try:
                        self.ftp_session.mkd(currentdir)
                    except:
                        self.log.info(
                            "FTP_Transfer.create_path(): Directory might already exist : " + str(currentdir))

            cpt = cpt + 1

    def get(self, local_filepath, remote_filepath):
        #Append the FTP path on the remote server
        remote_filepath = self.ftp_server.directory + remote_filepath
        self.log.info("FTP_Transfer.get(): Remote: " + remote_filepath)
        remoteFilesize = self.get_filesize(remote_filepath)
        self.log.info("FTP_Transfer.get(): Remote Filesize: " + str(remoteFilesize))

        self.log.info("FTP_Transfer.get(): Local: " + local_filepath)
        fileUUID = str(uuid.uuid4()) + ".tmp"
        tmpLocalFilepath = os.path.dirname(local_filepath) + "/" + str(fileUUID)

        self.log.info("FTP_Transfer.get(): Ensuring local directory exists, if not creating: " + os.path.dirname(
            local_filepath) + "/")
        fileUtils.CheckDir(os.path.dirname(local_filepath) + "/")

        with open(tmpLocalFilepath, 'wb') as downloadedFile:
            try:
                self.ftp_session.retrbinary('RETR ' + remote_filepath, downloadedFile.write)
            except:
                self.log.info("FTP_Transfer.get(): Unable to upload file")
                downloadedFile.close()
                return False
            downloadedFile.close()

        self.log.info("FTP_Transfer.get(): Local Filesize: " + str(remoteFilesize))
        localFilesize = 0
        if (os.path.isfile(tmpLocalFilepath)):
            localFilesize = os.path.getsize(tmpLocalFilepath)

        if (localFilesize != remoteFilesize):
            self.log.info("FTP_Transfer.get(): Local and Remote Filesize are different, transfer considered failed")
            if (os.path.isfile(tmpLocalFilepath)):
                os.remove(tmpLocalFilepath)
            return False

        self.log.info("FTP_Transfer.get(): Local and Remote Filesize are identical, transfer considered successful")
        self.log.info("FTP_Transfer.get(): Moving file to its definitive location: " + local_filepath)
        shutil.move(tmpLocalFilepath, local_filepath)
        self.log.info("FTP_Transfer.get(): Download Successful")

        return True

    # Get remote file size
    def get_filesize(self, filepath):
        self.log.info("FTP_Transfer.get_filesize(): Start - Path: " + filepath)
        filesize = 0
        try:
            filesize = self.ftp_session.size(filepath)
        except:
            self.log.info("FTP_Transfer.get_filesize(): File does not exist on FTP Server: " + filepath)
        return filesize

    def close(self):
        """Close the FTP connection"""
        self.log.info("FTP_Transfer.close(): Closing FTP Connection")
        try:
            self.ftp_session.close()
            return True
        except:
            self.log.error("FTP_Transfer.close(): Unable to close FTP Session")
            return False
