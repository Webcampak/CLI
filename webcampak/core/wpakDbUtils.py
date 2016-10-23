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

        self.dbCursor.execute(dbQuery, {'sourceId': sourceId})
        users = []
        for row in self.dbCursor.fetchall():
            email, firstname, lastname = row
            users.append({'name': firstname + ' ' + lastname, 'email': email})
        return users

    def getUserWithSourceAlerts(self):
        self.log.debug("dbUtils.getUserWithSourceAlerts(): " + _("Start"))
        if (self.dbConnection == None):
            self.openDb()

        dbQuery = "SELECT USE.USE_ID USE_ID, USE.EMAIL EMAIL, USE.FIRSTNAME FIRSTNAME, USE.LASTNAME LASTNAME \
        FROM USERS USE \
        LEFT JOIN USERS_SOURCES USESOU ON USE.USE_ID = USESOU.USE_ID \
        LEFT JOIN SOURCES SOU ON USESOU.SOU_ID = SOU.SOU_ID \
        WHERE USESOU.ALERTS_FLAG = 'Y' \
        GROUP BY USE.USE_ID\
        ORDER BY USE.USERNAME";

        self.dbCursor.execute(dbQuery)
        users = []
        for row in self.dbCursor.fetchall():
            useId, email, firstname, lastname = row

            dbQuery = "SELECT SOU.SOURCEID SOURCEID, SOU.NAME \
            FROM USERS_SOURCES USESOU \
            LEFT JOIN SOURCES SOU ON USESOU.SOU_ID = SOU.SOU_ID \
            WHERE USESOU.ALERTS_FLAG = 'Y' AND USESOU.USE_ID = :useid\
            ORDER BY SOU.SOURCEID";
            self.dbCursor.execute(dbQuery, {'useid': useId})
            userSources = []
            for dbUserSources in self.dbCursor.fetchall():
                sourceId, sourceName = dbUserSources
                userSources.append({'sourceid': sourceId, 'name': sourceName})

            users.append({'useId': useId, 'name': firstname + ' ' + lastname, 'email': email, 'sources': userSources})
        self.closeDb()
        return users

    def getSourcesForUser(self, useId):
        self.log.debug("dbUtils.getSourcesForUser(): " + _("Start"))
        if (self.dbConnection == None):
            self.openDb()

        dbQuery = "SELECT SOU.SOURCEID SOURCEID, SOU.NAME NAME,  USESOU.ALERTS_FLAG ALERTS_FLAG\
        FROM SOURCES SOU \
        LEFT JOIN USERS_SOURCES USESOU ON SOU.SOU_ID = USESOU.SOU_ID \
        WHERE USESOU.USE_ID = :useId\
        ORDER BY SOU.SOURCEID";

        self.dbCursor.execute(dbQuery, {'useId': useId})
        sources = []
        for row in self.dbCursor.fetchall():
            sourceid, name, alertsFlag = row
            sources.append({'sourceid': sourceid, 'name': name, 'alertsFlag': alertsFlag})
        self.closeDb()
        return sources

    def getSourceQuota(self, sourceId):
        self.log.debug("dbUtils.getUsers(): " + _("Start"))
        if (self.dbConnection == None):
            self.openDb()

        dbQuery = "SELECT SOU.QUOTA, SOU.SOURCEID\
        FROM SOURCES SOU \
        WHERE SOU.SOURCEID = :sourceId";

        self.dbCursor.execute(dbQuery, {'sourceId': sourceId})
        for row in self.dbCursor.fetchall():
            quota, sourceid = row
            self.closeDb()
            return quota

    def getSourceName(self, sourceId):
        self.log.debug("dbUtils.getSourceName(): " + _("Start"))
        if (self.dbConnection == None):
            self.openDb()

        dbQuery = "SELECT SOU.NAME, SOU.SOURCEID\
        FROM SOURCES SOU \
        WHERE SOU.SOURCEID = :sourceId";

        self.dbCursor.execute(dbQuery, {'sourceId': sourceId})
        for row in self.dbCursor.fetchall():
            name, sourceid = row
            self.closeDb()
            return name
