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
Comba Audio Class  -
"""
import os, sys, subprocess
import wave
import contextlib
import mutagen
import magic

import wave
import contextlib



class CombaAudiotools():

    def __init__(self):
        pass

    def combine_audiofiles(self, files, folder, outfile, clean=True, nice=14, wait=True, params = []):
        if not len(files):
            return

        folder = str(folder).replace('//', '/')

        parentfolder = os.path.abspath(os.path.join(folder, os.path.pardir))

        uid = os.stat(parentfolder).st_uid
        gid = os.stat(parentfolder).st_gid

        if not os.path.exists(folder):
            os.mkdir(folder, 0755)
            os.chmod(folder, 0755)
            try:
                os.chown(folder, uid, gid)
            except:
                pass

        # Name der Audiodatei, die angelegt werden muss
        tmp_out_file = folder +  "tmp-" + outfile
        out_file = folder + outfile
        command = ["nice","-n",str(nice),"sox"]

        for file in files:
            if os.path.exists(file):
                command.append(file)

        for param in params:
            command.append(param)

        command.append(tmp_out_file)
        p = subprocess.Popen(command)

        p.wait()
        if clean:
            for file in files:
                if os.path.exists(file):
                    os.remove(file)

        os.rename(tmp_out_file, out_file)
        try:
            os.chmod(out_file, 0644)
            os.chown(out_file, uid, gid)
        except:
            pass

    def get_wav_info(self, path):
        info = {'length':0,'bitrate':0,'channels':0}
        with contextlib.closing(wave.open(path,'r')) as f:
            frames = f.getnframes()
            info['bitrate'] = f.getframerate()
            info['channels'] = f.getnchannels()
            info['length'] = frames / float(info['bitrate'])
        return info


    def get_mp3_info(self, path):
        from mutagen.mp3 import MP3
        info = {'length':0,'bitrate':0,'channels':0}
        try:
            audio = MP3(path)
            try:
                info['length'] = audio.info.length
            except:
                pass
            try:
                info['bitrate'] = audio.info.bitrate
            except:
                pass
            try:
                info['channels'] = 2 if audio.info.mode < 3 else 1
            except:
                pass
            return info
        except:
            return {'length':0,'bitrate':0,'channels':0}

    def get_ogg_info(self, path):
        from mutagen.oggvorbis import OggVorbis
        info = {'length':0,'bitrate':0,'channels':0}
        try:
            audio = OggVorbis(path)
            try:
                info['length'] = audio.info.length
            except:
                pass
            try:
                info['bitrate'] = audio.info.bitrate
            except:
                pass
            try:
                info['channels'] = audio.info.channels
            except:
                pass
            return info
        except:
            return {'length':0,'bitrate':0,'channels':0}

    def audio_mime_type(self, path):
        m = magic.open(magic.MAGIC_MIME)
        m.load()
        mime_info = m.file(path)
        try:
            category, info =  mime_info.split("/")
        except:
            return False
        if category != "audio":
            return False
        try:
            mimetype, info  =  info.split(";")
        except:
            return False

        return mimetype



