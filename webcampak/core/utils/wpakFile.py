#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2010-2017 Eurotechnia (support@webcampak.com)
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
import json

class File:
    @staticmethod
    def check_filepath(filepath):
        d = os.path.dirname(filepath)
        if not os.path.exists(d):
            os.makedirs(d)
        return filepath

    @staticmethod
    def read_file(filepath):
        """return content of a file"""
        if os.path.isfile(filepath):
            f = open(filepath, 'r')
            try:
                file_content = f.read()
                f.close()
                return file_content
            except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                print(message)
                print('File.read_file() - Unable to open file: ' + filepath)
                exit()
        return None

    @staticmethod
    def write_json(filepath, content):
        """Write the content of a dictionary to a JSON file"""
        if File.check_filepath(filepath) != "":
            try:
                with open(filepath, "w") as threadJsonFile:
                    threadJsonFile.write(json.dumps(content))
                return True
            except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                print(message)
                print('File.write_json() - Unable to write to file: ' + filepath)
                print(content)
                exit()

    @staticmethod
    def read_json(filepath):
        """Loads the content of a JSON file"""
        if os.path.isfile(filepath):
            with open(filepath) as json_file:
                json_obj = json.load(json_file)
                return json_obj
