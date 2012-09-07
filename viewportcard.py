from Tkinter import *
from ScrolledText import ScrolledText
import tkMessageBox

from tkex import ResizableCanvasFrame
from slot import Slot

from viewportedge import ViewportEdge

from model import MIN_CARD_SIZE

class ViewportCard(object):
    '''
    Manages the graphical representation of a card in a
    Tkinter canvas. Creates and destroys items as necessary, facilitates
    editing, and so on and so forth.

    Members:
    * card: model.Card
    * viewport: GPViewport
    * gpfile: gpfile.GraphPaperFile, contains model.graph()
    * canvas: TKinter canvas we get drawn on
    * editing: bool, text is being edited
    * moving: bool, being dragged
    * moving_edgescroll_id: callback id to scroll periodically when hovering
      near edge of screen
    * resize_state: {}
    * resize_edgescroll_id: as moving_edgescroll_id
    * slot: calls callbacks whenever geometry changes
    * new_edge: if an edge is being dragged out from a handle, this is it.
    * card_after_new_edge: bool, if we should make a new card when edge is dropped.
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
        self.geom_slot = Slot()
        self.deletion_slot = Slot()
        self.new_edge = None

    def draw(self):
        self.frame_thickness = 5
        self.window = ResizableCanvasFrame(
            self.canvas,
            self.card.x,
            self.card.y,
            self.card.w,
            self.card.h,
            min_width = MIN_CARD_SIZE,
            min_height = MIN_CARD_SIZE
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
            new = self.canvas.create_oval(
                bbox[0], bbox[1], bbox[2], bbox[3],
                fill='green',
                outline=''
            )
            self.canvas.addtag_withtag('card_handle_tag', new) # for z-ordering
            self.canvas.tag_bind(new, '<Button-1>', self.handle_click)
            self.canvas.tag_bind(new, '<Shift-Button-1>', self.handle_shift_click)
            self.canvas.tag_bind(new, '<B1-Motion>', self.handle_mousemove)
            self.canvas.tag_bind(new, '<ButtonRelease-1>', self.handle_mouseup)
            return new
        x, y = self.window.canvas_coords()
        w, h = self.window.winfo_width(), self.window.winfo_height()
        # 2*radius should be < MIN_CARD_SIZE, and offset < radius
        radius = 30
        offset = 19 # offset of center of circle from card edge
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
        # have to do this every time, every time we recreate the edge handles
        self.viewport.fix_z_order()

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

    # next several functions are bound to the circular edge handles
    def handle_click(self, event):
        # create new edge
        self.new_edge = ViewportEdge(
            self.viewport,
            self.gpfile,
            None,
            self,
            None
        )
        self.new_edge.mousemove(event) # give it a real start pos

    def handle_shift_click(self, event):
        self.handle_click(event)
        self.new_edge.make_new_card = True

    def handle_mousemove(self, event):
        if self.new_edge:
            self.new_edge.mousemove(event)

    def handle_mouseup(self, event):
        if self.new_edge:
            self.new_edge.mouseup(event)
            self.new_edge = None

    def configure(self, event):
        self.redraw_edge_handles()

    def focusin(self, event):
        self.editing = True

    def focusout(self, event):
        self.editing = False
        self.save_text()

    def ctrldelete(self, event):
        title_sample = self.get_text().split('\n', 1)[0]
        if len(title_sample) > 20:
            title_sample = title_sample[:20] + '...'
        # delete the card
        if tkMessageBox.askokcancel(
            "Delete?",
            "Delete card \"%s\" and all its edges?" % title_sample
        ):
            for handle in self.edge_handles:
                self.canvas.delete(handle)
            self.deletion_slot.signal()
            self.viewport.remove_card(self)
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
 
    def add_geom_signal(self, fn):
        return self.geom_slot.add(fn)

    def remove_geom_signal(self, handle):
        self.geom_slot.remove(handle)

    def add_deletion_signal(self, fn):
        return self.deletion_slot.add(fn)

    def remove_deletion_signal(self, handle):
        self.deletion_slot.remove(handle)

    def geometry_callback(self):
        x, y = self.canvas_coords()
        w, h = self.window.winfo_width(), self.window.winfo_height()
        self.geom_slot.signal(self, x, y, w, h)

    def highlight(self):
        self.text.config(background='#ffffa2')

    def unhighlight(self):
        self.text.config(background='white')

