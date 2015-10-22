#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       combabase.py
#
#       Copyright 2014 BFR <info@freie-radios.de>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; Version 3 of the License
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, the license can be downloaded here:
#
#       http://www.gnu.org/licenses/gpl.html

# Meta
__version__ = '0.1.1'
__license__ = "GNU General Public License (GPL) Version 3"
__version_info__ = (0, 1, 1)
__author__ = 'Michael Liebler <michael-liebler@radio-z.net>'

"""
Comba Base Class  - lade Config
"""
import os
import sys
import StringIO
import ConfigParser
import socket

class CombaBase(object):

    def set(self, key, value):
        """
        Eine property setzen
        @type    key: string
        @param   key: Der Key
        @type    value: mixed
        @param   value: Beliebiger Wert
        """
        self.__dict__[key] = value

#------------------------------------------------------------------------------------------#
    def get(self, key, default=None):
        """
        Eine property holen
        @type    key: string
        @param   key: Der Key
        @type    default: mixed
        @param   default: Beliebiger Wert

        """
        if not self.__dict__.has_key(key):
            if default:
                self.set(key, default)
            else:
                return None
        return self.__dict__[key]

#------------------------------------------------------------------------------------------#
    def loadConfig(self):
        """
        Set config defaults and load settings from file
        :return:
        """
        ini_path = self.get('configpath', '/etc/comba/comba.ini')

        if not os.path.isfile(ini_path):
            print ini_path + " not found  :("
            sys.exit(1)

        # INI einlesen
        ini_str = '[root]\n' + open(ini_path, 'r').read()

        self.configDefaults = {
            'secondspertrack' : '1800',
            'audiobase' :       '/var/audio/rec',
            'altaudiobase' :    '/var/audio/preprod',
            'calendarurl' :     'http://localhost/index.php?option=com_jimtawl&view=calendar&format=json&from=#datefrom#&to=#dateto#',
            'communication':    'zmq',
            'playlistdir':      '/var/audio/playlists',
            'archivebase':      '/var/audio/archive/',
            'controllerport':   '9099',
            'logdir' :          '/var/log/comba',
            'loglevel':         'info',
            'securitylevel':     '0',
            'adminmail':        '',
            'frommail':        '',
            'calendar_precache_days': '7',
            'servername':        socket.getfqdn(),
            'serviceport':      '8080',
            'stream' : "",
            'stream_type' : "",
            'stream_host' : "",
            'stream_port' : "",
            'stream_mountpoint' : "",
            'stream_admin_user' : "",
            'stream_admin_password' : "",
        }
        # readfp is deprecated since 3.2
        if sys.version_info <= (3, 2):
            ini_str = StringIO.StringIO(ini_str)
            config = ConfigParser.RawConfigParser(self.configDefaults)
            config.readfp(ini_str)
        else:
            config = ConfigParser.ConfigParser(self.configDefaults)
            config.read_string(ini_str)

        for key, value in config.items('root'):
            self.set(key, config.get('root', key).replace('"', '').strip())

