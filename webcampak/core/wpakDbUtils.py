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
from datetime import tzinfo, timedelta, datetime
from pytz import timezone
import shutil
import pytz
import json
import dateutil.parser
import zlib
import gzip
from dateutil import tz
import time
import sqlite3

#
class dbUtils:
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir
        self.configPaths = parentClass.configPaths
        
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.configGeneral = parentClass.configGeneral

        self.dbFile = self.configPaths.getConfig('doctrine')['dbal']['path']

        self.dbConnection = None
        self.dbCursor = None

    def openDb(self):
        self.dbConnection = sqlite3.connect(self.dbFile)
        self.dbCursor = self.dbConnection.cursor()

    def closeDb(self):
        self.dbConnection.close()
        self.dbCursor = None
        self.dbConnection = None

    def getSourceEmailUsers(self, sourceId):
        self.log.debug("dbUtils.getUsers(): " + _("Start"))
        if (self.dbConnection == None):
            self.openDb()

        dbQuery = "SELECT USE.EMAIL EMAIL, USE.FIRSTNAME FIRSTNAME, USE.LASTNAME LASTNAME \
        FROM USERS USE \
        LEFT JOIN USERS_SOURCES USESOU ON USE.USE_ID = USESOU.USE_ID \
        LEFT JOIN SOURCES SOU ON USESOU.SOU_ID = SOU.SOU_ID \
        WHERE USESOU.ALERTS_FLAG = 'Y' AND SOU.SOURCEID = :sourceId \
        ORDER BY USE.USERNAME";

        self.dbCursor.execute(dbQuery, {'sourceId':sourceId})
        users = []
        for row in self.dbCursor.fetchall():
            email, firstname, lastname = row
            users.append({'name': firstname + ' ' + lastname, 'email': email})
        return users



        
