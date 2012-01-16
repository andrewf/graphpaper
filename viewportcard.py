from Tkinter import *
from ScrolledText import ScrolledText
import tkMessageBox

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
        self.window = Frame(self.canvas, borderwidth=self.frame_thickness, cursor='fleur')
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
            self.card.text = text

    def canvas_coords(self):
        return map(int, self.canvas.coords(self.itemid))

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
        self.canvas.move(self.itemid, scroll_x, scroll_y)
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
            self.canvas.move(self.itemid, delta[0], delta[1])
            self.viewport.reset_scroll_region()
            return "break"

    def mouseup(self, event):
        if self.moving:
            self.moving = False
            new_coords = self.canvas_coords()
            self.card.set_pos(new_coords[0], new_coords[1])
            self.cancel_moving_edgescroll_callback()

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
 
