
__author__ = 'anahita'

from collections import deque
from datetime import datetime, date
from copy import  deepcopy

"""
for each action we have a header node and a set of ActionNodes as children. Each child shows an interval when the action was active
and also has a number of instances of ActionNodes as sub-actions
"""
class ActionNode:
    def __init__(self,parent, id, action):
        self.action = action     #dictionary containing action name and id.
        self.id = id
        self.activeTime = (-1,-1)
        self.children = []   #new instances of ActionNode
        self.Parent = parent

    def setActiveTime(self, start, end):
        self.activeTime = (start,end)

    def add_child(self,child):
        self.children.append(child)
        return child


    def rmv_last_child(self):
        if len(self.children ) == 0:
            print "there is no child and you're removing one! my id is : {0}".format(self.id)
            return None
        return self.children.pop()


    def set_start_time(self, time_obj):
        self.activeTime  = (time_obj, self.activeTime[1])

    def set_end_time(self, time_obj):
        self.activeTime  = ( self.activeTime[0], time_obj)

    def __str__(self):
        return "{0} : {1}".format(self.id, self.action)





#TODO make an all nodes list
action_ids = {} #dict: action_name -> unique id to be used in action graph creation
curr_acction_id = 0
rsrc_ids = {} #dict : action_name -> unique id to be used in resource graph creation
curr_rsrc_id = 0

