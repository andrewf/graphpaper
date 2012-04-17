#!/usr/bin/env python

import sys
import os

from Tkinter import *
import tkFileDialog

import model
import gpfile

from viewportcard import ViewportCard
from viewportedge import ViewportEdge


class GPViewport(Frame):
    def __init__(self, master, gpfile):
        Frame.__init__(self, None)
        # load data
        self.gpfile = gpfile
        self.data = gpfile.graph
        self.config = gpfile.config
        self.width = self.config['viewport_w']
        self.height = self.config['viewport_h']
        # display self, create util frame
        self.pack(expand=1, fill="both")
        self.utility_frame()
        # create scrollbars
        self.yscroll = Scrollbar(self)
        self.yscroll.pack(side="right", fill="y")
        self.xscroll = Scrollbar(self, orient=HORIZONTAL)
        self.xscroll.pack(side="bottom", fill="x")
        # create canvas
        self.canvas = Canvas(self,
            bg = "lavender",
            width = self.width,
            height = self.height,
            xscrollincrement = 1,
            yscrollincrement = 1,
        )
        self.canvas.pack(expand=1, fill="both")
        # bind events
        self.canvas.bind("<Button-1>", self.mousedown)
        self.canvas.bind("<ButtonRelease-1>", self.mouseup)
        self.canvas.bind("<Double-Button-1>", self.doubleclick)
        self.canvas.bind("<B1-Motion>", self.mousemove)
        self.canvas.bind("<Configure>", self.resize)
        # load cards
        cards_by_id = {}
        self.cards = []
        for card in self.data.get_cards():
            new = ViewportCard(self, self.gpfile, card)
            self.cards.append(new)
            cards_by_id[card.obj.oid] = new
        self.reset_scroll_region()
        # load edges
        self.edges = []
        for edge in self.data.get_edges():
            new = ViewportEdge(
                self,
                self.gpfile,
                edge,
                cards_by_id[edge.orig.obj.oid],
                cards_by_id[edge.dest.obj.oid]
            )
            self.edges.append(new)
        # test edges
#        edge = model.Edge(self.data, orig=self.data.get_cards()[0], dest=self.data.get_cards()[1])
#        self.edge = ViewportEdge(self, self.gpfile, edge, self.cards[0], self.cards[1])
        # set up scrolling
        self.yscroll["command"] = self.canvas.yview
        self.xscroll["command"] = self.canvas.xview
        self.canvas["yscrollcommand"] = self.yscroll.set
        self.canvas["xscrollcommand"] = self.xscroll.set
        self.canvas.xview(MOVETO, self.config['viewport_x'])
        self.canvas.yview(MOVETO, self.config['viewport_y'])
        # set up drag scrolling
        self.dragging = False
        self.last_drag_coords = None

    def reset_scroll_region(self):
        # set scroll region to bounding box of all card rects
        # with, say, 20 px margin
        box = self.canvas.bbox(ALL)
        if not box:
            return # no objects, we'll have to set scrollregion later
        offset = 20
        self.canvas["scrollregion"] = (
            box[0] - offset,
            box[1] - offset,
            box[2] + offset,
            box[3] + offset)

    def card_collision(self, p):
        '''
        Return first card which the point p collides with, or None
        if there is no collision.
        '''
        for card in self.cards:
            c = card.card
            if not (c.x <= p[0] <= (c.x + c.w)):
                continue
            if not (c.y <= p[1] <= (c.y + c.h)):
                continue
            return card
        return None

    def utility_frame(self):
        "create and pack a frame for random tools"
        self.util = Frame(self, width = 100)
        self.util.pack(fill="y", side=LEFT)

    def new_card(self, x, y, w, h):
        print 'new card', x, y, w, h
        newcard = ViewportCard(
            self,
            self.gpfile,
            self.data.new_card(x, y, w, h)
        )
        self.data.commit()
        self.cards.append(newcard)
        return newcard

    def save_scroll_pos(self):
        # save current scrolling position to config
        new_x = (self.canvas.canvasx(0))
        new_y = (self.canvas.canvasy(0))
        self.config["viewport_x"] = new_x
        self.config["viewport_y"] = new_y

    def edge_scroll(self, canvas_mouse_coords):
        '''
        Given a mouse position in canvas coordinates, scroll a little bit and
        return the distance scrolled. Scrolling happens if the cursor is in
        a band of space around the outer edges.
        '''
        region_size = 70
        window_width = self.canvas.winfo_width()
        window_height = self.canvas.winfo_height()
        x0, y0 = self.canvas.canvasx(0), self.canvas.canvasy(0)
        # get mouse pos in the visible
        window_coords = (canvas_mouse_coords[0] - x0,
                         canvas_mouse_coords[1] - y0)
        # x scroll
        if window_coords[0] <= region_size:
            # scroll is negative when on top/left
            scroll_x = window_coords[0] - region_size
        elif (window_width - region_size) <= window_coords[0]:
            scroll_x = region_size - (window_width - window_coords[0])
        else:
            scroll_x = 0
        # y scroll
        if window_coords[1] <= region_size:
            # scroll is negative when on top/left
            scroll_y = window_coords[1] - region_size
        elif (window_height - region_size) <= window_coords[1]:
            scroll_y = region_size - (window_height - window_coords[1])
        else:
            scroll_y = 0
        # scale the movements
        scale_factor = 0.5
        scroll_x *= scale_factor
        scroll_y *= scale_factor
        # move and return
        self.canvas.xview_scroll(int(scroll_x), UNITS)
        self.canvas.yview_scroll(int(scroll_y), UNITS)
        #print 'canvas_mouse_coords', canvas_mouse_coords, 'window_coords', window_coords, 'edge scroll', scroll_x, scroll_y
        return scroll_x, scroll_y

    def doubleclick(self, event):
        '''Create a new card on the canvas and focus it'''
        default_w = int(self.config["default_card_w"] or 200)
        default_h = int(self.config["default_card_h"] or 150)
        new_x = self.canvas.canvasx(event.x) - default_w/2
        new_y = self.canvas.canvasy(event.y) - default_h/2
        newcard = self.new_card(new_x, new_y, default_w, default_h)
        newcard.text.focus_set()
        self.reset_scroll_region()

    def mousedown(self, event):
        # take focus
        self.canvas.focus_set()
        # if not on an object, start dragging
        if not self.canvas.find_withtag(CURRENT):
            self.dragging = True
            self.last_drag_coords = (event.x, event.y)

    def mouseup(self, event):
        if self.dragging:
            # commit scroll
            self.save_scroll_pos()
            self.dragging = False

    def mousemove(self, event):
        if self.dragging:
            self.canvas.xview(SCROLL, self.last_drag_coords[0] - event.x, UNITS)
            self.canvas.yview(SCROLL, self.last_drag_coords[1] - event.y, UNITS)
            self.last_drag_coords = (event.x, event.y)

    def resize(self, event):
        self.config["viewport_w"] = event.width - 2
        self.config["viewport_h"] = event.height - 2


