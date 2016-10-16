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
import subprocess
import shlex
from timeit import default_timer as timer

from wpakConfigObj import Config
from wpakFileUtils import fileUtils


class pictureTransformations:
    def __init__(self, parentClass):
        self.log = parentClass.log
        self.config_dir = parentClass.config_dir
        
        self.configPaths = parentClass.configPaths        
        self.dirEtc = self.configPaths.getConfig('parameters')['dir_etc']
        
        self.configGeneral = parentClass.configGeneral
        self.dirImageMagick = self.configGeneral.getConfig('cfgmagickdir')
                
        self.fileUtils = parentClass.fileUtils
        #self.fileUtils.setCurrentSourceId(parentClass.getSourceId())
        
        self.sourcePath = None
        self.destinationPath = None
        
    # Getters and Setters
    def setFilesourcePath(self, path):
        self.log.debug("pictureTransformations.setFilesourcePath(): " + _("FilePath: %(path)s") % {'path': path} )
        self.sourcePath = path
        
    def getFilesourcePath(self):
        return self.sourcePath
    
    def setFiledestinationPath(self, path):
        self.log.debug("pictureTransformations.setFiledestinationPath(): " + _("FilePath: %(path)s") % {'path': path} )
        self.destinationPath = path
        
    def getFiledestinationPath(self):
        return self.destinationPath    

    def resize(self, pictureSize):
        """ Resize a picture
            
        Args:
            pictureSize: A string, size of the picture, using WIDTHxHEIGHT format
        
        Returns:
            None
        """         
        self.log.debug("pictureTransformations.resize(): " + _("Start"))                                            
        if pictureSize != "":
            if os.path.isfile(self.dirImageMagick + "convert"):
                startTimer = timer()                            
                subprocess.check_call([self.dirImageMagick + "convert", self.getFilesourcePath(), "-scale", pictureSize + '!', self.getFiledestinationPath()])
                endTimer = timer()                
                self.log.info("pictureTransformations.resize(): " + _("Resized picture to %(pictureSize)s in %(timer)s ms") % {'pictureSize': pictureSize, 'timer': int((endTimer - startTimer) * 1000)} )
            else:
                self.log.debug(_("Error: Convert binary (ImageMagick) not found"))
                sys.exit()

    def crop(self, Width, Height, XPos, YPos):
        """ Cropping a picture
            
        Args:
            Width: An int,  Width of the area to be kept
            Height: An int, Height of the area to be kept
            XPos: An int, X coordinate of the top-left corner of the cropped area from the top-left corner of the picture
            YPos:An int, Y coordinate of the top-left corner of the cropped area from the top-left corner of the picture
        
        Returns:
            None
        """         
        self.log.debug("pictureTransformations.crop(): " + _("Start")) 
        if os.path.isfile(self.dirImageMagick + "convert"):
            startTimer = timer()            
            convert = subprocess.check_call([self.dirImageMagick + "convert", self.getFilesourcePath(), "-crop", Width + 'x' + Height + '+' + XPos + '+' + YPos + '!', self.getFiledestinationPath()])
            endTimer = timer()
            self.log.info("pictureTransformations.crop(): " + _("Cropped zone size: %(Width)sx%(Height)s Position: x: %(XPos)s y: %(YPos)s in %(timer)s ms") % {'Width': Width, 'Height': Height, 'XPos': XPos, 'YPos': YPos, 'timer': int((endTimer - startTimer) * 1000)} )            
        else:
            self.log.debug("pictureTransformations.crop(): " + _("Error: Convert binary (ImageMagick) not found"))
            sys.exit()

    def rotate(self, rotateAngle):
        """ Rotate a picture
            
        Args:
            rotateAngle: A string, Angle in degrees to rotate the picture by
        
        Returns:
            None
        """           
        self.log.debug("pictureTransformations.rotate(): " + _("Start")) 
        if os.path.isfile(self.dirImageMagick + "convert"):
            startTimer = timer()
            subprocess.check_call([self.dirImageMagick + "convert", self.getFilesourcePath(), "-rotate", rotateAngle, self.getFiledestinationPath()])
            endTimer = timer()
            self.log.info("pictureTransformations.rotate(): " + _("Rotated picture by %(rotateAngle)s degrees in %(timer)s ms") % {'rotateAngle': rotateAngle, 'timer': int((endTimer - startTimer) * 1000)} )            
        else:
            self.log.info("pictureTransformations.rotate(): " + _("Error: Convert binary (ImageMagick) not found"))
            sys.exit()

    # Function: Border 
    # Description; Add a border to an image
    # convert rose: -bordercolor #ffffff -border 10%x10%  border_percent.jpg
    ## Color: Color of the border
    ## HBorder: Horizontal border width (in px or %)
    ## VBorder: Vertical border width (in px or %)
    # Return: Nothing
    def Border(self, Color, HBorder, VBorder, NewPath):
        self.log.debug(_("pictureTransformations.Border(): Start")) 
        if os.path.isfile(self.dirImageMagick + "convert"):
            self.fileUtils.CheckDir(NewPath)
            self.log.info("pictureTransformations.Border(): " + _("Color: %(Color)s Width: %(BorderWidth)s") % {'Color': Color, 'BorderWidth': HBorder + ":" + VBorder} )
            convert = subprocess.check_call([self.dirImageMagick + "convert", self.getFilesourcePath(), "-bordercolor", Color, "-border", HBorder + 'x' + VBorder, NewPath])
        else:
            self.log.debug(_("Error: Convert binary (ImageMagick) not found"))
            sys.exit()

    def Watermark(self, XPos, YPos, Dissolve, Watermarkfile):
        """ Add a watermark to a picture
            
        Args:
            XPos: An int, X coordinate of the top-left corner of the watermark from the top-left corner of the picture
            YPos: An int, Y coordinate of the top-left corner of the cropped area from the top-left corner of the picture
            Dissolve: An int, % of transparency of the included image
            Watermarkfile: An int, Watermarkfile: Watermark file
        
        Returns:
            None
        """          
        self.log.debug("pictureTransformations.Watermark(): " + _("Start")) 
        if os.path.isfile(self.dirImageMagick + "composite"):
            startTimer = timer()            
            composite = subprocess.check_call([self.dirImageMagick + "composite", "-dissolve", Dissolve + '%', "-geometry", '+' + XPos + '+' + YPos, Watermarkfile, self.getFilesourcePath(), self.getFiledestinationPath()])
            endTimer = timer()
            self.log.info("pictureTransformations.Watermark(): " + _("Added watermark file %(Watermarkfile)s at position: x: %(XPos)s y: %(YPos)s Transparency: %(Dissolve)s percent in %(timer)s ms") % {'Watermarkfile': Watermarkfile, 'XPos': XPos, 'YPos': YPos, 'Dissolve': Dissolve, 'timer': int((endTimer - startTimer) * 1000)} )
        else:
            self.log.debug("pictureTransformations.Watermark(): " + _("Error: Composite binary (ImageMagick) not found"))
            sys.exit()

    def Text(self, Cfgimgtextfont, Cfgimgtextsize, Cfgimgtextgravity, Cfgimgtextbasecolor, Cfgimgtextbaseposition, Cfgimgtext, Cfgdisplaydate, Cfgimgtextovercolor, Cfgimgtextoverposition):
        """ Add some text to a picture
            
        Args:
            Cfgimgtextfont: A string, font to be used
            Cfgimgtextsize: An int
            Cfgimgtextgravity: A string
            Cfgimgtextbasecolor: A string
            Cfgimgtextbaseposition: A string
            Cfgimgtext: A string
            Cfgdisplaydate: A string
            Cfgimgtextovercolor: A string
            Cfgimgtextoverposition: A string
        
        Returns:
            None
        """          
        self.log.debug("pictureTransformations.Text(): " + _("Start")) 
        if os.path.isfile(self.dirImageMagick + "convert"):
            startTimer = timer()                        
            mogrify = subprocess.check_call([self.dirImageMagick + "convert", "-font", Cfgimgtextfont, "-pointsize", Cfgimgtextsize, "-draw", "gravity " + Cfgimgtextgravity + " fill " + Cfgimgtextbasecolor + " text " + Cfgimgtextbaseposition + " '" + Cfgimgtext + Cfgdisplaydate + "' fill " + Cfgimgtextovercolor + " text " + Cfgimgtextoverposition + " '" + Cfgimgtext + Cfgdisplaydate + "' ", self.getFilesourcePath(),  self.getFiledestinationPath()])
            endTimer = timer()
            self.log.info("pictureTransformations.Text(): " + _("Added text to the picture: %(Text)s Font: %(Cfgimgtextfont)s Gravity: %(Cfgimgtextgravity)s in %(timer)s ms") % {'Text': Cfgimgtext + Cfgdisplaydate, 'Cfgimgtextfont': Cfgimgtextfont, 'Cfgimgtextgravity': Cfgimgtextgravity, 'timer': int((endTimer - startTimer) * 1000)} )
        else:
            self.log.debug("pictureTransformations.Text(): " + _("Error: Composite binary (ImageMagick) not found"))
            sys.exit()

    # Function: Sketch 
    # Description; Add a sketch effect to a picture
    # Return: Nothing			
    def Sketch(self, TargetDir):
        self.log.debug("pictureTransformations.Sketch(): " + _("Start")) 
        if os.path.isfile(TargetDir + "pencil_tile.gif") == False:
            Command = self.dirImageMagick + "convert -size 640x480 xc: +noise Random  -virtual-pixel tile -motion-blur 0x20+135 -charcoal 1 -resize 50% " + TargetDir + "pencil_tile.gif"
            self.log.info("pictureTransformations.Sketch(): " + _("Running command to generate pencil tile: %(Command)s") % {'Command': Command})
            args = shlex.split(Command)
            p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            p.communicate()
        Command = self.dirImageMagick + "convert " + self.getFilesourcePath() + " -colorspace gray \( +clone -tile " + TargetDir + "pencil_tile.gif -draw \"color 0,0 reset\" +clone +swap -compose color_dodge -composite \) -fx 'u*.2+v*.8' " + self.getFiledestinationPath()
        self.log.info("pictureTransformations.Sketch(): " + _("Running command to creaste sketch: %(Command)s") % {'Command': Command})
        args = shlex.split(Command)
        p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        p.communicate()

    # Function: TiltShift 
    # Description; Add a tiltshift effect to a picture
    # Return: Nothing	
    def TiltShift(self):    
        self.log.debug(_("pictureTransformations.TiltShift(): Start")) 
        Command = self.dirImageMagick + "convert " + self.getFilesourcePath() + " -sigmoidal-contrast 15x30% ( +clone -sparse-color Barycentric '0,0 black 0,%[fx:h-1] gray80' -solarize 50% -level 50%,0 )  -compose Blur -set option:compose:args 15 -composite " + self.getFiledestinationPath()
        self.log.info("pictureTransformations.TiltShift(): " + _("Running command to create tiltshift effect: %(Command)s") % {'Command': Command})
        args = shlex.split(Command)
        p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()

    # Function: Charcoal 
    # Description; Add a charcoal effect to a picture
    # Return: Nothing
    def Charcoal(self):   
        self.log.debug(_("pictureTransformations.Charcoal(): Start"))  
        Command = self.dirImageMagick + "convert " + self.getFilesourcePath() + " -charcoal 5 " + self.getFiledestinationPath()
        self.log.info("pictureTransformations.Charcoal(): " + _("Running command to create charcoal effect: %(Command)s") % {'Command': Command})
        args = shlex.split(Command)
        p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()

    # Function: ColorIn 
    # Description; Add a colorin effect to a picture
    # Return: Nothing
    def ColorIn(self):    
        self.log.debug(_("pictureTransformations.ColorIn(): Start")) 
        Command = self.dirImageMagick + "convert " + self.getFilesourcePath() + " -edge 1 -negate -normalize -colorspace Gray -blur 0x.5 -contrast-stretch 0x50% " + self.getFiledestinationPath()
        self.log.info("pictureTransformations.ColorIn(): " + _("Running command to create color-in effect: %(Command)s") % {'Command': Command})
        args = shlex.split(Command)
        p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()

    # Function: VirtualPixel 
    # Description; Blur the picture by a specified vector (in pixels)
    # Return: Nothing
    def VirtualPixel(self, PixelsSpread):  
        self.log.debug(_("pictureTransformations.VirtualPixel(): Start")) 
        self.log.info(_("pictureTransformations.VirtualPixel(): Applying a spread of: %(PixelsSpread)s pixels") % {'PixelsSpread': PixelsSpread} )            
        Command = self.dirImageMagick + "convert " + self.getFilesourcePath() + " -interpolate nearest -virtual-pixel mirror -spread " + str(PixelsSpread) + " " + self.getFiledestinationPath()
        self.log.info(_("pictureTransformations.VirtualPixel(): Running Command: %(Command)s") % {'Command': Command} )                    
        import shlex, subprocess
        args = shlex.split(Command)
        p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output, errors = p.communicate()                

