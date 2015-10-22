#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       combac.py
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
import simplejson
import urllib2
import datetime
import sys
import threading
import codecs
import os
import os.path

from comba_lib.reporting.messenger import CombaMessenger
from comba_lib.base.combabase import CombaBase
from comba_lib.database.broadcasts import *

class CombaCalendarService(threading.Thread, CombaBase):
    """
    Holt Playlist-Daten und schreibt sie in die database
    """
    def __init__(self, datefrom="", dateto=""):
        threading.Thread.__init__ (self)
        self.messenger = CombaMessenger()
        self.messenger.setChannel('helpers')
        self.messenger.setSection('getcalendar')
        self.xmlplaylist = range(0)
        self.loadConfig()
        self.messenger.setMailAddresses(self.get('frommail'), self.get('adminmail'))
        self.dateto = dateto
        self.datefrom = str(datefrom)
        self.until = ''

    #------------------------------------------------------------------------------------------#
    def setDateFrom(self, date):
        self.datefrom = str(date).replace(" ", "T")

    #------------------------------------------------------------------------------------------#
    def setDateTo(self, date):
        self.dateto = str(date).replace(" ", "T")

    #------------------------------------------------------------------------------------------#
    def setUntilTime(self, timestring):
        self.until = timestring

    #------------------------------------------------------------------------------------------#
    def setSecondsPerTrack(self, seconds):
        self.secondspertrack = int(seconds)

    #------------------------------------------------------------------------------------------#
    def setCalendarUrl(self, url):
        self.calendarurl = url

    #------------------------------------------------------------------------------------------#
    def setAudioPath(self, path):
        self.audiobase = path

    #------------------------------------------------------------------------------------------#
    def setAudioPath(self, path):
        self.audiobase = path

    #------------------------------------------------------------------------------------------#
    def setPlaylistStore(self, path):
        self.playlistdir = path

    #------------------------------------------------------------------------------------------#
    def getUri(self):
        if not self.playlistdir:
            return False
        if not self.datefrom:
            return False
        if not self._calcDateTo():
            return
        hostname = self.get('servername');
        port = self.get('serviceport');
        date_from = self.datefrom[0:16] + ':00';
        date_to = self.dateto[0:16] + ':00';
        uri = 'http://' + hostname  + ':' + port + '/playlist/' + date_from + '/' + date_to

        return uri

    #------------------------------------------------------------------------------------------#
    def run(self):
        """
        Kalender-Daten abholen und in Playlist schreiben
        """
        filestotal = 0
        if not self._calcDateTo():
            return

        self._setUrl()
        self._fetchData()

        # secondspertrack  may be a string from config
        self.secondspertrack = int(self.secondspertrack)
        for show in self.data['shows']:
            #fix nonexisting origdatetime
            if not show.has_key('rerun'):
                continue
            if not show.has_key('end'):
                continue
            if not show.has_key('start'):
                continue

            if str(show['rerun']).lower() == 'true':
                try:
                    show['origdate'] = show['replay_of_datetime']
                except KeyError:
                    continue
            else:
                show['origdate'] = show['start']
                #TODO: message
                #mailnotice("Am " + datefrom[0:10] +" wurde eine Luecke im Kalender festgestellt")


            event = BroadcastEvent.objects(identifier=show['identifier']).first()

            if not event:
                event = BroadcastEvent()

            # calc duration
            duration = self._calcDuration(show['start'], show['end'])
            show['duration'] = datetime.timedelta(seconds=duration).__str__()
            for k in event:
                if show.has_key(k):
                    event[k] = show[k]

            event.modified = datetime.datetime.now()
            event.modified_by = 'calendarservice'

            event.save()
            broadcast_event = event.to_dbref()

            trackstart = datetime.datetime.strptime(show['start'].replace(' ', 'T'), "%Y-%m-%dT%H:%M:%S")
            trackrecorded = datetime.datetime.strptime(show['origdate'].replace(' ', 'T'), "%Y-%m-%dT%H:%M:%S")
            # split in parts
            parts = duration / self.secondspertrack

            for i in range(0, parts):
                filestotal += 1

                # Zu dieser Zeit muss die Aufnahme beendet werden
                trackDumpend = trackrecorded + datetime.timedelta(seconds=self.secondspertrack)
                trackPlayend = trackstart + datetime.timedelta(seconds=self.secondspertrack)

                identifier = show['identifier'] + ':' + str(i)
                track = BroadcastEventTrack.objects(identifier=identifier).first()
                if not track:
                    track = BroadcastEventTrack()

                File = str(self.audiobase + '/').replace('//','/') + trackrecorded.strftime('%Y-%m-%d') + '/' + trackrecorded.strftime('%Y-%m-%d-%H-%M') + '.wav'
                track.identifier = identifier
                track.title = show['title']
                track.ordering = i
                track.broadcast_event = broadcast_event
                track.location = 'file://' + File
                track.length = self.secondspertrack
                track.start = trackstart.strftime('%Y-%m-%d %H:%M:%S')
                track.end = trackPlayend.strftime('%Y-%m-%d %H:%M:%S')
                track.record_at = trackrecorded.strftime('%Y-%m-%d %H:%M:%S')

                track.save()

                # Events festhalten
                event = {'job': 'dump', 'location': File, 'length': track.length}
                self.messenger.queueAddEvent('dumpstart', track.record_at, event, 'recorder')
                event = {'job': 'dump', 'location': File, 'length': track.length}
                self.messenger.queueAddEvent('dumpend', trackDumpend, event, 'recorder')

                trackstart = trackstart + datetime.timedelta(seconds=self.secondspertrack)
                trackrecorded = trackrecorded + datetime.timedelta(seconds=self.secondspertrack)

    #------------------------------------------------------------------------------------------#
    def _calcDateTo(self):
        if self.dateto:
            return True
        if not self.until:
            return False
        if not self.datefrom:
            return False
        date_start = datetime.datetime.strptime(self.datefrom.replace('T',' '), "%Y-%m-%d %H:%M")
        time_start = date_start.strftime('%H:%M')
        day_offset = 1 if (time_start > self.until) else 0
        end_date = date_start + datetime.timedelta(day_offset)
        self.dateto = end_date.strftime('%F') + 'T' + self.until
        return True

    #------------------------------------------------------------------------------------------#
    def _calcDuration(self, start, end):
        """
        Berechnet Zeit in Sekunden aus Differenz zwischen Start und Enddatum
        @type start: datetime
        @param start: Startzeit
        @type end: datetime
        @param end: Endzeit
        @rtype:       int
        @return:      Zeit in Sekunden
        """
        sec1 = int(datetime.datetime.strptime(start[0:16].replace(" ","T"),"%Y-%m-%dT%H:%M").strftime("%s"));
        sec2 = int(datetime.datetime.strptime(end[0:16].replace(" ","T"),"%Y-%m-%dT%H:%M").strftime("%s"));
        return (sec2 - sec1);


    #------------------------------------------------------------------------------------------#
    def _fetchData(self):

        # Now open Calendar Url
        try:
            response = urllib2.urlopen(self.dataURL)

        except IOError, e:
            self.messenger.send("Could not connect to service " + self.dataURL, '1101', 'error', 'fetchCalenderData',
                                self._getErrorData(), 'getcalendar')
            #mailnotice("Verbindung zu Zappa konnte nicht hergestellt werden")
            #TODO: so gehts nicht
            sys.exit()
        else:
            # Read in data
            jsondata = response.read()
            try:
                self.data = simplejson.loads(jsondata)

            except:
                self.messenger.send("Could not decode calender data from service " + self.dataURL, '1102', 'error',
                                    'fetchCalenderData', self._getErrorData(), 'getcalendar')
                sys.exit()
            else:
                # check data
                try:
                    self.data['shows']
                except KeyError:
                    self.messenger.send("Could not decode calender data from service " + self.dataURL, '1102', 'error',
                                        'fetchCalenderData', self._getErrorData(), 'getcalendar')
                    sys.exit()
                else:
                    return self.data

    #------------------------------------------------------------------------------------------#
    def _dumpPlaylist(self, xml):
        """
        Dump the playlist
        @type xml: string
        @param xml: XML-String
        """
        # dump file
        try:
            f = codecs.open(self.playlistpath + '.xspf', 'w', encoding='utf-8')

            f.write(xml)
            f.close()
        except:
            self.messenger.send("Couldn't dump playlist " + self.playlistpath + '.xspf', '1201', 'error',
                                'get_playlist', self._getErrorData(), 'getcalendar')
        else:
            self.messenger.send("Dumped playlist" + self.playlistpath + ".xspf", '1200', 'success', 'get_playlist',
                                self._getErrorData(), 'getcalendar')

    #------------------------------------------------------------------------------------------#
    def _getErrorData(self):
        """
        Basisdaten als dict liefern
        """
        return (
        {'from': str(self.datefrom), 'dateto': str(self.dateto), 'path': self.playlistpath, 'url': self.calendarurl})

    #------------------------------------------------------------------------------------------#
    def _setUrl(self):
        """
        Die URL auf den Zappa-Kalender ermitteln
        """

        self.dataURL = self.calendarurl.replace('#datefrom#', self.datefrom.replace(' ', 'T')).replace('#dateto#', self.dateto.replace(' ', 'T'))
        print self.dataURL

