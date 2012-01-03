#!/usr/bin/env python

from Tkinter import *
import model

class ViewportCard(object):
    '''
    Manages the graphical representation of a card in a
    Tkinter canvas. Creates and destroys items as necessary, facilitates
    editing, and so on and so forth.
    '''
    def __init__(self, viewport, card):
        self.card = card
        self.viewport = viewport
        self.canvas = viewport.canvas
        self.draw()
        self.moving = False
    def draw(self):
        self.window = Text(self.canvas)
        self.window.bind("<Button-1>", self.mousedown)
        self.window.bind("<Shift-Button-1>", self.shiftmousedown)
        self.window.bind("<B1-Motion>", self.mousemove)
        self.window.bind("<ButtonRelease-1>", self.mouseup)
        self.window.insert(END, self.card.text)
        self.itemid = self.canvas.create_window(
            self.card.x,
            self.card.y,
            window = self.window,
            anchor = "nw",
            width = self.card.w,
            height = self.card.h,
            tags = 'card'
        )
    def mousedown(self, event):
        self.window.lift()
    def shiftmousedown(self, event):
        self.mousedown(event)
        self.moving = True
        self.foocoords = (event.x, event.y)
    def mousemove(self, event):
        if self.moving:
            # coords are relative to card, not canvas
            if self.foocoords:
                delta = (event.x - self.foocoords[0], event.y - self.foocoords[1])
            else:
                delta = (event.x, event.y)
            self.canvas.move(self.itemid, delta[0], delta[1])
            self.viewport.reset_scroll_region()
    def mouseup(self, event):
        if self.moving:
            self.moving = False
            #print "new coords", self.canvas.coords(self.itemid)
 

class GPViewport(Frame):
    def __init__(self, master, datastore):
        Frame.__init__(self, None)
        # load data
        self.data = datastore
        self.width = self.data.config['viewport_w']
        self.height = self.data.config['viewport_h']
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
            bg = "white",
            width = self.width,
            height = self.height,
            xscrollincrement = 1,
            yscrollincrement = 1,
        )
        self.canvas.pack(expand=1, fill="both")
        # bind events
        self.canvas.bind("<Button-1>", self.mousedown)
        self.canvas.bind("<ButtonRelease-1>", self.mouseup)
        self.canvas.bind("<B1-Motion>", self.mousemove)
        self.canvas.bind("<Key>", self.keydown)
        # load cards
        self.cards = [ViewportCard(self, card) for card in self.data.get_cards()]
        self.reset_scroll_region()
        # set up scrolling
        self.yscroll["command"] = self.canvas.yview
        self.xscroll["command"] = self.canvas.xview
        self.canvas["yscrollcommand"] = self.yscroll.set
        self.canvas["xscrollcommand"] = self.xscroll.set
        self.canvas.xview(MOVETO, self.data.config['viewport_x'])
        self.canvas.yview(MOVETO, self.data.config['viewport_y'])
        # set up drag scrolling
        self.dragging = False
        self.last_drag_coords = None
    def reset_scroll_region(self):
        # set scroll region to bounding box of all card rects
        # with, say, 20 px margin
        box = self.canvas.bbox(ALL)
        #print "bbox: ", box
        self.canvas["scrollregion"] = box
    def utility_frame(self):
        "create and pack a frame for random tools"
        self.util = Frame(self, width = 100)
        self.util.pack(fill="y", side=LEFT)
        def scroll_to_top():
            self.canvas.xview(MOVETO, 0)
            self.canvas.yview(MOVETO, 0)
        button = Button(self.util, text="scroll", command=scroll_to_top)
        button.pack()
        def move_card():
            card = self.cards[0]
            self.canvas.move(card.itemid, 30, 30)
            self.reset_scroll_region()
        button = Button(self.util, text="moveit", command=move_card)
        button.pack()
    def mousedown(self, event):
        # take focus
        self.canvas.focus_set()
        # if not on an object, start dragging
        if not self.canvas.find_withtag(CURRENT):
            self.dragging = True
            self.last_drag_coords = (event.x, event.y)
    def mouseup(self, event):
        self.dragging = False
    def mousemove(self, event):
        if self.dragging:
            self.canvas.xview(SCROLL, self.last_drag_coords[0] - event.x, UNITS)
            self.canvas.yview(SCROLL, self.last_drag_coords[1] - event.y, UNITS)
            self.last_drag_coords = (event.x, event.y)
    def keydown(self, event):
        pass

root = Tk()
app = GPViewport(root, model.DataStore("test.sqlite"));
root.title("GraphPaper")
root["bg"] = "green"

root.mainloop()

