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
import datetime
from pytz import timezone
import shutil
import pytz
import json
import dateutil.parser
import random
import time
import zlib
from dateutil import tz
from collections import OrderedDict
import json
import shlex, subprocess
import re
import psutil
import glob

from wpakConfigObj import Config
from wpakFileUtils import fileUtils
from wpakTimeUtils import timeUtils
#from wpakXferUtils import xferUtils
#from wpakFTPTransfer import FTPTransfer

# This class is used to start & process stored in the transfer queue 

class statsConsolidate:
    def __init__(self, log, appConfig, config_dir):
        self.log = log
        self.appConfig = appConfig                        
        self.config_dir = config_dir
        self.configPaths = Config(self.log, self.config_dir + 'param_paths.yml')


        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirConfig = self.configPaths.getConfig('parameters')['dir_config']
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']
        self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']
        self.dirStats = self.configPaths.getConfig('parameters')['dir_stats']
                        
        self.setupLog()
                                                
        self.configGeneral = Config(self.log, self.dirConfig + 'config-general.cfg')
        self.cfgLogfile = "gatherstats.log"
        
        self.timeUtils = timeUtils(self)
    
    def setupLog(self):      
        """ Setup logging to file """
        statsLogs = self.dirLogs + "stats/"
        if not os.path.exists(statsLogs):
            os.makedirs(statsLogs)  
        logFilename = statsLogs + "consolidate.log"
        self.appConfig.set(self.log._meta.config_section, 'file', logFilename)
        self.appConfig.set(self.log._meta.config_section, 'rotate', True)
        self.log._setup_file_log()
        
    # Collect stats from the system and store it in a log file
    # Function: run
    # Description: Start the threads processing process
    # Each thread will get started in its own thread.
    # Return: Nothing           
    def run(self):
        self.log.info("statsConsolidate.run(): Running Stats Collection")

        # The following call will convert all .txt to .jsonl files
        #convertTxtArchive(g, self.dirStats)
        #convertTxtArchive(g, '/home/webcampak/webcampak/sources/source1/resources/stats/')

        #1- Convert start - with days (contains hours), month (contains days), and year (contains months)
        self.log.info("statsConsolidate.run(): Step 1: Crunching hours")
        skipCount = 0
        for scanFile in sorted(os.listdir(self.dirStats), reverse=True):
            if os.path.splitext(scanFile)[1].lower() == '.jsonl' and len(os.path.splitext(scanFile)[0]) == 8 and skipCount < 2:
                skipCount = self.checkProcessFile(scanFile, "consolidated/" + scanFile, skipCount, '23:55', 11, 16)
                dayStats = self.parseSourceHoursFile(scanFile)
                dayStats = self.crunchHourFile(dayStats)
                dayStats = self.saveHourFile(dayStats, scanFile)

        #2- Convert Months, using days previously converted
        self.log.info("statsConsolidate.run(): Step 2: Crunching days")        
        skipCount = 0
        for scanFile in sorted(os.listdir(self.dirStats + "/consolidated"), reverse=True):
            #201601.jsonl
            monthFile = scanFile[0:6] + '.jsonl'
            if os.path.splitext(scanFile)[1].lower() == '.jsonl' and len(os.path.splitext(scanFile)[0]) == 8 and skipCount < 2:
                skipCount = self.checkProcessFile("consolidated/" + scanFile, "consolidated/" + monthFile,  skipCount, '31', 8, 10)
                print 'COUNT: ' + str(skipCount)
                dayStats = self.parseSourceDaysFile(scanFile)
                dayStats = self.crunchDayFile(dayStats)
                dayStats = self.saveDayFile(dayStats, monthFile)                

        #3- Convert Years
        self.log.info("statsConsolidate.run(): Step 2: Crunching years")                
        for scanFile in sorted(os.listdir(self.dirStats + "/consolidated"), reverse=True):
            if len(os.path.splitext(scanFile)[0]) == 4:
                os.remove(self.dirStats + "consolidated/" + scanFile) 
        
        skipCount = 0
        for scanFile in sorted(os.listdir(self.dirStats + "/consolidated"), reverse=True):
            #201601.jsonl
            yearFile = scanFile[0:4] + '.jsonl'
            if os.path.splitext(scanFile)[1].lower() == '.jsonl' and len(os.path.splitext(scanFile)[0]) == 6 and skipCount < 3:
                #skipCount = self.checkProcessFile(g, self.dirStats + "consolidated/" + scanFile, self.dirStats + "consolidated/" + yearFile,  skipCount, '31', 8, 10)
                #print 'COUNT: ' + str(skipCount)
                dayStats = self.parseSourceMonthsFile(scanFile)
                dayStats = self.crunchDayFile(dayStats)
                dayStats = self.saveDayFile(dayStats, yearFile)           

        
    def convertTxtArchive(self, targetDirectory):
        self.log.info("statsConsolidate.convertTxtArchive(): Directory: " + targetDirectory)                        
        # Parse and convert all .txt files into jsonl to get a good starting point
        for statFile in sorted(os.listdir(targetDirectory), reverse=True):
            if os.path.splitext(statFile)[1].lower() == '.txt' and statFile[0:3] == '201':
                self.log.info("statsConsolidate.convertTxtArchive(): Currently processing file: " + statFile)                        
                
                # Check if file exists, if yes, deleting
                if os.path.isfile(targetDirectory + os.path.splitext(statFile)[0].lower() + ".jsonl"):
                    self.log.info("statsConsolidate.convertTxtArchive(): Json counterpart exists, deleting... " + statFile)                                            
                    os.remove(targetDirectory + os.path.splitext(statFile)[0].lower() + ".jsonl")

                configObjStatsFile = ConfigObj(targetDirectory + statFile)
                for configTime in configObjStatsFile.keys():
                    # Exception for picture source file
                    if configTime == 'PicDirScan':
                        #ScannedDay20151220 = 9, 88784158                    
                        daysStats = OrderedDict()
                        for configParam in configObjStatsFile[configTime].keys():
                            currentDay = configParam[10:18]
                            daysStats[currentDay] = {'count': configObjStatsFile[configTime][configParam][0], 'size': configObjStatsFile[configTime][configParam][1]}                        
                        #{"date": "2016-02-16T03:10:30.048079+01:00", "days": {"20151220": {"count": 9, "size": "88784158"}, "20151221": {"count": 3, "size": "28503586"}, "20160131": {"count": 1, "size": "10806290"}, "20160201": {"count": 17, "size": "175090473"}, "20160202": {"count": 6, "size": "60198023"}, "20160214": {"count": 33, "size": "333103769"}, "20160215": {"count": 73, "size": "734524652"}}, "PicturesSize": "1431015047", "VideoSize": "4096", "GlobalSize": "1445014635"}
                    else:                
                        # Get date from section title
                        dateString = configTime[0:4] + "/" + configTime[4:6] + "/" + configTime[6:8] + "/" + configTime[8:10] + "/" + configTime[10:12] + "/" + configTime[12:14]
                        currentTime = datetime.datetime.strptime(dateString, "%Y/%m/%d/%H/%M/%S")    
                        currentTime = currentTime.replace(tzinfo=tz.gettz('UTC'))	

                        systemStats = OrderedDict()
                        systemStats['date'] = currentTime.isoformat()  
                        if 'daysStats' in locals() or 'daysStats' in globals():
                            systemStats['days'] = daysStats

                        for configParam in configObjStatsFile[configTime].keys():
                            systemStats[configParam] = configObjStatsFile[configTime][configParam]

                        #print json.dumps(systemStats)
                        with open(targetDirectory + os.path.splitext(statFile)[0].lower() + ".jsonl", "a") as systemStatsFile:
                            systemStatsFile.write(json.dumps(systemStats) + "\n")    

    #Take a jsonl as an input, group everything by Hour, each hours containing a list of values for each index
    def parseSourceHoursFile(self, scanFile):
        self.log.info("statsConsolidate.parseSourceHoursFile() - Processing Hours file: " + scanFile)        
        dayStats = OrderedDict()
        # Start with days
        for line in reversed(open(self.dirStats + scanFile).readlines()):
            currentStatsLine = json.loads(line, object_pairs_hook=OrderedDict)
            currentStatsLine['date'] = dateutil.parser.parse(currentStatsLine['date'])
            newDate = currentStatsLine['date'].replace(minute=0, second=0, microsecond=0)
            if newDate not in dayStats:
                dayStats[newDate] = OrderedDict()
                dayStats[newDate]['date'] = newDate
            for dictIndex in currentStatsLine.keys():
                if dictIndex != 'date' and dictIndex != 'Timestamp':
                    if dictIndex not in dayStats[newDate]:
                        dayStats[newDate][dictIndex] = OrderedDict()
                        dayStats[newDate][dictIndex]['list'] = []
                    #dayStats[newDate][dictIndex]['list'].append(float(currentStatsLine[dictIndex]))
                    dayStats[newDate][dictIndex]['list'].append(float(currentStatsLine[dictIndex]))                
        return dayStats

    def parseSourceDaysFile(self, scanFile):
        self.log.info("statsConsolidate.parseSourceDaysFile() - Processing Days file: " + scanFile)        
        dayStats = OrderedDict()
        # Start with days
        for line in reversed(open(self.dirStats + "consolidated/" + scanFile).readlines()):
            currentStatsLine = json.loads(line, object_pairs_hook=OrderedDict)
            currentStatsLine['date'] = dateutil.parser.parse(currentStatsLine['date'])
            newDate = currentStatsLine['date'].replace(hour=0, minute=0, second=0, microsecond=0)
            if newDate not in dayStats:
                dayStats[newDate] = OrderedDict()
                dayStats[newDate]['date'] = newDate
            for dictIndex in currentStatsLine.keys():
                if dictIndex != 'date' and dictIndex != 'Timestamp':
                    if dictIndex not in dayStats[newDate]:
                        dayStats[newDate][dictIndex] = OrderedDict()
                        dayStats[newDate][dictIndex]['listmin'] = []
                        dayStats[newDate][dictIndex]['listmax'] = []
                        dayStats[newDate][dictIndex]['listavg'] = []
                    #dayStats[newDate][dictIndex]['list'].append(float(currentStatsLine[dictIndex]))
                    dayStats[newDate][dictIndex]['listmin'].append(float(currentStatsLine[dictIndex]['min']))                
                    dayStats[newDate][dictIndex]['listmax'].append(float(currentStatsLine[dictIndex]['max']))                
                    dayStats[newDate][dictIndex]['listavg'].append(float(currentStatsLine[dictIndex]['avg']))   
        return dayStats

    def parseSourceMonthsFile(self, scanFile):
        self.log.info("statsConsolidate.parseSourceMonthsFile() - Processing Months file: " + scanFile)                
        dayStats = OrderedDict()
        # Start with days
        for line in reversed(open(self.dirStats + "consolidated/" + scanFile).readlines()):
            currentStatsLine = json.loads(line, object_pairs_hook=OrderedDict)
            currentStatsLine['date'] = dateutil.parser.parse(currentStatsLine['date'])
            newDate = currentStatsLine['date'].replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if newDate not in dayStats:
                dayStats[newDate] = OrderedDict()
                dayStats[newDate]['date'] = newDate
            for dictIndex in currentStatsLine.keys():
                if dictIndex != 'date' and dictIndex != 'Timestamp':
                    if dictIndex not in dayStats[newDate]:
                        dayStats[newDate][dictIndex] = OrderedDict()
                        dayStats[newDate][dictIndex]['listmin'] = []
                        dayStats[newDate][dictIndex]['listmax'] = []
                        dayStats[newDate][dictIndex]['listavg'] = []
                    #dayStats[newDate][dictIndex]['list'].append(float(currentStatsLine[dictIndex]))
                    dayStats[newDate][dictIndex]['listmin'].append(float(currentStatsLine[dictIndex]['min']))                
                    dayStats[newDate][dictIndex]['listmax'].append(float(currentStatsLine[dictIndex]['max']))                
                    dayStats[newDate][dictIndex]['listavg'].append(float(currentStatsLine[dictIndex]['avg']))   
        return dayStats

    # Taking the lists perviously built, calculate min, max and avg    
    def crunchHourFile(self, dayStats):
        self.log.info("statsConsolidate.crunchHourFile() - Start")
        for dayHour in dayStats.keys():
            for dictIndex in dayStats[dayHour].keys():
                if dictIndex != 'date':
                    #print dayStats[dayHour][dictIndex]['list']
                    dayStats[dayHour][dictIndex]['min'] = int(min(dayStats[dayHour][dictIndex]['list']))
                    dayStats[dayHour][dictIndex]['max'] = int(max(dayStats[dayHour][dictIndex]['list']))
                    dayStats[dayHour][dictIndex]['avg'] = int(sum(dayStats[dayHour][dictIndex]['list'])/len(dayStats[dayHour][dictIndex]['list']))
                    del dayStats[dayHour][dictIndex]['list']
                else:
                    dayStats[dayHour]['date'] = dayStats[dayHour]['date'].isoformat()  
        return dayStats

    # Taking the lists perviously built, calculate min, max and avg    
    def crunchDayFile(self, dayStats):
        self.log.info("statsConsolidate.crunchDayFile() - Start")        
        for dayHour in dayStats.keys():
            for dictIndex in dayStats[dayHour].keys():
                if dictIndex != 'date':
                    #print dayStats[dayHour][dictIndex]['list']
                    dayStats[dayHour][dictIndex]['min'] = int(min(dayStats[dayHour][dictIndex]['listmin']))
                    dayStats[dayHour][dictIndex]['max'] = int(max(dayStats[dayHour][dictIndex]['listmax']))
                    dayStats[dayHour][dictIndex]['avg'] = int(sum(dayStats[dayHour][dictIndex]['listavg'])/len(dayStats[dayHour][dictIndex]['listavg']))
                    del dayStats[dayHour][dictIndex]['listmin']
                    del dayStats[dayHour][dictIndex]['listmax']
                    del dayStats[dayHour][dictIndex]['listavg']
                else:
                    dayStats[dayHour]['date'] = dayStats[dayHour]['date'].isoformat()  
        return dayStats    

    # Save crunched numbers to file
    def saveHourFile(self, dayStats, scanFile):
        self.log.info("statsConsolidate.saveHourFile() - Start")
        if os.path.isfile(self.dirStats + "consolidated/" + scanFile):
            self.log.info("statsConsolidate.saveHourFile() - Json file:  exists, deleting... " + self.dirStats + "consolidated/" + scanFile)            
            os.remove(self.dirStats + "consolidated/" + scanFile)   
        for dayHour in reversed(dayStats.keys()):
            with open(self.dirStats + "consolidated/" + scanFile, "a") as consolidatedStatFile:
                consolidatedStatFile.write(json.dumps(dayStats[dayHour]) + "\n")       

    def prependLine(self, filename, line):
        with open(filename, 'r+') as f:
            content = f.read()
            f.seek(0, 0)
            f.write(line.rstrip('\r\n') + '\n' + content)

    # Save crunched numbers to file
    def saveDayFile(self, dayStats, scanFile):
        self.log.info("statsConsolidate.saveHourFile() - Start")        
        if os.path.isfile(self.dirStats + "consolidated/" + scanFile):
            for dayHour in reversed(dayStats.keys()):
                self.prependLine(self.dirStats + "consolidated/" + scanFile, json.dumps(dayStats[dayHour]) + "\n")
        else:
            for dayHour in reversed(dayStats.keys()):
                with open(self.dirStats + "consolidated/" + scanFile, "a") as consolidatedStatFile:
                    consolidatedStatFile.write(json.dumps(dayStats[dayHour]) + "\n")    


    # Identify if we want to process this file
    # If scanned date is 23:55 and target file  exists then increase count
    def checkProcessFile(self, sourceFile, targetFile, skipCount, searchTime, searchStart, searchEnd):
        self.log.info("statsConsolidate.checkProcessFile() - File: " + sourceFile)                
        for line in reversed(open(self.dirStats + sourceFile).readlines()):
            currentStatsLine = json.loads(line, object_pairs_hook=OrderedDict)
            #if currentStatsLine['date'][11:16] == searchTime and os.path.isfile(targetFile):
            if currentStatsLine['date'][searchStart:searchEnd] == searchTime and os.path.isfile(targetFile):
                return skipCount+1
            else:
                return skipCount
