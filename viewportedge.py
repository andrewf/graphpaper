'''
Contains class for managing viewport manifestation of edges.
'''

class ViewportEdge(object):
    '''
    Class for displaying edges

    Handles modifying/redrawing of the lines between cards,
    and for changing their endpoints.

    Members:
    * edge: model.Edge object
    * viewport: GPViewport self belongs to
    * canvas: shortcut to viewport canvas
    * itemid: int handle to item on canvas
    * orig: ViewportCard or None
    * dest: ViewportCard or None
    * orig_callback: int callback handle for geometry callback on orig card
    * dest_callback: as above, s/orig/dest/g
    '''
    def __init__(self, viewport, gpfile, edge, orig, dest):
        '''
        Arguments:
        * viewport: GPViewport this edge lives in
        * gpfile: GPFile, needed for committing
        * edge: model.Edge that we will be managing.
        '''
        # store all the arguments
        self.edge = edge
        self.viewport = viewport
        self.canvas = viewport.canvas
        self.gpfile = gpfile
        # draw self
        self.itemid = self.canvas.create_line(
            #0, 0, 100, 0, 100, 100, 200, 100,
            # have to unpack self.get_coords as first args, not last
            *(self.get_coords()),
            arrow='last',
            smooth='raw',
            width=4,
            fill='blue'
        )
        # set up state
        self.orig_callback = self.dest_callback = None
        self.orig = orig
        self.dest = dest

    def refresh(self):
        self.canvas.coords(self.itemid, *self.get_coords())
        #self.itemid.coords(*(self.get_coords()))

    def get_coords(self):
        '''
        Return a list of points for the edge to pass through.

        Calculates from the position of self.edge.orig/dest,
        and at some point from the mouse position I guess.
        Straight line between the centers of orig and dest.
        '''
        # watch out for loss of sync between viewport cards and model card
        # also, this will have to be rewritten at some point so any
        # endpoint can be mouse-driven rather than card-driven
        orig = self.edge.orig
        dest = self.edge.dest
        start_point = (orig.x + orig.w/2, orig.y + orig.h/2)
        end_point = (dest.x + orig.w/2, dest.y + orig.h/2)
        print 'edge points: ', start_point, end_point
        print '  orig: ', orig.text[:30]
        print '  dest: ', dest.text[:30]
        return (start_point[0], start_point[1], end_point[0], end_point[1])

    def geometry_callback(self, *args):
        "For passing to ViewportCard slots"
        self.refresh()

    def get_orig(self):
        return self._orig
    def set_orig(self, orig):
        if self.orig_callback:
            self.orig.remove_signal(self.orig_callback)
        self._orig = orig
        if orig:
            self.orig_callback = orig.add_signal(self.geometry_callback)
            self.edge.orig = orig.card
    orig = property(get_orig, set_orig)

    def get_dest(self):
        return self._dest
    def set_dest(self, dest):
        if self.dest_callback:
            self.dest.remove_signal(self.dest_callback)
        self._dest = dest
        if dest:
            self.dest_callback = dest.add_signal(self.geometry_callback)
            self.edge.dest = dest.card
    dest = property(get_dest, set_dest)

