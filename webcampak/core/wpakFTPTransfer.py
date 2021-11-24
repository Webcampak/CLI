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

from __future__ import absolute_import
from builtins import str
from builtins import object
import os, uuid, signal
import shutil
from ftplib import FTP

from .wpakConfigObj import Config
from .wpakFileUtils import fileUtils


# This class is used to initialize transfer queues and dispatch files to the queue
# It reads files from the global queue directory, starting from the oldest ones, and stops one all threads are full
# Each transfer queue (or thread) can hold up to "self.maxFilesPerThread" files 

class FTPTransfer(object):
    def __init__(self, log, config_dir):
        self.log = log
        self.config_dir = config_dir
        self.configPaths = Config(self.log, self.config_dir + 'param_paths.yml')

        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']

        self.ftpSession = None

    # Close the FTP connection
    def closeFtp(self):
        self.log.debug("FTPTransfer.closeFtp(): Start")
        try:
            self.ftpSession.close()
        except:
            self.log.error("FTPTransfer.closeFtp(): Unable to close FTP Session")


            # Calculate the FTP server hash

    # Hash is an md5 of the remote host and the username
    def calculateFTPServerHash(self, ftpServerConfig):
        self.log.debug("FTPTransfer.calculateFTPServerHash(): Start")
        FTPServer = f.getConfig('cfgftpserverslist' + str(serverId))[1]
        FTPUsername = f.getConfig('cfgftpserverslist' + str(serverId))[2]

        return hashlib.sha224(FTPServer + FTPUsername).hexdigest()

    # Get remote file size
    def getFilesize(self, filepath):
        self.log.info("FTPTransfer.getFilesize(): Start - Path: " + filepath)
        filesize = 0
        try:
            filesize = self.ftpSession.size(filepath)
        except:
            self.log.info("FTPTransfer.getFilesize(): File does not exist on FTP Server: " + filepath)
        return filesize

    # Function: createFTPDirectories
    # Description; This function is used to create FTP directories if they do not exist
    ## FTPDirectory: Directory to be created 
    # Return: Nothing
    def createFTPDirectories(self, FTPDirectory):
        self.log.info("FTPTransfer.createFTPDirectories(): Start")
        ftpdirectories = FTPDirectory.split("/")
        cpt = 0
        currentdir = ""
        for j in ftpdirectories:
            if j != "":
                currentdir = currentdir + "/" + ftpdirectories[cpt]
                try:
                    self.ftpSession.cwd(currentdir)
                    self.ftpSession.cwd('..')
                except:
                    self.log.info("FTPTransfer.createFTPDirectories(): Creation of : " + str(currentdir))
                    try:
                        self.ftpSession.mkd(currentdir)
                    except:
                        self.log.info(
                            "FTPTransfer.createFTPDirectories(): Directory might already exist : " + str(currentdir))

            cpt = cpt + 1

            # Function: putFile

    # Description; This function is used to upload a local file to a remote FTP server
    ## localFilepath: Full path to the file on the local filesystem
    ## remoteFilepath: Full path to the file on the remote FTP Server
    # Return: True if upload successful, False if upload failed        
    def putFile(self, localFilepath, remoteFilepath):
        self.log.debug("FTPTransfer.putFile(): Start")
        self.log.info("FTPTransfer.putFile(): Local: " + localFilepath)
        localFilesize = os.path.getsize(localFilepath)
        self.log.info("FTPTransfer.putFile(): Local Filesize: " + str(localFilesize))

        self.log.info("FTPTransfer.putFile(): Remote: " + remoteFilepath)
        fileUUID = str(uuid.uuid4()) + ".tmp"
        tmpRemoteFilepath = os.path.dirname(remoteFilepath) + "/" + str(fileUUID)

        self.log.info("FTPTransfer.putFile(): Ensuring remote directory exists, if not creating: " + os.path.dirname(
            remoteFilepath) + "/")
        self.createFTPDirectories(os.path.dirname(remoteFilepath) + "/")

        try:
            self.ftpSession.cwd(os.path.dirname(remoteFilepath) + "/")
        except:
            self.log.info(
                "FTPTransfer.putFile(): Unable to CD into newly created directory: " + os.path.dirname(remoteFilepath))
            return False

        self.log.info("FTPTransfer.putFile(): Starting upload in temporary file: " + tmpRemoteFilepath)
        loadedFile = open(localFilepath, 'rb')
        try:
            self.ftpSession.storbinary('STOR ' + fileUUID, loadedFile)
        except:
            self.log.info("FTPTransfer.putFile(): Unable to upload file")

        try:
            remoteFilesize = self.ftpSession.size(tmpRemoteFilepath)
        except:
            self.log.info("FTPTransfer.putFile(): Unable to get remote file size: " + tmpRemoteFilepath)
            return False

        self.log.info("FTPTransfer.putFile(): Remote Filesize: " + str(remoteFilesize))

        if (localFilesize != remoteFilesize):
            self.log.info("FTPTransfer.putFile(): Local and Remote Filesize are different, transfer considered failed")
            self.ftpSession.delete(fileUUID)
            return False

        self.log.info("FTPTransfer.putFile(): Local and Remote Filesize are identical, transfer considered successful")
        self.log.info("FTPTransfer.putFile(): Moving file to its definitive location: " + remoteFilepath)
        self.ftpSession.cwd("/")
        self.ftpSession.rename(tmpRemoteFilepath, remoteFilepath)
        self.log.info("FTPTransfer.putFile(): Upload Successful")

        return True

    # Function: getFile
    # Description; This function is used to download a file from a remote FTP server and save it on the local filesystem
    ## localFilepath: Full path to the file on the local filesystem
    ## remoteFilepath: Full path to the file on the remote FTP Server
    # Return: True if download successful, False if download failed        
    def getFile(self, localFilepath, remoteFilepath):
        self.log.debug("FTPTransfer.getFile(): Start")
        self.log.info("FTPTransfer.getFile(): Remote: " + remoteFilepath)
        remoteFilesize = self.getFilesize(remoteFilepath)
        self.log.info("FTPTransfer.getFile(): Remote Filesize: " + str(remoteFilesize))

        self.log.info("FTPTransfer.getFile(): Local: " + localFilepath)
        fileUUID = str(uuid.uuid4()) + ".tmp"
        tmpLocalFilepath = os.path.dirname(localFilepath) + "/" + str(fileUUID)

        self.log.info("FTPTransfer.getFile(): Ensuring local directory exists, if not creating: " + os.path.dirname(
            localFilepath) + "/")
        fileUtils.CheckDir(os.path.dirname(localFilepath) + "/")

        with open(tmpLocalFilepath, 'wb') as downloadedFile:
            try:
                self.ftpSession.retrbinary('RETR ' + remoteFilepath, downloadedFile.write)
            except:
                self.log.info("FTPTransfer.getFile(): Unable to upload file")
                downloadedFile.close()
                return False
            downloadedFile.close()

        self.log.info("FTPTransfer.getFile(): Local Filesize: " + str(remoteFilesize))
        localFilesize = 0
        if (os.path.isfile(tmpLocalFilepath)):
            localFilesize = os.path.getsize(tmpLocalFilepath)

        if (localFilesize != remoteFilesize):
            self.log.info("FTPTransfer.getFile(): Local and Remote Filesize are different, transfer considered failed")
            if (os.path.isfile(tmpLocalFilepath)):
                os.remove(tmpLocalFilepath)
            return False

        self.log.info("FTPTransfer.getFile(): Local and Remote Filesize are identical, transfer considered successful")
        self.log.info("FTPTransfer.getFile(): Moving file to its definitive location: " + localFilepath)
        shutil.move(tmpLocalFilepath, localFilepath)
        self.log.info("FTPTransfer.getFile(): Download Successful")

        return True


        # Function: initByServerId

    # Description; Initialize a FTP connection using parameters from a config file
    ## sourceId: SourceId where the Ftp configuration file is stored
    ## serverId: ServerId of the server to be used for the connection
    # Return: True if init successful, False if init failed   
    def initByServerId(self, sourceId, serverId):
        self.log.debug(
            "FTPTransfer.initByServerId(): Start: Source ID: " + str(sourceId) + " - Server ID: " + str(serverId))

        # We load the FTP configuration file
        if os.path.isfile(self.dirEtc + "config-source" + str(sourceId) + "-ftpservers.cfg"):
            f = Config(self.log, self.dirEtc + "config-source" + str(sourceId) + "-ftpservers.cfg")
            FTPServer = f.getConfig('cfgftpserverslist' + str(serverId))[1]
            FTPUsername = f.getConfig('cfgftpserverslist' + str(serverId))[2]
            FTPPassword = f.getConfig('cfgftpserverslist' + str(serverId))[3]
            FTPActive = f.getConfig('cfgftpserverslist' + str(serverId))[5]

        try:
            self.ftpSession = FTP(FTPServer)
        except:
            self.log.error("FTPTransfer.initByServerId(): Unable to connect to server: " + FTPServer)
            return False

        try:
            self.ftpSession.login(FTPUsername, FTPPassword)
        except:
            self.log.error(
                "FTPTransfer.initByServerId(): Unable to connect to server (username/password error): Username: " + FTPUsername)
            return False

        try:
            self.ftpSession.set_debuglevel(0)

        except:
            self.log.error("FTPTransfer.initByServerId(): Unable to set debug level")
            return False

        try:
            if FTPActive == "yes":
                self.ftpSession.set_pasv(False)
            else:
                self.ftpSession.set_pasv(True)
        except:
            self.log.error("FTPTransfer.initByServerId(): Unable to set Active Mode")
            return False

        self.log.info(
            "FTPTransfer.initByServerId(): Connection established with server: " + FTPServer + " - Username: " + FTPUsername)
        return True
