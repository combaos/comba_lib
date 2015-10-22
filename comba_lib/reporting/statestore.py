# -*- coding: utf-8 -*-
import redis
import time
import datetime
import json
import re
import uuid

class RedisStateStore(object):
    
    """Store and get Reports from redis"""

    def __init__(self, **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.db= redis.Redis()
        self.channel = '*'
        self.section = '*' 
        self.separator = '_'
        self.daily = False

    #------------------------------------------------------------------------------------------#
    def setChannel(self, channel):
        """
        Kanal setzen
        @type channel: string
        @param channel: Kanal
        """
        self.channel = channel

    #------------------------------------------------------------------------------------------#
    def setSection(self, section):
        """
        Sektion setzen
        @type section: string
        @param section: Sektion
        """
        self.section = section

    #------------------------------------------------------------------------------------------#
    def setAliveState(self):
        """
        Alive Funktion - alle 20 Sekunden melden, dass man noch am Leben ist
        """        
        self.setState('alive', 'Hi', 21)

    #------------------------------------------------------------------------------------------#
    def getAliveState(self, channel):
        """
        Alive Status eines Channels ermitteln
        @type channel:  string
        @param channel: der Channel
        @rtype: string/None
        @return: Ein String, oder None, bei negativem Ergebnis
        """           
        return self.getState('alive', channel)            

    #------------------------------------------------------------------------------------------#
    def setState(self, name, value, expires=None, channel=None):
        """
        Setzt einen Status 
        @type name: string
        @param name: Name des state
        @type value: string
        @param value: Wert
        @type channel: string
        @param channel: Kanal (optional)       
        """
        if not channel:
            channel = self.channel
        
        key = self._createKey(channel + 'State', name)

        if value == "":
            self.db.delete(key)
        else:
            # publish on channel
            message = json.dumps({'eventname':name, 'value': value})
            self.db.publish(channel + 'Publish', message)
            # store in database
            self.db.set(key, value)
            if(expires):
                self.db.expire(key, 21)                                    

    #------------------------------------------------------------------------------------------#
    def getState(self, name, channel):
        """
        Holt einen Status
        @type name: string
        @param name: Name des state
        @type channel: string
        @param channel: Kanal (optional)       
        """
        key = self._createKey(channel + 'State', name)
        return self.db.get(key)
                                                
    #------------------------------------------------------------------------------------------#
    def queueAddEvent(self, eventtime, name, value, channel=None):
        """
        Kündigt einen Event an 
        @type eventtime: string
        @param eventtime: Datum und Zeit des events
        @type name: string
        @param name: Name des Events        
        @type value: dict
        @param value: Werte
        @type channel: string
        @param channel: Kanal (optional)       
        """
        timeevent = datetime.datetime.strptime(eventtime[0:16],"%Y-%m-%dT%H:%M")
        expire = int(time.mktime(timeevent.timetuple()) - time.time()) + 60        
        self._setEvent(name, eventtime, value, 'Evqueue', 'evqueue', expire, channel)
              
    #------------------------------------------------------------------------------------------#
    def queueRemoveEvents(self, name=None, channel=None):
        """
        Löscht Events
        @type name: string
        @param name: Name des Events
        @type channel: string
        @param channel: Kanal (optional)       
        """
        query = channel + 'Evqueue_' if channel else '*Evqueue_'
        query = query + '*_' + name  if name else query + '*_*'
        
        keys = self.db.keys(query)

        for delkey in keys:
            self.db.delete(delkey)        

    #------------------------------------------------------------------------------------------#
    def fireEvent(self, name, value, channel=None):
        """
        Feuert einen Event 
        @type name: string
        @param name: Name des Events
        @type value: dict
        @param value: Werte
        @type channel: string
        @param channel: Kanal (optional)       
        """
        eventtime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M")
        self._setEvent(name, eventtime, value, 'Event', 'events', 60, channel)

    #------------------------------------------------------------------------------------------#
    def _setEvent(self, name, eventtime, value, type, namespace, expire, channel=None):
        """
        Feuert einen Event 
        @type eventtime: string
        @param eventtime: Datum und Zeit des events
        @type value: dict
        @param value: Werte
        @type channel: string
        @param channel: Kanal (optional)       
        """
        if not channel:
            channel = self.channel

        timeevent = datetime.datetime.strptime(eventtime[0:16],"%Y-%m-%dT%H:%M")                
        key = self._createKey(channel + type, eventtime, name)
        
        value['starts'] = eventtime[0:16]
        value['eventchannel'] = channel
        value['eventname'] = name
        self.db.hset(key, namespace, value)
        self.db.expire(key, expire)                    

    #------------------------------------------------------------------------------------------#
    def getEventQueue(self, name=None, channel=None):
        """
        Holt events eines Kanals
        @type channel: string
        @param channel: Kanal (optional)
        @rtype: list
        @return: Liste der Events       
        """
        query = channel + 'Evqueue_' if channel else '*Evqueue_' 
        query = query + '*_' + name  if name else query + '*_*'
        keys = self.db.keys(query)        
        keys.sort()
        entries = self._getEntries(keys, 'evqueue')
        return entries

    #------------------------------------------------------------------------------------------#
    def getEvents(self, name=None, channel=None):
        """
        Holt events eines Kanals
        @type channel: string
        @param channel: Kanal (optional)
        @rtype: list
        @return: Liste der Events       
        """
        query = channel + 'Event_' if channel else '*Event_' 
        query = query + '*_' + name  if name else query + '*_*'
        keys = self.db.keys(query)        
        keys.sort()
        entries = self._getEntries(keys, 'events')
        return entries

    #------------------------------------------------------------------------------------------#
    def getNextEvent(self, name=None, channel=None):
        """
        Holt den aktuellsten Event
        @type channel: string
        @param channel: Kanal (optional)
        @rtype: dict/boolean
        @return: ein Event oder False       
        """
        events = self.getEventQueue(name, channel)
        if len(events) > 0:            
            result = events.pop(0)
        else:
            result = False
        
        return result

    #------------------------------------------------------------------------------------------#
    def store(self, level, value):
        """
        Hash speichern
        @type level: string
        @param level: der errorlevel
        @type value: dict
        @param value: Werte als dict
        """ 
        microtime = str(time.time())
        value['microtime'] = microtime
        value['level'] = level        
        key = self._createKey(self.channel, self.section, level, microtime, str(uuid.uuid1()))
        self.db.hset(key, self.channel, value)
        self.db.expire(key, 864000)

    #------------------------------------------------------------------------------------------#
    def _getKeys(self, level = '*'):        
        """
        Redis-Keys nach Suchkriterium ermitteln
        @type level: string
        @param level: einen Errorlevel filtern  
        @rtype: list
        @return: Die Keys auf die das Suchkriterium zutrifft         
        """
        key = self._createKey(self.channel, self.section, level)
        microtime = str(time.time())
        search = microtime[0:4] + '*' if self.daily else '*'
        return self.db.keys(key + self.separator + '*')

    #------------------------------------------------------------------------------------------#
    def _createKey(self, *args):
        """
        Key erschaffen - beliebig viele Argumente
        @rtype: string
        @return: Der key
        """
        return self.separator.join(args)
         
    def getEntries(self, level = '*'):
        """
        Liste von Hashs nach Suchkriterium erhalten
        @type level: string
        @param level: einen Errorlevel filtern
        @rtype: list
        @return: Redis Hashs  
        """
        def tsort(x,y):
        
            if float(x.split('_',4)[3]) > float(y.split('_',4)[3]):
                return 1
            elif float(x.split('_',4)[3]) < float(y.split('_',4)[3]):
                return -1
            else:
                return 0
         
        keys = self._getKeys(level)        
        
        keys.sort(tsort)
        entries = self._getEntries(keys, self.channel)
        entries = sorted(entries, key=lambda k: k['microtime'], reverse=True)
        return entries

    #------------------------------------------------------------------------------------------#
    def _getEntries(self, keys, channel):        
        entries = []      
        for key in keys:
            entry = self.db.hget(key,channel)
            entry = json.dumps(entry)

            if not (entry is None):
                try:
                    entry = entry.decode('utf-8').replace('None','"None"')
                    entry =  re.sub("########[^]]*########", lambda x:x.group(0).replace('\"','').replace('\'',''),entry.replace("\\\"","########").replace("\\'","++++++++").replace("'",'"').replace('u"','"').replace('"{','{').replace('}"','}')).replace("########","\"")
                    entry = json.loads(entry)
                    entry['key'] = key
                    entries.append(entry)
                except:
                    pass
        
        return entries
    