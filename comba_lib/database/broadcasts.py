__author__ = 'michel'
# -*- coding: utf-8 -*-
from mongoengine import *
import datetime, os, urllib2
from datetime import timedelta

connect('broadcasts')

#------------------------------------------------------------------------------------------#

class BroadcastPeriod(Document):
    """
    Daten werden noch in der scheduler.xml gehalten
    """
    identifier = StringField(required=True)
    start = DateTimeField(required=True)
    end = DateTimeField(required=True)
    meta = {
        'ordering': ['+start']
    }

#------------------------------------------------------------------------------------------#

class BroadcastEvent(Document):
    """
    Definiert eine Sendung mit Start- und End-Datum
    """
    identifier = StringField(required=True) # Unique (o)id
    location = StringField(required=False) # archived audio file, will be available when the broadcast event is over
    reccurrence_id = StringField(required=False) # Unique id of event to be repeated
    duration = StringField(required=False) # duration in seconds
    start = DateTimeField(required=True)  # start date
    end = DateTimeField(required=True)  # end date
    rerun = BooleanField(required=True)  # true, if the event is a rerun
    replay_of_datetime = DateTimeField(required=False)
    replay_of = StringField(required=False)
    programme_id = StringField(required=False)
    station_name = StringField(required=False)
    station_id = StringField(required=False)
    title = StringField(required=True)
    subject = StringField(required=False)
    description = StringField(required=False)
    overwrite_event = ReferenceField('BroadcastEvent')
    state = StringField(required=False, default="created")
    created = DateTimeField(default=datetime.datetime.now)
    modified = DateTimeField(default=datetime.datetime.now)
    modified_by = StringField(required=False)
    text = StringField(required=False)
    data = DictField(required=False)
    meta = {
        'ordering': ['+start'],
        'indexes': [
            {'fields': ['title', "subject"],
             'default_language': 'german',
             'weight': {'title': 10, 'subject': 2}
             }
        ]
    }

    def fileExists(self):
        return os.path.exists(str(self.location).replace('file://', ''))

#------------------------------------------------------------------------------------------#
class BroadcastEventTrack(Document):
    """
    Track, der einem BroadcastEvent zugeordnet ist
    """
    identifier = StringField(required=True) # Unique id
    broadcast_event = ReferenceField(BroadcastEvent) # the BroadcastEvent the track refers to
    location = StringField(required=True)  # audio location (url or file)
    length = FloatField() # duration in seconds
    start = DateTimeField(required=False) # start date
    end = DateTimeField(required=False) # end date
    record_at = DateTimeField(required=False) # The date on which the recording has to start.
    meta = {
        'ordering': ['+start']
    }

    def isLast(self):
        return self == BroadcastEventTrack.objects(broadcast_event=self.broadcast_event).order_by('-start').first()

    def fileExists(self):
        return os.path.exists(str(self.location).replace('file://', ''))

    def totalLength(self):
        tracks = BroadcastEventTrack.objects(broadcast_event=self.broadcast_event)
        length = 0
        for track in tracks:
            length = length + track.length if track.length else length
        return length

#------------------------------------------------------------------------------------------#
class BroadcastEventOverride(Document):
    """
    Ein Track, der in die Sendeautomatisierung eingeblendet wird
    Muss manuell erstellt werden
    """
    identifier = StringField(required=True) # Unique id
    broadcast_event = ReferenceField(BroadcastEvent) # the BroadcastEvent the track refers to
    location = StringField(required=True) # audio location (url or file)
    mimetype = StringField() # audio mime
    bitrate = IntField() # bitrate
    channels = IntField() # number of channels
    length = FloatField() # duration in seconds
    start = DateTimeField() # start date
    end = DateTimeField() # end date
    seek = IntField() # TODO: seconds to seek into the audio
    ordering = IntField(default=0)  # track sorting
    data = DictField(required=False) # additional data
    meta = {
        'ordering': ['+ordering']
    }

    def nextOrdering(self):
        """
        Return number of next track in tracklist
        @return:  int ordering
        """
        lastOverride = BroadcastEventOverride.objects(broadcast_event=self.broadcast_event)\
            .order_by('-ordering')\
            .first()

        if lastOverride:
            return lastOverride.ordering + 1
        else:
            return 1

    def filled(self):
        """
        what percent of the broadcast event is allready filled with audio
        @return:  percent filled with audio
        """
        object = self.broadcast_event
        parent_total = (object.end - object.start).total_seconds()
        proc = 0
        try:
            proc = (self.totalLength() / parent_total) * 100
        except:
            proc = 0
        return int(proc)


    def totalLength(self):
        """
        Get the total length of audio in the track list
        @return:  total length of audio
        """
        tracks = BroadcastEventOverride.objects(broadcast_event=self.broadcast_event)
        length = 0
        for track in tracks:
            length = length + track.length if track.length else length
        return length

    def fileExists(self):
        request = urllib2.Request(self.location)
        request.get_method = lambda: 'HEAD'
        try:
            response = urllib2.urlopen(request)
            return True
        except:
            return False