class GPApp(object):
    def __init__(self, filename):
        self.root = Tk()
        self.root["bg"] = "green"
        self.root.title("GraphPaper!")
        self.viewport = None
        self.default_filename = 'instructions.gp'
        self.openfile(filename)
        # create menus:
        # File:
        #   Open
        # Edit:
        #   Default Card Size (disabled)
        rootmenu = Menu(self.root)
        # file menu
        filemenu = Menu(rootmenu, tearoff=0)
        rootmenu.add_cascade(menu=filemenu, label='File')
        filemenu.add_command(label="Open", command = self.choosefile)
        filemenu.add_command(label="Create", command = self.newfile)
        # edit menu
        editmenu = Menu(rootmenu, tearoff=0)
        rootmenu.add_cascade(menu=editmenu, label='Edit')
        editmenu.add_command(label="Default Card Size", state='disabled')
        self.root.config(menu=rootmenu)
        # settings for tkFileDialog
        self.file_dialog_settings = dict(
            defaultextension = '.gp',
            filetypes = (('GraphPaper files', '.gp'), ('sqlite files', '.sqlite')),
            title = 'GraphPaper'
        )
        # set ctrl-o to open, ctrl-n to new
        self.root.bind('<Control-o>', self.choosefile)
        self.root.bind('<Control-n>', self.newfile)

    def mainloop(self):
        self.root.mainloop()

    def openfile(self, filename):
        # creates new GPViewport
        # loads sample data if filename is None
        print 'opening "%s"' % filename
        load_sample_data = filename is None
        filename = filename or self.default_filename
        if self.viewport:
            self.viewport.destroy()
        self.viewport = GPViewport(self.root, gpfile.GraphPaperFile(filename))
        self.root.title('GraphPaper - %s' % filename)

    def newfile(self, *args):
        # *args lets it be both an event binding and menu command
        filename = tkFileDialog.asksaveasfilename(**self.file_dialog_settings)
        if filename:
            self.openfile(filename)
    
    def choosefile(self, *args):
        filename = tkFileDialog.askopenfilename(**self.file_dialog_settings)
        if filename:
            self.openfile(filename)
    

if __name__ == '__main__':
    # get optional cmdline file arg
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = None 
    # load app
    app = GPApp(filename)
    app.mainloop()

