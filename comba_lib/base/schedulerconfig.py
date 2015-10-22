from xml.dom.minidom import parse
import datetime
from datetime import timedelta
import simplejson
from xml.etree import ElementTree

class NotTextNodeError:
    pass


class CombaSchedulerConfig():
    def __init__(self, xmlpath):
        self.jobs = {}
        self.filename = xmlpath
        self.playperiods = []
        self.recordperiods = []
        self.hasinstance = False
        self.until = None

    # -----------------------------------------------------------------------#
    def getPlayPeriods(self):
        if not self.hasinstance:
            self.getJobs()
        return self.playperiods

    # -----------------------------------------------------------------------#
    def getRecordPeriods(self):
        if not self.hasinstance:
            self.getJobs()
        return self.recordperiods

    # -----------------------------------------------------------------------#
    def getJobs(self):
        self.hasinstance = True
        self.loadXml()

        for job in self.jobs:
            if not job.has_key('job'):
                continue;
            if not job.has_key('until'):
                job['until'] = ''
            if not job.has_key('day'):
                job['day'] = 'all'
        self.jobs.sort(cmp=lambda x,y: cmp(x['time'], y['time']))
        self.jobs.sort(cmp=lambda x,y: cmp(x['day'], y['day']))
        for index, job in enumerate(self.jobs):
            if job['job'] == 'play_playlist':                
                job['duration'] = self._calcDuration(job['time'], job['until'])
                self.playperiods.append({'from': job['time'],'until': job['until'], 'duration': job['duration']})
                day = None
                if job.has_key('day'):
                    day = job['day'] 
                     
                self.addPlaylistLoadJob(job['time'], job['until'], day)

            if job['job'] == 'start_recording':                
                job['duration'] = self._calcDuration(job['time'], job['until'])
                self.recordperiods.append({'from': job['time'],'until': job['until'], 'duration': job['duration']})

        return self.jobs

    # -----------------------------------------------------------------------#
    def addPlaylistLoadJob(self, playTime, untilTime, day=None):
         job = {}
         playStart = datetime.datetime.strptime('1901-01-01T' + playTime,'%Y-%m-%dT%H:%M');
         loadTime =  playStart - timedelta(minutes=3)
         loadTime = loadTime.strftime('%H:%M')
         job['time'] = loadTime
         job['from'] = playTime
         job['until'] = untilTime
         job['job'] = 'load_playlist'
         
         if day and  not day == 'all' and loadTime > playTime:
             day = int(day)
             day = 6 if day == 0 else day - 1
         job['day'] = str(day) 
         self.jobs.append(job)
    
    # -----------------------------------------------------------------------#         
    def storeJsonToXml(self, json):
        try:
            jobs = simplejson.loads(json)
        except:
            return False
        xml =           '<?xml version="1.0" encoding="UTF-8"?>'+"\n"
        xml +=          '<Config>'+"\n";
        xml +=          '    <Jobs multiple="true">'+"\n";
        xmlend =        '    </Jobs>'+"\n";
        xmlend +=       '</Config>';

        for job in jobs:
            xml+=       '        <job>'+"\n"; 
            for key in job.keys():
                xml+=   '            <'+key+'>'+str(job[key])+'</'+key+'>'+"\n"
            if not job.has_key('params'):
                xml+=   '            <params></params>'+"\n"
            if not job.has_key('day'):
                xml+=   '            <day>all</day>'+"\n"
            xml+=       '        </job>'+"\n"
        # validate xml    
        try:    
            x = ElementTree.fromstring(xml+xmlend)
        except:
            return False
        else:            
            try:
                file = open(self.filename, "w")
                file.write(xml+xmlend)
                file.close()
            except:
                return False
            else:
                return True
            
                 
    # -----------------------------------------------------------------------#
    def loadXml(self):
        dom = parse(self.filename)
        config = self.nodeToDic(dom)

        self.jobs = config['Config']['Jobs']

    # -----------------------------------------------------------------------#
    def getTextFromNode(self, node):

        t = ""
        for n in node.childNodes:
            if n.nodeType == n.TEXT_NODE:
                t += n.nodeValue
            else:
                raise NotTextNodeError
        return t

    # -----------------------------------------------------------------------#
    def nodeToDic(self, node):

        dic = {}
        for n in node.childNodes:
            if n.nodeType != n.ELEMENT_NODE:
                continue
            if n.getAttribute("multiple") == "true":
                # node with multiple children:
                # put them in a list
                l = []
                for c in n.childNodes:
                    if c.nodeType != n.ELEMENT_NODE:
                        continue
                    l.append(self.nodeToDic(c))
                    dic.update({n.nodeName: l})
                continue

            try:
                text = self.getTextFromNode(n)
            except NotTextNodeError:
                # 'normal' node
                dic.update({str(n.nodeName): self.nodeToDic(n)})
                continue
            # text node
            dic.update({str(n.nodeName): str(text)})
            continue
        return dic

    # -----------------------------------------------------------------------#
    def in_timeperiod(self, now, job):
        if not job.has_key('until') or not job['until']:
            return False
        (hour1, minute1) = job['time'].split(':')
        (hour2, minute2) = job['until'].split(':')
        if job['time'] > job['until']:
            return datetime.time(hour=int(hour1), minute=int(minute1)) \
                   <= now.time()
        else:
            return datetime.time(hour=int(hour1), minute=int(minute1)) \
                   <= now.time() \
                   <= datetime.time(hour=int(hour2), minute=int(minute2))

    # -----------------------------------------------------------------------#
    def _calcDuration(self, timestring1, timestring2):
        """Berechnet Zeit in Sekunden aus zwei Time-Strings
        """
        ftr = [3600, 60, 1]
        sec1 = sum([a * b for a, b in zip(ftr, map(int, timestring1.split(':')))])
        sec2 = sum([a * b for a, b in zip(ftr, map(int, timestring2.split(':')))])
        offset = 0 if sec2 > sec1 else  86400
        return  (sec2 + offset) - sec1

    # -----------------------------------------------------------------------#

    def find_next(self, items, index, key, value):

        for idx, item in enumerate(items):
            if idx <= index:
                continue
            if item[key] == value:
                    return idx
        return self.find_next(items,0,key,value)
