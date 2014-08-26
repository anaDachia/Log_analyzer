__author__ = 'chiliadmin'

import sys
import re
from datetime import datetime, date


start_actions = re.compile('201\d-\d\d-\d\d (?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d),(?P<milisec>\d\d\d).*(?P<command>Starting) action <(?P<action>.*)> now.')
#2014-08-05 17:04:23,122 robots.actions: DEBUG - Starting action <background_blink()[a13cf98a-475c-4282-a7d1-7154efdcb7ac]> now.

complete_actions = re.compile('201\d-\d\d-\d\d (?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d),(?P<milisec>\d\d\d).*Action <(?P<action>.*)>: (?P<command>completed.)')
#2014-08-05 17:04:24,600 robots.actions: DEBUG - Action <wakeup()[bb100d53-11ea-468e-a83f-39b1a21f300c]>: completed.

waitsOn_rsrc_start = re.compile('201\d-\d\d-\d\d (?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d),(?P<milisec>\d\d\d).*Robot action <(?P<action>.*)> is (?P<command>waiting) on resource(?P<rsrc>.*) \(.*\)')
#2014-08-05 17:12:52,211 robots.actions: INFO - Robot action <lightpattern(2)[40306ef8-db30-406a-a3d8-16f232a39fd1]> is waiting on resource LEDs (currently owned by <lightbar>)

acquire_rsrc_wait = re.compile('201\d-\d\d-\d\d (?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d),(?P<milisec>\d\d\d).*Robot action <(?P<action>.*)> has (?P<command>acquired) resource(?P<rsrc>.*) \(.*\)')
#2014-08-05 17:12:56,117 robots.actions: INFO - Robot action lightpattern(2)[40306ef8-db30-406a-a3d8-16f232a39fd1] has acquired resource LEDs (currently owned by <lightpattern>)

wait_rsrc_free = re.compile('201\d-\d\d-\d\d (?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d),(?P<milisec>\d\d\d).*Robot action <(?P<action>.*)> (?P<command>acquired free) resource (?P<rsrc>.*) \(.*\)')

cancel_action_onWait = re.compile('201\d-\d\d-\d\d (?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d),(?P<milisec>\d\d\d).*Action <(?P<action>.*)> (?P<command>cancelled) while it was waiting for a lock on a resource.')

add_sub = re.compile('201\d-\d\d-\d\d (?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d),(?P<milisec>\d\d\d).*Added (?P<command>sub-action) (?P<action>.*) to action (?P<action2>.*)')

error = re.compile('201\d-\d\d-\d\d (?P<hour>\d\d):(?P<min>\d\d):(?P<sec>\d\d),(?P<milisec>\d\d\d).*(?P<command>more) than.*')

search_regexes= [start_actions, complete_actions, waitsOn_rsrc_start, acquire_rsrc_wait, wait_rsrc_free, cancel_action_onWait, add_sub,error]



class DataObj:

    """
    class containing each line of parser
    """
    def __init__(self):
        self.time= (0,0,0,0)
        self.action1 = {}
        self.action2 = {}
        self.command = ""
        self.rsrc = ""


    def get_timeInstance(self):
        """
        @:return an object of type datatime
        """
        t= datetime.time(datetime.now())
        t = t.replace(hour = self.time[0],minute = self.time[1], second= self.time[2], microsecond= self.time[3])
        return t

    def setAction1(self, actionstr):
        self.action1 = self._get_action_name_Id(actionstr)

    def setAction2(self, actionstr):
        self.action2 = self._get_action_name_Id(actionstr)



    def _get_action_name_Id(self, action):
        """
        @:return a dictionary containing name and id of a given action
        """

        regex = re.compile('(?P<name>[_A-Za-z][_a-zA-Z0-9]*)\(.*\)\[(?P<id>.*)\]')
        match = regex.search(action)
        return  {"name" : match.group(1), "id" : match.group(2)} #(match.group(1), match.group(2))

    def __str__(self):
        return "{0}, {1}, {2}, {3}".format(self.time, self.command, self.action1, self.action2)




class Reader:
    def __init__(self, filename):
        self.data_objs = []
        self.filename = filename

    def parse(self):
        with open(self.filename) as log:
            for line in log.readlines():
                for regex in search_regexes:
                    found = regex.search(line)
                    if found:

                        self._make_data_obj(found)


    def _make_data_obj(self,match):
        data = DataObj()
        hour = int(match.group(1))
        min = int(match.group(2))
        sec = int(match.group(3))
        milisec = int(match.group(4))
        data.command = match.group('command')
        try:
            data.setAction1(match.group('action'))
            data.setAction2(match.group('action2'))

        except:
            pass
        try:
            data.rsrc = match.group('rsrc')
        except:
            pass
        data.time = (hour,min,sec,milisec * 1000)
        self.data_objs.append(data)

    def get_parsed_log(self):
        return self.data_objs


import wx
from diagram import GraphMaker
from analyzer import ActionAnalyzer
r = Reader('/home/chiliadmin/Documents/src/pyranger/bin/myToto')
r.parse()
a = ActionAnalyzer(r.get_parsed_log())
root = a._make_tree(True)  #get root node from analyzer

start_time= a.start_time    #get start_time from analyzer
action_ids = a.get_action_ids()
rsrcStack = a.get_rsrcStack()

app = wx.PySimpleApp()
frame = GraphMaker([root], start_time,action_ids,rsrcStack)
app.MainLoop()

