#!/usr/bin/env python

import sys
import os

from Tkinter import *
import tkMessageBox
import tkFileDialog

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
        self.resize_state = None
    def draw(self):
        self.frame_thickness = 5
        self.window = Frame(self.canvas, borderwidth=self.frame_thickness, cursor='fleur')
        self.text = Text(self.window)
        self.text.pack(expand=1, fill='both')
        # set up text for editing, dragging, deleting
        self.text.bind("<Button-1>", self.mousedown)
        self.text.bind("<Shift-Button-1>", self.shiftmousedown)
        self.text.bind("<Double-Button-1>", self.doubleclick)
        self.text.bind("<B1-Motion>", self.mousemove)
        self.text.bind("<ButtonRelease-1>", self.mouseup)
        self.text.bind("<FocusIn>", self.focusin)
        self.text.bind("<FocusOut>", self.focusout)
        self.text.bind("<Control-Delete>", self.ctrldelete)
        self.text.insert(END, self.card.text)
        # set up frame for resizing
        self.window.bind("<Button-1>", self.frame_mousedown)
        self.window.bind("<B1-Motion>", self.frame_mousemove)
        self.window.bind("<ButtonRelease-1>", self.frame_mouseup)
        # add item to canvas
        self.itemid = self.canvas.create_window(
            self.card.x,
            self.card.y,
            window = self.window,
            anchor = "nw",
            width = self.card.w,
            height = self.card.h,
            tags = 'card'
        )
    def get_text(self):
        "gets the text from the actual editor, which may not be saved yet"
        return self.text.get('0.0', END)
    def save_text(self):
        # get text from window
        text = self.get_text()
        if text != self.card.text:
            #print 'new card text: "%s"' % text
            self.card.text = text
        #else:
            #print 'card unchanged'
    def canvas_coords(self):
        return map(int, self.canvas.coords(self.itemid))
    def start_moving(self, event):
        # set up state for a drag
        self.moving = True
        self.foocoords = (event.x, event.y)
    def mousedown(self, event):
        self.window.lift()
    def doubleclick(self, event):
        self.start_moving(event)
        return 'break'
    def shiftmousedown(self, event):
        self.mousedown(event)
        self.start_moving(event)
        return "break"
    def mousemove(self, event):
        if self.moving:
            # coords are relative to card, not canvas
            if self.foocoords:
                delta = (event.x - self.foocoords[0], event.y - self.foocoords[1])
            else:
                delta = (event.x, event.y)
            self.canvas.move(self.itemid, delta[0], delta[1])
            self.viewport.reset_scroll_region()
            return "break"
    def mouseup(self, event):
        if self.moving:
            self.moving = False
            new_coords = self.canvas_coords()
            self.card.set_pos(new_coords[0], new_coords[1])
    def focusin(self, event):
        #print "focusing text"
        self.editing = True
    def focusout(self, event):
        self.editing = False
        self.save_text()
    def ctrldelete(self, event):
        title_sample = self.get_text().split('\n', 1)[0]
        if len(title_sample) > 20:
            title_sample = title_sample[:20] + '...'
        # delete the card
        if tkMessageBox.askokcancel("Delete?", "Delete card \"%s\"?" % title_sample):
            # delete card, item, window
            self.card.delete()
            self.canvas.delete(self.itemid)
            self.window.destroy()
        return "break"
    def frame_mousedown(self, event):
        # store initial coords and which edges are 
        self.resize_state = {
            'start_coords': (event.x, event.y),
            'last_coords': (event.x, event.y),
            'left_edge': (0 <= event.x <= self.frame_thickness),
            'right_edge': (event.x >= self.window.winfo_width() - self.frame_thickness),
            'top_edge': (0 < event.y < self.frame_thickness),
            'bottom_edge': (event.y > self.window.winfo_height() - self.frame_thickness)
        }
    def frame_mousemove(self, event):
        if self.resize_state:
            resize = self.resize_state # debug var
            event_x = event.x
            event_y = event.y
            # distance of cursor from original position of window
            delta = map(int, (event.x - self.resize_state['start_coords'][0],
                              event.y - self.resize_state['start_coords'][1]))
            # load current pos, size
            new_x, new_y = self.canvas_coords()
            new_width = int(self.canvas.itemcget(self.itemid, 'width'))
            new_height = int(self.canvas.itemcget(self.itemid, 'height'))
            # handle x resize/move
            if self.resize_state['left_edge']:
                # must move pos and resize
                new_x += delta[0]
                new_width -= delta[0]
            elif self.resize_state['right_edge']:
                new_width += (event.x - self.resize_state['last_coords'][0])
            # handle y resize/move
            if self.resize_state['top_edge']:
                new_y += delta[1]
                new_height -= delta[1]
            elif self.resize_state['bottom_edge']:
                new_height += (event.y - self.resize_state['last_coords'][1])
            # save new settings in item, not card yet
            self.resize_state['last_coords'] = (event.x, event.y)
            self.canvas.coords(self.itemid, new_x, new_y)
            self.canvas.itemconfig(self.itemid, width=new_width, height=new_height)
    def frame_mouseup(self, event):
        if self.resize_state:
            self.card._x, self.card._y = self.canvas_coords()
            self.card._w = int(self.canvas.itemcget(self.itemid, 'width'))
            self.card._h = int(self.canvas.itemcget(self.itemid, 'height'))
            #print 'saving:', self.card.x, self.card.y, self.card.w, self.card.h
            self.card.save()
            self.resize_state = None
 

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
        if not box:
            return # no objects, we'll have to set scrollregion later
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
    def new_card(self, x, y, w, h):
        newcard = ViewportCard(self, self.data.new_card(x, y, w, h))
        self.cards.append(newcard)
        return newcard
    def save_scroll_pos(self):
        # save current scrolling position to config
        new_x = (self.canvas.canvasx(0))
        new_y = (self.canvas.canvasy(0))
        self.data.config["viewport_x"] = new_x
        self.data.config["viewport_y"] = new_y
    def doubleclick(self, event):
        '''Create a new card on the canvas and focus it'''
        default_w = int(self.data.config["default_card_w"] or 200)
        default_h = int(self.data.config["default_card_h"] or 150)
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
    def keydown(self, event):
        pass
    def resize(self, event):
        self.data.config["viewport_w"] = event.width - 2
        self.data.config["viewport_h"] = event.height - 2

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
            self.viewport.destroy() # better hope that last card is saved
        self.viewport = GPViewport(self.root, model.DataStore(filename, load_sample_data))
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

