from Tkinter import *
from ScrolledText import ScrolledText
import tkMessageBox

from tkex import ResizableCanvasFrame
from slot import Slot

class ViewportCard(object):
    '''
    Manages the graphical representation of a card in a
    Tkinter canvas. Creates and destroys items as necessary, facilitates
    editing, and so on and so forth.
    '''
    def __init__(self, viewport, gpfile, card):
        self.card = card
        self.viewport = viewport
        self.gpfile = gpfile
        self.canvas = viewport.canvas
        self.draw()
        self.editing = False
        self.moving = False
        self.moving_edgescroll_id = None
        self.resize_state = None
        self.resize_edgescroll_id = None
        # slot triggered when geometry (pos/size) changes
        # fn args: (self, x, y, w, h)
        self.slot = Slot()

    def draw(self):
        self.frame_thickness = 5
        self.window = ResizableCanvasFrame(
            self.canvas,
            self.card.x,
            self.card.y,
            self.card.w,
            self.card.h,
        )
        self.text = ScrolledText(self.window, wrap=WORD)
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
        #self.window.bind('<Configure>', self.configure)
        self.window.save_callback = self.save_card

    def get_text(self):
        "gets the text from the actual editor, which may not be saved yet"
        return self.text.get('0.0', END)

    def save_text(self):
        # get text from window
        text = self.get_text()
        if text != self.card.text:
            self.card.text = text
            self.gpfile.commit()

    def canvas_coords(self):
        return self.window.canvas_coords()

    def start_moving(self, event):
        # set up state for a drag
        self.moving = True
        self.foocoords = (event.x, event.y)
        self.set_moving_edgescroll_callback()

    def edge_scroll(self):
        # if any edges are too close to the edge, move and scroll the canvas
        canvas_coords = self.canvas_coords()
        relative_mouse_pos = self.foocoords
        canvas_mouse_coords = (
            canvas_coords[0] + relative_mouse_pos[0] + self.frame_thickness,
            canvas_coords[1] + relative_mouse_pos[1] + self.frame_thickness
        )
        scroll_x, scroll_y = self.viewport.edge_scroll(canvas_mouse_coords)
        # move the opposite direction the viewport scrolled
        scroll_x, scroll_y = -scroll_x, -scroll_y
        #print 'card.edgescroll x y', scroll_x, scroll_y, 'relative_mouse_pos', relative_mouse_pos
        self.window.move(scroll_x, scroll_y)
        self.viewport.reset_scroll_region()
        self.set_moving_edgescroll_callback()

    def set_moving_edgescroll_callback(self):
        self.moving_edgescroll_id = self.text.after(10, self.edge_scroll)

    def cancel_moving_edgescroll_callback(self):
        self.text.after_cancel(self.moving_edgescroll_id)
        self.moving_edgescroll_id = None

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
            self.window.move(delta[0], delta[1])
            self.geometry_callback()
            self.viewport.reset_scroll_region()
            return "break"

    def mouseup(self, event):
        if self.moving:
            self.moving = False
            new_coords = self.canvas_coords()
            self.card.x, self.card.y = new_coords[0], new_coords[1]
            self.gpfile.commit()
            self.cancel_moving_edgescroll_callback()
            self.geometry_callback()

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
            self.window.destroy()
            self.gpfile.commit()
        return "break"

    def save_card(self):
        # grab values from self.window,
        # and put them in the model.card
        self.card.x, self.card.y = self.window.canvas_coords()
        self.card.w, self.card.h = self.window.winfo_width(), self.window.winfo_height()
        self.geometry_callback() # here so it gets called after resizing
        self.gpfile.commit()
 
    def add_signal(self, fn):
        return self.slot.add(fn)

    def remove_signal(self, handle):
        self.slot.remove(handle)

    def geometry_callback(self):
        x, y = self.canvas_coords()
        w, h = self.window.winfo_width(), self.window.winfo_height()
        self.slot.signal(self, x, y, w, h)

    def highlight(self):
        self.text.config(background='#ffffa2')

    def unhighlight(self):
        self.text.config(background='white')

