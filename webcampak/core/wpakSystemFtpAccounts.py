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

import os, uuid
import re
import shlex, subprocess
import gettext

from wpakConfigObj import Config
from wpakFileUtils import fileUtils
from wpakTimeUtils import timeUtils


# This class is used to initialize transfer queues and dispatch files to the queue
# It reads files from the global queue directory, starting from the oldest ones, and stops one all threads are full
# Each transfer queue (or thread) can hold up to "self.maxFilesPerThread" files 

class systemFtpAccounts:
    def __init__(self, log, appConfig, config_dir):
        self.log = log
        self.appConfig = appConfig
        self.config_dir = config_dir
        self.configPaths = Config(self.log, self.config_dir + 'param_paths.yml')

        self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirConfig = self.configPaths.getConfig('parameters')['dir_config']
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']
        self.dirInit = self.configPaths.getConfig('parameters')['dir_init']
        self.dirLocale = self.configPaths.getConfig('parameters')['dir_locale']

        self.setupLog()

        self.configGeneral = Config(self.log, self.dirConfig + 'config-general.cfg')

        self.timeUtils = timeUtils(self)

        self.initGetText(self.dirLocale, self.configGeneral.getConfig('cfgsystemlang'),
                         self.configGeneral.getConfig('cfggettextdomain'))

    def setupLog(self):
        """ Setup logging to file """
        systemLogs = self.dirLogs + "system/"
        if not os.path.exists(systemLogs):
            os.makedirs(systemLogs)
        logFilename = systemLogs + "ftp.log"
        self.appConfig.set(self.log._meta.config_section, 'file', logFilename)
        self.appConfig.set(self.log._meta.config_section, 'rotate', True)
        self.appConfig.set(self.log._meta.config_section, 'max_bytes', 512000)
        self.appConfig.set(self.log._meta.config_section, 'max_files', 10)
        self.log._setup_file_log()

    def initGetText(self, dirLocale, cfgsystemlang, cfggettextdomain):
        """ Initialize Gettext with the corresponding translation domain
        
        Args:
            dirLocale: A string, directory location of the file
            cfgsystemlang: A string, webcampak-level language configuration parameter from config-general.cfg
            cfggettextdomain: A string, webcampak-level gettext domain configuration parameter from config-general.cfg
        
        Returns:
            None
        """
        try:
            t = gettext.translation(cfggettextdomain, dirLocale, [cfgsystemlang], fallback=True)
            _ = t.ugettext
            t.install()
            self.log.info("systemFtpAccounts.initGetText(): " + _(
                "Initialized gettext with Domain: %(cfggettextdomain)s - Language: %(cfgsystemlang)s - Path: %(dirLocale)s")
                          % {'cfggettextdomain': cfggettextdomain, 'cfgsystemlang': cfgsystemlang,
                             'dirLocale': dirLocale})
        except:
            self.log.error("systemFtpAccounts.initGetText(): " + _("No translation file available"))

            # Function: create

    # Description: Create Local FTP User Accounts
    # Return: Nothing     
    def create(self):
        # Load the config containing all paths and the general config file
        self.log.info("systemFtpAccounts.create(): " + _("Creating Local FTP Accounts"))
        self.log.info("systemFtpAccounts.create(): " + _("Deleting previous temporary users file (if any)"))
        if os.path.isfile("/etc/vsftpd/ftpusers"):
            os.remove("/etc/vsftpd/ftpusers")

        fileUtils.CheckFilepath("/etc/vsftpd/ftpusers")

        f = open("/etc/vsftpd/ftpusers", 'a')
        f.write(self.configGeneral.getConfig('cfgftpresourcesusername') + "\n")
        f.write(self.configGeneral.getConfig('cfgftpresourcespassword') + "\n")

        # We list all files from configuration directory
        for scanfile in sorted(os.listdir(self.dirEtc), reverse=True):
            if re.findall('config-source[0-9]+.cfg', scanfile) and scanfile[-1] != "~":
                sourceid = str(re.findall('\d+', scanfile)[0])
                self.log.info("systemFtpAccounts.create(): " + _(
                    "Identified configuration file: %(scanfile)s Source ID: %(sourceid)s") % {'scanfile': scanfile,
                                                                                              'sourceid': sourceid})
                if os.path.isfile("/etc/vsftpd/vsftpd_user_conf/source" + sourceid) == False:
                    self.log.info("systemFtpAccounts.create(): " + _(
                        "There was no VSFTPD configuration file for source: %(sourceid)s, creating ..") % {
                                      'sourceid': sourceid})
                    fileUtils.CheckDir('/etc/vsftpd/vsftpd_user_conf/')
                    vsftpdFile = "/etc/vsftpd/vsftpd_user_conf/source" + sourceid
                    fvs = open(vsftpdFile, 'w')
                    fvs.write('local_root=/home/webcampak/webcampak/sources/source' + sourceid + '/ \n')
                    fvs.write(' \n')
                    vsftpdTemplateFile = self.dirInit + "vsftpd-source"
                    with open(vsftpdTemplateFile) as ftf:
                        for line in ftf:
                            fvs.write(line + ' \n')
                    ftf.close()
                    fvs.close()

                self.log.info("systemFtpAccounts.create(): " + _(
                    "Opening configuration file %(scanfile)s for source: %(sourceid)s, creating ..") % {
                                  'scanfile': scanfile, 'sourceid': sourceid})
                currentSourceConfig = Config(self.log, self.dirEtc + scanfile)
                f.write("source" + sourceid + "\n")
                f.write(currentSourceConfig.getConfig('cfglocalftppass') + "\n")
                if os.path.exists(self.dirSources + "source" + sourceid + "/") == True:
                    self.log.info("systemFtpAccounts.create(): " + _("Making directory not writable %(directory)s") % {
                        'directory': self.dirSources + "source" + sourceid + "/"})
                    Command = "chmod -w " + self.dirSources + "source" + sourceid + "/"
                    self.log.info("systemFtpAccounts.create(): " + _("Modifying file permission: %(Command)s") % {
                        'Command': Command})
                    args = shlex.split(Command)
                    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    output, errors = p.communicate()
                    self.log.info(output)
                    self.log.info(errors)
        f.write(" " + "\n")
        f.close()

        #	for sources in range(1, int(g.getConfig('cfgnbsources')) + 1):
        #		if os.path.isfile(self.dirEtc + "config-source" + str(sources) + ".cfg"):
        #			c = Config(self.dirEtc + "config-source" + str(sources) + ".cfg")
        #			f.write("source" + str(sources) + "\n")
        #			f.write(c.getConfig('cfglocalftppass') + "\n")
        #	f.write(" " + "\n")
        #	f.close()

        # echo "local_root=/home/francois/webcampak/sources/" > /etc/vsftpd/vsftpd_user_conf/source3
        # echo " " >> /etc/vsftpd/vsftpd_user_conf/source3
        # cat /home/francois/webcampak/init/config/vsftpd-source >> /etc/vsftpd/vsftpd_user_conf/source3
        self.log.info("systemFtpAccounts.create(): " + _("Creation of the users database"))

        # Command = "db4.7_load -T -t hash -f /etc/vsftpd/ftpusers /etc/vsftpd/login.db"
        Command = "db5.3_load -T -t hash -f /etc/vsftpd/ftpusers /etc/vsftpd/login.db"
        self.log.info(
            "systemFtpAccounts.create(): " + _("Creation of the database: %(Command)s") % {'Command': Command})

        args = shlex.split(Command)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = p.communicate()
        self.log.info(output)
        self.log.info(errors)
