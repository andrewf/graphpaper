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
        self.rectid = self.textid = None
    def draw(self):
        self.rectid = self.canvas.create_rectangle(
            (self.card.x, self.card.y, self.card.x+self.card.w, self.card.y+self.card.h),
            fill="white"
        )
        # text with 5px padding
        pad = 5
        self.textid = self.canvas.create_text(
            (self.card.x + pad, self.card.y + pad),
            width = self.card.w - 2 * pad,
            anchor = "nw",
            justify = "left",
            text = self.card.text
        )


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
        self.cards = [ViewportCard(self, card) for card in self.data.get_cards()]
        # set up scrolling
        self.yscroll["command"] = self.canvas.yview
        self.xscroll["command"] = self.canvas.xview
        self.canvas["yscrollcommand"] = self.yscroll.set
        self.canvas["xscrollcommand"] = self.xscroll.set
        self.canvas.xview(MOVETO, self.data.config['viewport_x'])
        self.canvas.yview(MOVETO, self.data.config['viewport_y'])
    def reset_scroll_region(self):
        # set scroll region to bounding box of all card rects
        # with, say, 20 px margin
        pass

root = Tk()
app = GPViewport(root, model.DataStore("test.sqlite"));
root.title("GraphPaper")
root["bg"] = "green"

root.mainloop()

