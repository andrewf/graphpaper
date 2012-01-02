#!/usr/bin/env python

from Tkinter import *
import model

class ViewportCard(object):
    '''
    Manages the graphical representation of a card in a
    Tkinter canvas. Creates and destroys items as necessary, facilitates editing
    '''
    pass

class GPViewport(Frame):
    def __init__(self, master, datastore):
        Frame.__init__(self, None)
        # load data
        self.data = datastore
        self.width = self.data.config['viewport_w']
        self.height = self.data.config['viewport_h']
        # set size to saved viewport size
        self.configure(
            width = self.width,
            height = self.height,
        )
        self.pack(expand=1, fill="both")
        # create scrollbars
        self.yscroll = Scrollbar(self)
        self.yscroll.pack(side="right", fill="y")
        self.xscroll = Scrollbar(self, orient=HORIZONTAL)
        self.xscroll.pack(side="bottom", fill="x")
        # create canvas
        self.canvas = Canvas(self, bg = "white", scrollregion = (-100, -100, self.width+100, self.height+100))
        self.canvas.pack(expand=1, fill="both")
        # draw fake stuff
        for c in self.data.get_cards():
            self.canvas.create_rectangle((c.x, c.y, c.x+c.w, c.y+c.h),
                fill="white"
            )
            self.canvas.create_text((c.x, c.y),
                width = c.w,
                anchor = "nw",
                justify = "left",
                text = c.text
            )
        # set up scrolling
        self.yscroll["command"] = self.canvas.yview
        self.xscroll["command"] = self.canvas.xview
        self.canvas["yscrollcommand"] = self.yscroll.set
        self.canvas["xscrollcommand"] = self.xscroll.set

root = Tk()
app = GPViewport(root, model.DataStore("test.sqlite"));
root.title("GraphPaper")
root["bg"] = "green"

root.mainloop()

