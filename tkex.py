'''
Extra helpful widgets for Tkinter.
'''

from Tkinter import *

class ResizableCanvasFrame(Frame):
    '''
    Class that handles creating resizable frames on a canvas.
    Don't pack it.

    Set save_callback to whatever you want to happen when the mouse
    lets up on the border.
    '''
    def __init__(self, master, x, y, w, h, *args, **kwargs):
        # pull min_width, min_height from kwargs
        self.min_width = kwargs.pop('min_width', 0)
        self.min_height = kwargs.pop('min_height', 0)
        # master should be a Canvas
        self.frame_thickness = 5
        Frame.__init__(
            self,
            master,
            *args,
            borderwidth = self.frame_thickness,
            cursor = 'fleur',
            **kwargs
        )
        self.canvas = master
        self.resize_state = None
        self.bind('<Button-1>', self.mousedown)
        self.bind('<B1-Motion>', self.mousemove)
        self.bind('<ButtonRelease-1>', self.mouseup)
        self.bind('<Destroy>', self.delete_item)
        # add self to canvas
        self.itemid = self.canvas.create_window(
            x,
            y,
            window=self,
            anchor="nw",
            width=w,
            height=h
        )
        self.save_callback = None
        
    def canvas_coords(self):
        "Window position on canvas as a tuple of integers"
        return map(int, self.canvas.coords(self.itemid))
    
    def move(self, dx, dy):
        # strictly, this is out of the range of RCF,
        # but it helps with the law of demeter
        self.canvas.move(self.itemid, dx, dy)

    def mousedown(self, event):
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        self.resize_state = {
            'start_coords': (event.x, event.y),
            'last_coords': (event.x, event.y),
            'left_edge': (0 <= event.x < self.frame_thickness),
            'right_edge': (window_width - self.frame_thickness <= event.x < window_width),
            'top_edge': (0 <= event.y < self.frame_thickness),
            'bottom_edge': (window_height - self.frame_thickness <= event.y < window_height),
        }            

    def mousemove(self, event):
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
            # normalize sizes
            new_width = max(new_width, self.min_width)
            new_height = max(new_height, self.min_height)
            # save new settings in item, not card yet
            self.resize_state['last_coords'] = (event.x, event.y)
            self.canvas.coords(self.itemid, new_x, new_y)
            self.canvas.itemconfig(self.itemid, width=new_width, height=new_height)

    def mouseup(self, event):
        if self.resize_state:
            self.resize_state = None
            if self.save_callback:
                self.save_callback()

    def delete_item(self, event):
        self.canvas.delete(self.itemid)

