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
import gettext

class captureGphoto(object):
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir
        self.captureClass = parentClass        

        self.configPaths = parentClass.configPaths
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        self.dirSources = self.configPaths.getConfig('parameters')['dir_sources']
        self.dirCache = self.configPaths.getConfig('parameters')['dir_cache']
        self.dirLogs = self.configPaths.getConfig('parameters')['dir_logs']
                    
        self.configGeneral = parentClass.configGeneral
        self.configSource = parentClass.configSource
        self.currentSourceId = parentClass.getSourceId()
        self.currentCaptureDetails = parentClass.currentCaptureDetails
        
        self.dirCurrentSourceTmp = self.dirSources + 'source' + self.currentSourceId +'/' + self.configPaths.getConfig('parameters')['dir_source_tmp']
        
        self.fileUtils = parentClass.fileUtils
        self.captureUtils = parentClass.captureUtils
        self.timeUtils = parentClass.timeUtils        
        self.pictureTransformations = parentClass.pictureTransformations
        self.phidgetsUtils = parentClass.phidgetsUtils
        
                
    # Function: scanPorts
    # Description; This function is used to scan cameras detected by gphoto and write results to a file
    # Return: Console output or null in case of error
    def scanPorts(self):
        self.log.debug(_("captureGphoto.scanPorts(): Start"))                                
        try:            
            args = shlex.split(gphotoScanPortsCommand)
            p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output, errors = p.communicate()
            return output
        except:
            self.log.info(_("captureGphoto.scanPorts(): Gphoto busy"))
            return None

    # Function: getCameraOwner
    # Description; This function is used to get camera owner of a specific camera
    #	Camera Owner is a setting stored in the camera and available via PTP
    # Return: Camera owner
    def getCameraOwner(self, usbport):
        self.log.debug(_("captureGphoto.getCameraOwner(): Start"))                                        
        CmdGphotoSearchOwner = self.configGeneral.getConfig('cfggphotodir') + "gphoto2 --port=" + usbport + " --get-config=/main/settings/ownername"
        import shlex, subprocess
        args = shlex.split(CmdGphotoSearchOwner)
        p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()
        head, sep, CameraOwner = output.partition('Current: ')
        CameraOwner = CameraOwner.strip()
        return CameraOwner

    # Function: cameraLookup
    # Description; This function is used to find a camera and update configuration files accordingly. Only useful in a multi cameras environment
    #	- The function scan gphoto ports which stores results in a file
    #	- The file is analyzed to find cameras USB ports
    #	- If the system is configured to use different cameras (not the same model / brand)
    #		- If the model is found in the scan file, the USB port is updated in the global system configuration file
    #	- If the system is configured to use identical cameras (same model / brand)
    #		- The system will get the camera owner from the USB port of the scan file
    #		- It will try to see if the camera's owner matches owner of the configuration file, 
    #		- If yes the USB port is updated
    ## Gphoto: Gphoto instance
    # Return: Nothing
    def cameraLookup(self):
        self.log.debug("captureGphoto.cameraLookup(): " + _("Start"))        
        if self.configGeneral.getConfig('cfggphotoports') == "yes":
            import filecmp
            self.log.info("captureGphoto.cameraLookup(): " + _("Capture previously failed, checking USB port of the camera"))	
            gphotoPorts = self.scanPorts()
            if gphotoPorts != None: 	
                import re
                for line in gphotoPorts:
                    regexusb = re.compile('usb:...,...')
                    resultusb = regexusb.search(line)
                    regexcamera = re.compile('.*usb:')
                    resultcamera = regexcamera.search(line)
                    self.log.info("captureGphoto.cameraLookup(): " + _("USB Port: %(USBPort)s") % {'USBPort': resultusb.group(0)} )	
                    if self.configGeneral.getConfig('cfggphotoportscameras') == "different":
                        if self.configSource.getConfig('cfgsourcegphotocameramodel') in resultcamera.group(0):
                            self.log.info("captureGphoto.cameraLookup(): " + _("Camera: %(USBCamera)s") % {'USBCamera': resultcamera.group(0)} )	
                            self.log.info("captureGphoto.cameraLookup(): " + _("Camera in config file: %(USBCameraConfig)s") % {'USBCameraConfig': self.configSource.getConfig('cfgsourcegphotocameramodel')} )	
                            self.log.info("captureGphoto.cameraLookup(): " + _("USB Port configured: %(USBPortConfigured)s") % {'USBPortConfigured': self.configSource.getConfig('cfgsourcegphotocameraportdetail')} )	
                            self.log.info("captureGphoto.cameraLookup(): " + _("USB Port detected: %(USBPordDetected)s") % {'USBPordDetected': resultusb.group(0)} )	
                            try:
                                self.log.info("captureGphoto.cameraLookup(): " + _("Modification of the configuration file"))
                                self.configSource.setConfig('cfgsourcegphotocameraportdetail', resultusb.group(0))
                                self.log.info("captureGphoto.cameraLookup(): " + _("New USB Port configured: %(USBPortConfigured)s") % {'USBPortConfigured': self.configSource.getConfig('cfgsourcegphotocameraportdetail')} )	
                            except:
                                self.log.info("captureGphoto.cameraLookup(): " + _("Unable to modify the configuration file"))
                        else:
                            self.log.info("captureGphoto.cameraLookup(): " + _("Unknown camera"))
                    elif self.configGeneral.getConfig('cfggphotoportscameras') == "identical":
                        CameraOwner = self.getCameraOwner(resultusb.group(0))
                        self.log.info("captureGphoto.cameraLookup(): " + _("Configured camera: Port: %(USBPortConfigured)s, Owner: %(OwnerConfigured)s") % {'USBPortConfigured': self.configSource.getConfig('cfgsourcegphotocameraportdetail'), 'OwnerConfigured': self.configSource.getConfig('cfgsourcegphotoowner')} )	
                        self.log.info("captureGphoto.cameraLookup(): " + _("Detected Camera: Port: %(USBPortConfigured)s, Owner: %(OwnerConfigured)s") % {'USBPortConfigured': resultusb.group(0), 'OwnerConfigured': CameraOwner} )	
                        if self.configSource.getConfig('cfgsourcegphotoowner') == CameraOwner and self.configSource.getConfig('cfgsourcegphotocameraportdetail') != resultusb.group(0):
                            self.log.info("captureGphoto.cameraLookup(): " + _("Camera owner identified"))
                            try:
                                self.log.info("captureGphoto.cameraLookup(): " + _("Modification of the configuration file"))
                                self.configSource.setConfig('cfgsourcegphotocameraportdetail', resultusb.group(0))
                                self.log.info("captureGphoto.cameraLookup(): " + _("New USB Port configured: %(USBPortConfigured)s") % {'USBPortConfigured': self.configSource.getConfig('cfgsourcegphotocameraportdetail')} )	
                            except:
                                self.log.info("captureGphoto.cameraLookup(): " + _("Unable to modify the configuration file"))
            else:
                self.log.info("captureGphoto.cameraLookup(): " + _("Call to Gphoto failed"))	
                

    def appendCameraPort(self):    
        self.log.debug(_("captureGphoto.appendCameraPort(): Start"))        
        if self.configSource.getConfig('cfgsourcegphotocameraportdetail') != "automatic" and self.configSource.getConfig('cfgsourcegphotocameraportdetail') != "" and self.configGeneral.getConfig('cfggphotoports') == "yes":
            GphotoPortCommand = '--port=' + self.configSource.getConfig('cfgsourcegphotocameraportdetail')
            self.log.info(_("captureGphoto.capture(): Gphoto: Precision camera port: %(CameraPort)s") % {'CameraPort': self.configSource.getConfig('cfgsourcegphotocameraportdetail')} )
        else:
            GphotoPortCommand = ''
        
        return GphotoPortCommand

    def appendDebugMode(self):    
        self.log.debug(_("captureGphoto.appendDebugMode(): Start"))
        if self.configSource.getConfig('cfgsourcedebug') == "yes":
            GphotoDebugCommand = "--debug --debug-logfile=" + self.dirLogs + "gphoto-debug-source" + str(self.currentSourceId)
            self.log.info(_("captureGphoto.capture(): Gphoto: Debug mode activation"))
        else:
            GphotoDebugCommand = ''        
        return GphotoDebugCommand

    def triggerCapture(self):    
        self.log.debug("captureGphoto.triggerCapture(): " + _("Start"))
        self.currentCaptureDetails.setCaptureValue('captureDate', self.timeUtils.getCurrentSourceTime(self.configSource).isoformat())

        #if self.C.getConfig('cfgsourcegphotocameramodel') != "no":
        #	GphotoCameraCommand = '--camera="' + self.C.getConfig('cfgsourcegphotocameramodel') + '"'
        #	Debug.Display("Capture: Gphoto: Precision modele appareil:" + self.C.getConfig('cfgsourcegphotocameramodel'))									
        #else:              
        GphotoCameraCommand = ''

        GphotoPortCommand = self.appendCameraPort()
        GphotoDebugCommand = self.appendDebugMode()

        self.captureFilename = self.captureClass.getCaptureTime().strftime("%Y%m%d%H%M%S")   
        self.fileUtils.CheckFilepath(self.dirCurrentSourceTmp + self.captureFilename + ".jpg")
        totalCaptureSize = 0

        self.log.info(_("captureGphoto.triggerCapture(): Gphoto: Start Capture"))
        if os.path.isfile(self.configGeneral.getConfig('cfggphotodir') + "gphoto2"):
            import shlex, subprocess
            GphotoCommand = self.configGeneral.getConfig('cfggphotodir') + "gphoto2 --capture-image-and-download " + GphotoDebugCommand + " " + GphotoCameraCommand + " " + GphotoPortCommand + " --filename " + self.dirCurrentSourceTmp + self.captureFilename + ".%C"
            args = shlex.split(GphotoCommand)
            p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            output, errors = p.communicate()
            self.log.info('captureGphoto.triggerCapture() - OUTPUT 1: ' + output)
            self.log.info('captureGphoto.triggerCapture() - OUTPUT 2: ' + errors)

            if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".JPG"):					
                self.log.info(_("captureGphoto.triggerCapture(): Gphoto: Renaming raw picture from .JPG to .jpg"))
                os.rename(self.dirCurrentSourceTmp + self.captureFilename + ".JPG", self.dirCurrentSourceTmp + self.captureFilename + ".jpg")	

            #We rename vendor specific extension to .raw, objective being to have a standard name for raw files
            if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".CR2"):	
                self.log.info(_("captureGphoto.triggerCapture(): Gphoto: Renaming raw picture from .CR2 to .raw"))
                os.rename(self.dirCurrentSourceTmp + self.captureFilename + ".CR2", self.dirCurrentSourceTmp + self.captureFilename + ".raw")

            if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".cr2"):	
                self.log.info(_("captureGphoto.triggerCapture(): Gphoto: Renaming raw picture from .cr2 to .raw"))
                os.rename(self.dirCurrentSourceTmp + self.captureFilename + ".cr2", self.dirCurrentSourceTmp + self.captureFilename + ".raw")

            if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".nef"):	
                self.log.info(_("captureGphoto.triggerCapture(): Gphoto: Renaming raw picture from .nef to .raw"))				
                os.rename(self.dirCurrentSourceTmp + self.captureFilename + ".nef", self.dirCurrentSourceTmp + self.captureFilename + ".raw")		

            if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".nrw"):	
                self.log.info(_("captureGphoto.triggerCapture(): Gphoto: Renaming raw picture from .nrw to .raw"))								
                os.rename(self.dirCurrentSourceTmp + self.captureFilename + ".nrw", self.dirCurrentSourceTmp + self.captureFilename + ".raw")	

            #If raw is not configured, we remove the file		
            if self.configSource.getConfig('cfgprocessraw') != "yes" and os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".raw"):
                self.log.info(_("captureGphoto.triggerCapture(): Gphoto: Raw file not allowed, deleting file"))													
                os.remove(self.dirCurrentSourceTmp + self.captureFilename + ".raw")		

            #If there is only a raw file (i.e. no jpg), we convert raw file to jpg
            if not os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".jpg") and os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".raw"):
                self.log.info(_("captureGphoto.triggerCapture(): Gphoto: No jpg file captured, converting raw file to jpg"))
                import shlex, subprocess
                #dcraw -c 20121030192802.raw | cjpeg -quality 100 -optimize -progressive > 20121030193004.jpg
                #ufraw-batch --out-type=jpeg 20121030193907.raw
                GphotoCommand = "ufraw-batch --out-type=jpeg " + self.dirCurrentSourceTmp + self.captureFilename + ".raw"
                print GphotoCommand
                args = shlex.split(GphotoCommand)
                p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                output, errors = p.communicate()
                self.log.info(_("captureGphoto.triggerCapture(): Gphoto: Conversion to jpg completed"))	

            #if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".jpg"):
            #    return [self.dirCurrentSourceTmp + self.captureFilename + ".jpg"]
            if self.captureUtils.verifyCapturedFile(self.dirCurrentSourceTmp + self.captureFilename + ".jpg"):
                return [self.dirCurrentSourceTmp + self.captureFilename + ".jpg"]
            else:
                self.log.error("captureGphoto.triggerCapture(): " + _("Failed to capture from Camera"))
                if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".jpg"):
                    os.remove(self.dirCurrentSourceTmp + self.captureFilename + ".jpg")
                if os.path.isfile(self.dirCurrentSourceTmp + self.captureFilename + ".raw"):
                    os.remove(self.dirCurrentSourceTmp + self.captureFilename + ".raw")
                return False

    # Function: capture
    # Description; This function is used to capture a picture with gphoto
    # Return: Nothing
    def capture(self):
        self.log.debug("captureGphoto.capture(): " + _("Start"))   
        self.log.info("captureGphoto.capture(): " + _("Initiating capture"))     
        capturedPicture = self.triggerCapture()
        if capturedPicture != False:
            self.log.info("captureGphoto.capture(): " + _("Capture successful"))                               
            return capturedPicture
        self.log.info("captureGphoto.capture(): " + _("Capture failed"))                   
        if self.configSource.getConfig('cfgphidgeterroractivate') == "yes" and self.captureUtils.getCustomCounter('errorcount') < 5:
            # The camera is only rebooted at each failed capture until we get to 5 failed capture, after that the system will not try to restart.
            # Objective is to avoid powercycling the camera indefinitively
            self.log.info("captureGphoto.capture(): " + _("Proceeding with a Phidget restart of the camera (powercycle)"))                   
            self.phidgetsUtils.restartCamera()            
        return capturedPicture
                                       