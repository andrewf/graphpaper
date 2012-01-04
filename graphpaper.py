#!/usr/bin/env python

from Tkinter import *
import tkMessageBox
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
        self.editing = False
    def draw(self):
        self.window = Text(self.canvas)
        self.window.bind("<Button-1>", self.mousedown)
        self.window.bind("<Shift-Button-1>", self.shiftmousedown)
        self.window.bind("<B1-Motion>", self.mousemove)
        self.window.bind("<ButtonRelease-1>", self.mouseup)
        self.window.bind("<FocusIn>", self.focusin)
        self.window.bind("<FocusOut>", self.focusout)
        self.window.bind("<Control-Delete>", self.ctrldelete)
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
    def save_text(self):
        # get text from window
        text = self.window.get('0.0', END)
        if text != self.card.text:
            print 'new card text: "%s"' % text
            self.card.text = text
        else:
            print 'card unchanged'
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
            new_coords = map(int, self.canvas.coords(self.itemid))
            self.card.set_pos(new_coords[0], new_coords[1])
    def focusin(self, event):
        print "focusing text"
        self.editing = True
    def focusout(self, event):
        self.editing = False
        self.save_text()
    def ctrldelete(self, event):
        # delete the card
        if tkMessageBox.askokcancel("Delete?", "Delete card?"):
            # delete card, item, window
            self.card.delete()
            self.canvas.delete(self.itemid)
            self.window.destroy()
 

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
        self.canvas.bind("<Control-Button-1>", self.ctrlclick)
        self.canvas.bind("<B1-Motion>", self.mousemove)
        self.canvas.bind("<Key>", self.keydown)
        self.canvas.bind("<Configure>", self.resize)
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
        offset = 20
        self.canvas["scrollregion"] = (
            box[0] - offset,
            box[1] - offset,
            box[2] + offset,
            box[3] + offset)
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
    def new_card(self, x, y, w, h):
        self.cards.append(ViewportCard(self, self.data.new_card(x, y, w, h)))
    def save_scroll_pos(self):
        # save current scrolling position to config
        new_x = (self.canvas.canvasx(0))
        new_y = (self.canvas.canvasy(0))
        self.data.config["viewport_x"] = new_x
        self.data.config["viewport_y"] = new_y
    def ctrlclick(self, event):
        default_w = 200
        default_h = 150
        new_x = self.canvas.canvasx(event.x) - default_w/2
        new_y = self.canvas.canvasy(event.y) - default_h/2
        self.new_card(new_x, new_y, default_w, default_h)
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
    def keydown(self, event):
        pass
    def resize(self, event):
        self.data.config["viewport_w"] = event.width - 2
        self.data.config["viewport_h"] = event.height - 2

root = Tk()
app = GPViewport(root, model.DataStore("test.sqlite"));
root.title("GraphPaper")
root["bg"] = "green"

root.mainloop()

