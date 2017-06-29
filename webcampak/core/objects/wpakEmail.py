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

from datetime import datetime
from wpakDefault import Default

class Email(object):
    """ Builds an object used to send emails"""

    def __init__(self, log, dir_emails = None, dir_schemas = None):
        self.log = log
        self.__dir_emails = dir_emails
        self.__dir_schemas = dir_schemas

        self.__email_filepath = self.__dir_emails + "queued/" + datetime.utcnow().strftime("%Y-%m-%d_%H%M%S_%f") + ".json"
        self.log.info("emailObj(): " + _("Setting default filename to: %(em_fp)s") % {'em_fp': self.__email_filepath})

        # Load schema into memory
        # self.__schema = File.read_json(self.dir_schemas + 'emails.json')

        self.default = Default(self.log, schema_filepath = self.__dir_schemas + 'emails.json', object_filepath = self.__email_filepath)

        # Init default email object
        self.__email = {
            'status': 'queued'
            , 'hash': None
            , 'content': {
                'FROM': []
                , 'TO': []
                , 'CC': []
                , 'BODY': None
                , 'SUBJECT': None
                , 'ATTACHMENTS': []
            }
            , 'logs': []
        }

    @property
    def email(self):
        return self.__email

    @email.setter
    def email(self, email):
        self.__email = email

    @property
    def email_filepath(self):
        return self.__email_filepath

    @email_filepath.setter
    def email_filepath(self, email_filepath):
        self.__email_filepath = email_filepath

    @property
    def status(self):
        return self.__email['status']

    @status.setter
    def status(self, status):
        self.__email['status'] = status

    @property
    def email_hash(self):
        return self.__email['hash']

    @email_hash.setter
    def email_hash(self, email_hash):
        self.__email['hash'] = email_hash

    @property
    def field_from(self):
        return self.__email['content']['FROM']

    @field_from.setter
    def field_from(self, field_from):
        self.__email['content']['FROM'] = field_from

    @property
    def field_to(self):
        return self.__email['content']['TO']

    @field_to.setter
    def field_to(self, field_to):
        self.__email['content']['TO'] = field_to

    @property
    def field_cc(self):
        return self.__email['content']['CC']

    @field_cc.setter
    def field_cc(self, field_cc):
        self.__email['content']['CC'] = field_cc

    @property
    def field_bcc(self):
        return self.__email['content']['BCC']

    @field_bcc.setter
    def field_bcc(self, field_bcc):
        self.__email['content']['BCC'] = field_bcc

    @property
    def body(self):
        return self.__email['content']['BODY']

    @body.setter
    def body(self, body):
        self.__email['content']['BODY'] = body

    @property
    def subject(self):
        return self.__email['content']['SUBJECT']

    @subject.setter
    def subject(self, subject):
        self.__email['content']['SUBJECT'] = subject

    @property
    def attachments(self):
        return self.__email['content']['ATTACHMENTS']

    @attachments.setter
    def attachments(self, attachments):
        self.__email['content']['ATTACHMENTS'] = attachments

    def send(self):
        """Send an email object, effectively taking an object and writing it to a file in the queue directory"""
        self.default.save(self.email)