class ActionAnalyzer:
    def __init__(self, command_list):
        self.id = 0
        self.command_list = command_list
        ##################################setting start time#################################
        tmp = command_list[0]
        self.start_time = datetime.time(datetime.now())
        self.start_time = self.start_time.replace(hour=tmp.time[0],minute=tmp.time[1],second=tmp.time[2],microsecond=tmp.time[3])
        #####################################################################################
        self.action_root = ActionNode(parent=None, id = self.id, action= {"name" : "root", "id" : "_"}) #the root node

        self.actionStacks = {} # key = action name, value : working stack of that action : containing incomplete actions
        self.wait_start = {} #key = action name, value: stack corresponding to that action: containing actions added as subactions but not started yet
        self.rsrcStacks={} #key = resource name, value : stack of tuples of (actionNode, wait) in which wait is a boolean showing if the action is waiting for rsrc or has acquired

        ###################bfs#################
        self.bfs_queue = deque()
        self.nodes = []
        self.colors = ['W' for i in range(0, len(self.nodes))]
        self.parents = [-1 for i in range (0, len(self.nodes))]



    def bfs_tree(self, root):
        self.queue.append(root)
        self.action_root.color = 'B' # B for Black

        while len(self.queue):
            u =  self.queue.popleft()
            for v in root.children:
                if self.colors[v.id] == 'W':
                    self.colors[v.id] ='B'
                    self.queue.append(v)
                    self.parents[v.id] = u



    """
    this function analyzes formerly parsed logs and builds a tree of action and subactions
    @:param hierarchical is a boolean if not set, all nodes will be added to the root and the final tree will be in 2 level
    @:return root of the action tree
    """
    def _make_tree(self, hierarchical = True):
        global action_ids
        global  curr_acction_id
        global rsrc_ids
        global curr_rsrc_id

        i = 0
        for cm in self.command_list:
            if cm.command == "more":
                continue
            print cm
            func = cm.action1['name']
            print func

            if cm.command == "Starting":
                print "in start---------------------------------------"
                found = False
                if func in self.wait_start and len(self.wait_start[func]) > 0: #if there is an sub-action that was added before starting:
                    #print "there is an added subaction in stack, checking if its me : new_command {0}".format(cm.action1['name'])

                    for f in self.wait_start[func]:
                        if cm.action1['id'] == f.action['id']:
                            #print "the corresponding node is found fortunately."
                            self.wait_start[func].remove(f)
                            found = True
                            break
                if found:
                    continue

                self.id +=1
                newNode = ActionNode(id = self.id, parent = self.action_root, action=cm.action1)
                self.action_root.add_child(newNode)
                self.nodes.append(newNode)
                #print "a new node with name {0} and id {1} is created".format(cm.action1, self.id)
                newNode.set_start_time(cm.get_timeInstance())

                if func in self.actionStacks:
                    self.actionStacks[func].append(newNode)
                else:
                    action_ids[func] = curr_acction_id
                    curr_acction_id += 1
                    self.actionStacks[func] = [newNode]

            elif cm.command == "completed.":

                if (not func in self.actionStacks) or len(self.actionStacks[func]) == 0:
                    print "there is an action that is ending but has not started. func_name {0}".format(cm.action1)
                    continue
                else:
                    for node in self.actionStacks[func]:
                        if node.action['id'] == cm.action1['id']:
                            node.set_end_time(cm.get_timeInstance())
                            tmp = self.actionStacks[func].remove(node)



            elif cm.command == "sub-action" :
                if(not hierarchical):
                    continue

                parent_action = cm.action2

                #####################
                child_exists = False
                parent_exists = False
                child = None
                parent = None
                if parent_action['name'] in self.actionStacks and len(self.actionStacks[parent_action['name']]) > 0:
                    for j in self.actionStacks[parent_action['name']] :

                        if j.action['id'] == parent_action['id']:
                            parent_exists = True
                            parent = j

                if (func in self.actionStacks) and len(self.actionStacks[func]) > 0  :
                    for j in self.actionStacks[func]:
                        if j.action['id'] == cm.action1['id']:
                            child_exists = True
                            child = j

                #############################################################################
                if not parent_exists:
                    print "ERROR : there is no such parent to add this action to it{0}".format(parent)

                elif not child_exists :
                    self.id +=1
                    newNode = ActionNode(id = self.id, parent = parent, action= cm.action1)
                    parent.add_child(newNode)
                    self.nodes.append(newNode)
                    newNode.set_start_time(cm.get_timeInstance())

                    if func in self.wait_start:
                        self.wait_start[func].append(newNode)
                    else:
                        self.wait_start[func] = [newNode]
                    ###########################################
                    if func in self.actionStacks:
                        self.actionStacks[func].append(newNode)
                    else:
                        action_ids[func] = curr_acction_id
                        curr_acction_id += 1
                        self.actionStacks[func] = [newNode]

                else:
                    child.Parent.rmv_last_child()
                    child.Parent = parent
                    parent.add_child(child)

            elif cm.command == "cancelled":

                if func in self.wait_start and len(self.wait_start[func]) > 0: #if there is an sub-action that was added before starting:
                    for f in self.wait_start[func]:
                        if cm.action1['id'] == f.action['id']:
                            print "the requesting node for cancellation is found."
                            self.wait_start[func].remove(f)
                            break
                else:
                    print "ERROR: an action is requesting for cancellation that has not been started"
                ###############################################################################
                if cm.rsrc in self.rsrcStacks and len(self.rsrcStacks[cm.rsrc]) > 0:
                    acquiering_node = None
                    for j in self.rsrcStacks[cm.rsrc]:
                        if j[0].action['id'] == cm.action1['id']:
                            acquiering_node = j[0]
                    if acquiering_node:
                        acquiering_node.set_end_time(cm.get_timeInstance())

            elif cm.command == "acquired free" or cm.command == "acquired" or cm.command == "waiting":
                node = None
                if (func in self.actionStacks) and len(self.actionStacks[func]) > 0 :
                    for j in self.actionStacks[func]:
                        if j.action['id'] == cm.action1['id']:
                            node = j

                if not node:
                    print "ERROR: the action does not exist and calls an action on resource command  ", cm.action1, " ",cm.command
                    continue


                if cm.command == "waiting":
                    new_wait_node = deepcopy(node)
                    new_wait_node.set_start_time(cm.get_timeInstance())
                    if cm.rsrc in self.rsrcStacks:
                        self.rsrcStacks[cm.rsrc].append((node, False))
                        self.rsrcStacks[cm.rsrc].append((new_wait_node, True))
                    else:
                        rsrc_ids[cm.rsrc] = curr_rsrc_id
                        curr_rsrc_id +=1
                        self.rsrcStacks[cm.rsrc] = [(node, False)]
                        self.rsrcStacks[cm.rsrc].append((new_wait_node, True))
                if cm.command == "acquired":
                    acquiering_node = None
                    if cm.rsrc in self.rsrcStacks and len(self.rsrcStacks[cm.rsrc]) > 0:
                        for j in self.rsrcStacks[cm.rsrc]:
                            if j[0].action['id'] == cm.action1['id']:
                                acquiering_node = j[0]
                    if not acquiering_node:
                        continue
                    acquiering_node.set_end_time(cm.get_timeInstance())
                if cm.command == "acquired free":
                    if cm.rsrc in self.rsrcStacks:
                        self.rsrcStacks[cm.rsrc].append((node, False))
                    else:
                        rsrc_ids[cm.rsrc] = curr_rsrc_id
                        curr_rsrc_id +=1
                        self.rsrcStacks[cm.rsrc] = [(node, False)]

            i += 1

        return self.action_root

    def get_action_ids(self):
        return action_ids
    def get_rsrcStack(self):
        return self.rsrcStacks


