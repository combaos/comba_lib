# -*- coding: utf-8 -*-
import datetime
import time
import logging

from comba_lib.reporting.statestore import RedisStateStore
from comba_lib.reporting.mail import CombaMailer

"""
Meldungen an den StateStore schicken
"""
class CombaMessenger():
    def __init__(self):
     """
         Constructor
     """   
     self.channel = 'main'
     self.section = ''
     self.rstore = RedisStateStore()
     self.errnr = '00'
     self.components = {'controller':'01', 'scheduler':'02', 'playd':'03', 'recorder':'04', 'helpers':'09'}
     self.fromMail = ''
     self.adminMails = ''

    #------------------------------------------------------------------------------------------#
    def setChannel(self, channel):
        """
        Einen "Kanal" setzen - zb scheduler
        @type channel: string
        @param channel: Kanal/Name der Komponente  
        """
        self.channel = channel
        if self.components.has_key(channel):
            self.errnr = self.components[channel]
        self.rstore.setChannel(channel)

    #------------------------------------------------------------------------------------------#
    def setSection(self, section):
        """
        Einen Sektion / Gültigkeitsbereich der Meldung setzen - zb internal
        @type section: string
        @param section: Gültigkeitsbereich
        """
        self.section = section


#------------------------------------------------------------------------------------------#
    def setMailAddresses(self, fromMail, adminMails):
        """
        Einen Sektion / Gültigkeitsbereich der Meldung setzen - zb internal
        @type section: string
        @param section: Gültigkeitsbereich
        """
        self.fromMail = fromMail
        self.adminMails = adminMails

    #------------------------------------------------------------------------------------------#
    def send(self, message, code, level, job, value='', section=''):
        """
        Eine Message senden
        @type message:  string
        @param message: menschenverständliche Nachricht
        @type code:     string
        @param code:    Fehlercode - endet mit 00 bei Erfolg
        @type level:    string
        @param level:   Error-Level - info, warning, error, fatal
        @type job:      string
        @param job:     Name der ausgeführten Funktion
        @type value:    string
        @param value:   Ein Wert
        @type section:  string
        @param section: Globale Sektion überschreiben        
        """        
        section = self.section if section == '' else section 
        self.time = str(datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S:%f'))
        self.utime = time.time()
        state = {'message':message.strip().replace("'","\\'"), 'code':self.errnr + str(code),'job':job,'value':value}
        self.rstore.setSection(section)
        self.rstore.store(level, state)
        ###TODO: hier kann auch was zu redis gepostet werden
        if level == 'info' or level == 'success':
            logging.info(message)
        elif level == 'warning':
            logging.warning(message)
        elif level == 'error':
            logging.error(message)
            self.sendAdminmail(level, message, state)

        elif level == 'fatal':
            logging.critical(message)
            self.sendAdminmail(level, message, state)

    #------------------------------------------------------------------------------------------#
    def sayAlive(self):
        """
        Soll alle 20 Sekunden von den Komponenten ausgeführt werden, 
        um zu melden, dass sie am Leben sind
        """
        self.rstore.setAliveState()

    #------------------------------------------------------------------------------------------#
    def getAliveState(self, channel):
        """
        Live State abfragen 
        @type channel: string
        @param channel: Channel/Komponente    
        """
        return self.rstore.getAliveState(channel)

    #------------------------------------------------------------------------------------------#
    def setState(self, name, value, expires=None, channel=None):
        """
        Kündigt einen Event an 
        @type name: string
        @param name: Name des state
        @type value: string
        @param value: Wert
        @type channel: string
        @param channel: Kanal (optional)       
        """
        if not channel:
            channel = self.channel

        self.rstore.setState(name, value, expires, channel)        

    #------------------------------------------------------------------------------------------#
    def queueAddEvent(self, name, eventtime, value, channel=None):
        """
        Kündigt einen Event an 
        @type name: string
        @param name: der Name des Events        
        @type eventtime: string|datetime.datetime
        @param eventtime: Datum und Zeit des events
        @type value: dict
        @param value: Werte
        @type channel: string
        @param channel: Kanal (optional)       
        """
        if not channel:
            channel = self.channel

        if type(eventtime) == type(str()):            
            eventtime_str = datetime.datetime.strptime(eventtime[0:16].replace(' ','T'), "%Y-%m-%dT%H:%M").strftime("%Y-%m-%dT%H:%M")
        
        elif type(eventtime) is datetime.datetime:
            eventtime_str = eventtime.strftime("%Y-%m-%dT%H:%M")
            
        else: 
            raise TypeError('eventtime must be a datetime.date or a string, not a %s' % type(eventtime))                      
        
        self.rstore.queueAddEvent(eventtime_str, name, value, channel)        

    #------------------------------------------------------------------------------------------#
    def queueRemoveEvents(self, name, channel=None):
        """
        Löscht Events
        @type name: string
        @param name: der Name des Events        
        @type channel: string
        @param channel: Kanal (optional)       
        """
        if not channel:
            channel = self.channel
                        
        self.rstore.queueRemoveEvents(name, channel)        
    
    #------------------------------------------------------------------------------------------#
    def fireEvent(self, name, value, channel=None):
        """
        Feuert einen Event 
        @type name: string
        @param name: der Name des Events
        @type value: dict
        @param value: Werte
        @type channel: string
        @param channel: Kanal (optional)       
        """
        if not channel:
            channel = self.channel

        self.rstore.fireEvent(name, value, channel)        

    #------------------------------------------------------------------------------------------#
    def getEventQueue(self, name=None, channel=None):
        """
        Holt events eines Kanals
        @type channel: string
        @param channel: Kanal (optional)
        @rtype: list
        @return: Liste der Events       
        """
        queue = self.rstore.getEventQueue(name, channel)
        return queue

    #------------------------------------------------------------------------------------------#
    def getEvents(self, name=None, channel=None):
        """
        Holt events eines Kanals
        @type channel: string
        @param channel: Kanal (optional)
        @rtype: list
        @return: Liste der Events       
        """
        events = self.rstore.getEvents(name, channel)
        return events

    #------------------------------------------------------------------------------------------#
    def getEvent(self, name=None, channel=None):
        """
        Holt event eines Kanals
        @type channel: string
        @param channel: Kanal (optional)
        @rtype: dict
        @return: Event       
        """
        events = self.rstore.getEvents(name, channel)
        result = False
        if events:
            result = events.pop(0)
        return result

#------------------------------------------------------------------------------------------#
    def sendAdminmail(self, level, message, state):
        """
        Sendent mail an Admin(s),
        @type message: string
        @param message: Die Message
        @type state: dict
        @param state: Der State
        @return result
        """

        if self.fromMail and self.adminMails:
            subject = "Possible comba problem on job " + state['job'] + " - " + level
            mailmessage = "Hi Admin,\n comba reports a possible problem\n\n"
            mailmessage = mailmessage + level + "!\n"
            mailmessage = mailmessage + message + "\n\n"
            mailmessage = mailmessage + "Additional information:\n"
            mailmessage = mailmessage + "##################################################\n"
            mailmessage = mailmessage + "Job:\t" + state['job'] + "\n"
            mailmessage = mailmessage + "Code:\t" + state['code'] + "\n"
            mailmessage = mailmessage + "Value:\t" + str(state['value']) + "\n"
            mailer = CombaMailer(self.adminMails,self.fromMail)
            mailer.sendAdminMail(subject,mailmessage)

        else:
            return False





    #------------------------------------------------------------------------------------------#
    def receive(self):
        """
        Bisher wird nichts empfangen
        """
        return ""    
