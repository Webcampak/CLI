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

import os
from collections import OrderedDict
import json
import shlex, subprocess
import re
import psutil
import glob

from wpakConfigObj import Config
from wpakFileUtils import fileUtils
from wpakTimeUtils import timeUtils

# This class is used to collect various metrics from the system
class statsCollect:
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
		logFilename = statsLogs + "collect.log"
		self.appConfig.set(self.log._meta.config_section, 'file', logFilename)
		self.appConfig.set(self.log._meta.config_section, 'rotate', True)
		self.appConfig.set(self.log._meta.config_section, 'max_bytes', 512000)
		self.appConfig.set(self.log._meta.config_section, 'max_files', 10)
		self.log._setup_file_log()

	# Collect stats from the system and store it in a log file
	# Function: run
	# Description: Start the threads processing process
	# Each thread will get started in its own thread.
	# Return: Nothing
	def run(self):
		self.log.info("statsCollect.run(): Running Stats Collection")

		cfgnow = self.timeUtils.getCurrentDate()
		cfgcurrentday = cfgnow.strftime("%Y%m%d")
		cfgcurrentdaytime = cfgnow.strftime("%Y%m%d%H%M%S")

		cfgnetif = self.configGeneral.getConfig('cfgnetif')

		systemStats = OrderedDict()
		systemStats['date'] = self.timeUtils.getCurrentDateIso()

		self.log.info("Gather Stats: Set timestamp into file:" + self.dirStats + cfgcurrentday + ".txt")
		fileUtils.CheckFilepath(self.dirStats + cfgcurrentday + ".txt")
		StatsFile = Config(self.log, self.dirStats + cfgcurrentday + ".txt")
		StatsFile.setSensor(cfgcurrentdaytime, "", "")
		StatsFile.setSensor(cfgcurrentdaytime, 'Timestamp', cfgnow.strftime("%s"))

		if os.path.isfile("/usr/bin/ifstat"):
			self.log.info("statsCollect.run(): Gathering Bandwidth stats over 10 seconds")
			IfstatCommand = "sudo /usr/bin/ifstat -i " + cfgnetif + " 10 1"
			self.log.info("statsCollect.run(): Running command: " + IfstatCommand)
			args = shlex.split(IfstatCommand)
			p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			output, errors = p.communicate()
			print output
			print errors
			systemStats['BandwidthIn'] = int(float(re.findall("\d+\.\d+", output)[0])*1000)
			systemStats['BandwidthOut'] = int(float(re.findall("\d+\.\d+", output)[1])*1000)
			systemStats['BandwidthTotal'] = systemStats['BandwidthIn'] + systemStats['BandwidthOut']
			#systemStats['BandwidthTotal'] = str(float(re.findall("\d+\.\d+", output)[0]) + float(re.findall("\d+\.\d+", output)[1]))
			StatsFile.setSensor(cfgcurrentdaytime, 'BandwidthIn', systemStats['BandwidthIn'])
			StatsFile.setSensor(cfgcurrentdaytime, 'BandwidthOut', systemStats['BandwidthOut'])
			StatsFile.setSensor(cfgcurrentdaytime, 'BandwidthTotal', systemStats['BandwidthTotal'])

		self.log.info("statsCollect.run(): Gathering Memory usage")
		#memoryusage = psutil.phymem_usage()
		memoryusage = psutil.virtual_memory()

		systemStats['MemoryUsageTotal'] = str(memoryusage.total)
		systemStats['MemoryUsageUsed'] = str(memoryusage.used)
		systemStats['MemoryUsageFree'] = str(memoryusage.free)
		systemStats['MemoryUsagePercent'] = str(memoryusage.percent)
		StatsFile.setSensor(cfgcurrentdaytime, 'MemoryUsageTotal', systemStats['MemoryUsageTotal'])
		StatsFile.setSensor(cfgcurrentdaytime, 'MemoryUsageUsed', systemStats['MemoryUsageUsed'])
		StatsFile.setSensor(cfgcurrentdaytime, 'MemoryUsageFree', systemStats['MemoryUsageFree'])
		StatsFile.setSensor(cfgcurrentdaytime, 'MemoryUsagePercent', systemStats['MemoryUsagePercent'])

		self.log.info("statsCollect.run(): Gathering Disk usage")
		diskusage = psutil.disk_usage('/home/')

		systemStats['DiskUsageTotal'] = str(diskusage.total)
		systemStats['DiskUsageUsed'] = str(diskusage.used)
		systemStats['DiskUsageFree'] = str(diskusage.free)
		systemStats['DiskUsagePercent'] = str(diskusage.percent)
		StatsFile.setSensor(cfgcurrentdaytime, 'DiskUsageTotal', systemStats['DiskUsageTotal'])
		StatsFile.setSensor(cfgcurrentdaytime, 'DiskUsageUsed', systemStats['DiskUsageUsed'])
		StatsFile.setSensor(cfgcurrentdaytime, 'DiskUsageFree', systemStats['DiskUsageFree'])
		StatsFile.setSensor(cfgcurrentdaytime, 'DiskUsagePercent', systemStats['DiskUsagePercent'])

		self.log.info("statsCollect.run(): Gathering CPU usage")
		cpuusage = psutil.cpu_percent(interval=10)
		systemStats['CPUUsagePercent'] = str(cpuusage)
		StatsFile.setSensor(cfgcurrentdaytime, 'CPUUsagePercent', systemStats['CPUUsagePercent'])

		with open(self.dirStats + cfgcurrentday + ".jsonl", "a") as systemStatsFile:
			systemStatsFile.write(json.dumps(systemStats) + "\n")

		self.log.info("statsCollect.run(): Gathering Per-Sources usage")
		# We list all files from configuration directory
		for scanfile in sorted(os.listdir(self.dirEtc), reverse=True):
				if re.findall('config-source[0-9]+.cfg', scanfile):
					sourceid = str(re.findall('\d+', scanfile)[0])
					if os.path.isdir(self.dirSources + "source" + sourceid + "/"):
						self.log.info("statsCollect.run(): Getting details for source: " + sourceid)
						fileUtils.CheckFilepath(self.dirSources + "source" + sourceid + "/resources/stats/" + cfgcurrentday + ".txt")
						sourceStats = OrderedDict()
						sourceStats['date'] = cfgnow.isoformat()
						StatsFile = Config(self.log, self.dirSources + "source" + sourceid + "/resources/stats/" + cfgcurrentday + ".txt")
						if os.path.isdir(self.dirSources + "source" + sourceid + "/pictures/"):
							StatsFile.setSensor('PicDirScan', "", "")
							daysStats = OrderedDict()
							for listpictdir in sorted(os.listdir(self.dirSources + "source" + sourceid + "/pictures/"), reverse=False):
								if listpictdir[:2] == "20" and os.path.isdir(self.dirSources + "source" + sourceid + "/pictures/" + listpictdir):
									self.log.info("statsCollect.run(): Scanning directory:" + self.dirSources + "source" + sourceid + "/pictures/" + listpictdir)
									daysStats[listpictdir] = {'count': len(glob.glob(self.dirSources + "source" + sourceid + "/pictures/" + listpictdir + "/*.jpg")), 'size': fileUtils.CheckDirDu(self.dirSources + "source" + sourceid + "/pictures/" + listpictdir + "/")}
									StatsFile.setSensor('PicDirScan', 'ScannedDay' + listpictdir, [len(glob.glob(self.dirSources + "source" + sourceid + "/pictures/" + listpictdir + "/*.jpg")), fileUtils.CheckDirDu(self.dirSources + "source" + sourceid + "/pictures/" + listpictdir + "/")])
							sourceStats['days'] = daysStats
						StatsFile.setSensor(cfgcurrentdaytime, "", "")
						StatsFile.setSensor(cfgcurrentdaytime, 'Timestamp', cfgnow.strftime("%s"))
						if os.path.isdir(self.dirSources + "source" + sourceid + "/pictures/"):
							sourceStats['PicturesSize'] = fileUtils.CheckDirDu(self.dirSources + "source" + sourceid + "/pictures/")
							StatsFile.setSensor(cfgcurrentdaytime, 'PicturesSize', sourceStats['PicturesSize'])
						if os.path.isdir(self.dirSources + "source" + sourceid + "/videos/"):
							sourceStats['VideoSize'] = fileUtils.CheckDirDu(self.dirSources + "source" + sourceid + "/videos/")
							StatsFile.setSensor(cfgcurrentdaytime, 'VideoSize', sourceStats['VideoSize'])
						if os.path.isdir(self.dirSources + "source" + sourceid + "/"):
							sourceStats['GlobalSize'] = fileUtils.CheckDirDu(self.dirSources + "source" + sourceid + "/")
							StatsFile.setSensor(cfgcurrentdaytime, 'GlobalSize', sourceStats['GlobalSize'])
						with open(self.dirSources + "source" + sourceid + "/resources/stats/" + cfgcurrentday + ".jsonl", "a") as sourceStatsFile:
							sourceStatsFile.write(json.dumps(sourceStats) + "\n")
					else:
						self.log.info("statsCollect.run(): Error, there is no directory for source:" + sourceid)

