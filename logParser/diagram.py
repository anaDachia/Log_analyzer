
import wx

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from datetime import datetime, date
import scipy
import random
import matplotlib.pyplot as plt
from matplotlib.backend_bases import NavigationToolbar2


class RsrcPanel(wx.Panel):
    """
    Each instance of this class makes a tab containing a resource usage graph
    """
    #----------------------------------------------------------------------
    def __init__(self, parent, data):
        """"""

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        #sizer = wx.BoxSizer(wx.VERTICAL)
        #txtOne = wx.TextCtrl(self, wx.ID_ANY, "")
        #txtTwo = wx.TextCtrl(self, wx.ID_ANY, "")

        fig,ax = plt.subplots()
        f = fig.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, fig)
        self.toolbar=NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.TOP | wx.GROW)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

        m = MyPlot(line= None, start_time=data["start_time"])
        m.make_resource_graph(f, ax,data["rsrc"])

class ActionPanel(wx.Panel):
    """
    An instance of this class makes a tab containing an action timing graph
    """
    def __init__(self, parent, data):
        """"""
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        #sizer = wx.BoxSizer(wx.VERTICAL)
        #txtOne = wx.TextCtrl(self, wx.ID_ANY, "")
        #txtTwo = wx.TextCtrl(self, wx.ID_ANY, "")

        fig,ax = plt.subplots()
        f = fig.add_subplot(111)
        self.f =f
        self.canvas = FigureCanvas(self, -1, fig)
        f.canvas = self.canvas
        self.toolbar=NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.TOP | wx.GROW)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()



        m = MyPlot(line= None, start_time=data["start_time"])
        m.make_action_graph(data["nodes"], self.f, ax)


        button = wx.Button(self.canvas, wx.ID_ANY, 'Home')
        self.Bind(wx.EVT_BUTTON, lambda event, arg=(f, m, ax, data ): self.go_back(event, arg))

    def go_back(self,event, arg):
        arg[0].clear()
        arg[1].make_action_graph(arg[3]["nodes"], self.f, arg[2])


##############################################################################
home = NavigationToolbar2.home

def new_home(self, *args, **kwargs):
    print 'new home'
    home(self, *args, **kwargs)



########################################################################
class NotebookDemo(wx.Notebook):
    """
    A container class for tabs.
    """

    #----------------------------------------------------------------------
    def __init__(self, parent, data):
        wx.Notebook.__init__(self, parent, id=wx.ID_ANY, style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             )

        action_ids  = data["action_ids"]
        global action_ids


        tabs = []
        tab = ActionPanel(self,data)
        global tab
        tabs.append(tab)
        self.AddPage(tab, "Action Timing")


        for rsrc in data["rsrcStack"]:
            data["rsrc"] = data["rsrcStack"][rsrc]
            tab = RsrcPanel(self, data)
            tabs.append(tab)
            self.AddPage(tab, "%s Usage" %rsrc)


