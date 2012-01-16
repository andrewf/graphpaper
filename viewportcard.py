from Tkinter import *
from ScrolledText import ScrolledText
import tkMessageBox

from tkex import ResizableCanvasFrame

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
        self.editing = False
        self.moving = False
        self.moving_edgescroll_id = None
        self.resize_state = None
        self.resize_edgescroll_id = None

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
        self.window.bind('<Configure>', self.configure)
        self.window.save_callback = self.save_card
        # draw edge handles
        self.edge_handles = None
        #self.redraw_edge_handles()

    def redraw_edge_handles(self):
        '''
        Either creates or modifies the edge handles, little circles poking
        out the side of the card, based on the current position and width.

        self.edge_handles is a list of itemids of the circles in (top,
        right, bottom, left) order.
        '''
        def create_circle(bbox):
            # create circle suitable for edge-handle use
            return self.canvas.create_oval(
                bbox[0], bbox[1], bbox[2], bbox[3],
                fill='blue',
                outline=''
            )
        x, y = self.window.canvas_coords()
        w, h = self.window.winfo_width(), self.window.winfo_height()
        radius = 40
        offset = 30 # offset of center of circle from card edge
        left_coords = (x + offset, y + h/2)
        right_coords = (x + w - offset, y + h/2)
        top_coords = (x + w/2 , y + offset)
        bottom_coords = (x + w/2, y + h - offset)
        all_coords = (top_coords, right_coords, bottom_coords, left_coords)
        bboxes = [ (x-radius, y-radius, x+radius, y+radius) for x, y in all_coords]
        if self.edge_handles:
            # move the edge handles
            for i, box in enumerate(bboxes):
                #self.canvas.coords(handle, box[0], box[1], box[2], box[3])
                self.canvas.delete(self.edge_handles[i])
                self.edge_handles[i] = create_circle(box)
                #self.canvas.itemconfig(handle, bbox = box)
        else:
            # create new ones
            self.edge_handles = [
                create_circle(b) for b in bboxes
            ]

    def get_text(self):
        "gets the text from the actual editor, which may not be saved yet"
        return self.text.get('0.0', END)

    def save_text(self):
        # get text from window
        text = self.get_text()
        if text != self.card.text:
            self.card.text = text

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
            self.viewport.reset_scroll_region()
            return "break"

    def mouseup(self, event):
        if self.moving:
            self.moving = False
            new_coords = self.canvas_coords()
            self.card.set_pos(new_coords[0], new_coords[1])
            self.cancel_moving_edgescroll_callback()

    def configure(self, event):
        print 'configure'
        self.redraw_edge_handles()

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
            for handle in self.edge_handles:
                self.canvas.delete(handle)
            self.card.delete()
            self.window.destroy()
        return "break"

    def save_card(self):
        # grab values from self.window
        self.card._x, self.card._y = self.window.canvas_coords()
        self.card.w, self.card._h = self.window.winfo_width(), self.window.winfo_height()
        self.card.save()
        
 