class MyPlot:
    """
    This class contains methods for making different digrams.
    """
    def __init__(self, line, node=None, start_time = None,):
        self.line = line
        self.press = None
        self.node = node
        self.start_time = start_time
        #################

    def connect(self):
        self.line.figure.canvas.mpl_connect('button_press_event', self.on_press)

    @staticmethod
    def change_page(ax,myplot):
        fig = ax.get_figure()
        def kuft(event):
            myplot.on_press(event,ax)

        fig.canvas.mpl_connect('button_press_event',kuft)
        return kuft


    @staticmethod
    def zoom_factory(ax,base_scale = 2.):

        def zoom_fun(event):

            # get the current x and y limits
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()
            cur_xrange = (cur_xlim[1] - cur_xlim[0])*.5
            cur_yrange = (cur_ylim[1] - cur_ylim[0])*.5
            xdata = event.xdata # get event x location
            ydata = event.ydata # get event y location
            if event.button == 'up':

                scale_factor = 1/base_scale
            elif event.button == 'down':
                scale_factor = base_scale
            else:
                scale_factor = 1
                print event.button
            # set new limits

            ax.set_xlim([xdata - cur_xrange*scale_factor,
                         xdata + cur_xrange*scale_factor])
            ax.set_ylim([ydata - cur_yrange*scale_factor,
                         ydata + cur_yrange*scale_factor])
            ax.get_figure().canvas.draw()

        fig = ax.get_figure()
        fig.canvas.mpl_connect('scroll_event',zoom_fun)
        return zoom_fun


    # Event call back for action timing diagram to move to the subgraph
    def on_press(self,event,f):
        global history
        if event.inaxes != self.line.axes: return
        contains, attrd = self.line.contains(event)
        if not contains: return

        lines = []

        f.clear()
        local_labels = []
        for ch in self.node.children:
            self._aux_make_line(node=ch,start_time=self.start_time, figure=f,lines= lines)
            if not ch.action["name"] in local_labels :
                local_labels.append(ch.action["name"])

        labels = [-1 for i in range (0,len(action_ids))] #action_ids
        for label in action_ids:
            labels[action_ids[label]] = label #action_ids[label]

        f.set_yticks(scipy.arange(0, len(labels), 1))
        f.set_yticklabels(labels)
        plt.margins(0.1)
        f.canvas.draw()


    @staticmethod
    def _aux_make_line( node, start_time,figure, lines, color = None, hierarchy = True):
        #TODO check why this happens!!
        if node.id == 0 or node.Parent == None:
            return
        if node.activeTime[0] == -1 :
            node.activeTime = (node.Parent.activeTime[0], node.activeTime[1])
        if node.activeTime[1] == -1 :
            node.activeTime = (node.activeTime[0],node.Parent.activeTime[1])
        if (node.activeTime[0] == -1  or node.activeTime[1] == -1):
            print("dge nakhodesh na parentesh time nadashtan!!! {0} : {1} {2}: {3}".format(node.id, node.action
                                                                                    ,node.activeTime[0],node.activeTime[1]))
            return

        ##################################
        delta1 = datetime.combine(date.today(), node.activeTime[0]) - datetime.combine(date.today(), start_time)
        delta2 = datetime.combine(date.today(), node.activeTime[1]) - datetime.combine(date.today(), start_time)


        if not color:
            r = lambda: random.randint(0,255)
            line_color = '#%02X%02X%02X' % (r(),r(),r())
        else:
            line_color = color

        if len(node.children )> 0 :
            line =  figure.hlines(action_ids[node.action["name"]], delta1.total_seconds(),
                        delta2.total_seconds(), colors="black", lw=15)
        line =  figure.hlines(action_ids[node.action["name"]], delta1.total_seconds(),
            delta2.total_seconds(), colors=line_color, lw=10)

        if len(node.children) > 0 and hierarchy:

            mp = MyPlot(line, node,start_time)
            MyPlot.change_page(figure,mp)
            lines.append(mp)




    def make_action_graph (self, node_list, f, ax):

        lines = []
        for node in node_list:
            MyPlot._aux_make_line(node=node, start_time = self.start_time, figure=f, lines=lines)

            for ch in node.children:
                #print ch.id
                MyPlot._aux_make_line(node= ch, start_time = self.start_time, figure=f, lines=lines)


        #fig.canvas.draw()
        labels = [-1 for i in range (0,len(action_ids))]

        for label in action_ids:
            labels[action_ids[label]] = label

        ax.set_yticks(scipy.arange(0, len(labels), 1))
        MyPlot.zoom_factory(ax,base_scale=1.5)
        ax.set_yticklabels(labels)
        plt.margins(0.1)
        plt.tight_layout()
        f.canvas.draw()




    def make_resource_graph(self,f ,ax,rsrc):
        lines = []
        for tup in rsrc:
            color = "red"
            if tup[1]:
                color = "yellow"
            MyPlot._aux_make_line(color=color, start_time=self.start_time, node=tup[0], figure=f, lines=lines)
        #fig.canvas.draw()
        labels = [-1 for i in range (0,len(action_ids))]

        for label in action_ids:
            labels[action_ids[label]] = label

        ax.set_yticks(scipy.arange(0, len(labels), 1))
        MyPlot.zoom_factory(ax,base_scale=1.5)
        ax.set_yticklabels(labels)
        plt.margins(0.1)
        plt.tight_layout()
        #plt.show()



########################################################################


class GraphMaker(wx.Frame):
    """
    this class is the main class to be instanced for creating action and resource graph
    """
    #----------------------------------------------------------------------
    def __init__(self, nodes, start_time, action_ids, rsrcStack):
        """Constructor"""
        wx.Frame.__init__(self, None, wx.ID_ANY,
                          "Log Analysis",
                          size=(800,800)
                          )

        self.data ={"nodes" : nodes, "start_time" : start_time, "action_ids" :action_ids, "rsrcStack" : rsrcStack}

        panel = wx.Panel(self)
        notebook = NotebookDemo(panel, self.data)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(sizer)
        self.Layout()

        self.Show()

#----------------------------------------------------------------------
