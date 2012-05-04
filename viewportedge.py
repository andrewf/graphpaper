'''
Contains class for managing viewport manifestation of edges.
'''

from math import sqrt
import model

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
    * nodes: [ViewportCard or None], list of orig and dest node.
    * geom_callbacks: int callback handles for geometry callbacks
    * deletion_callbacks: callback handles for when card is deleted
    * coords = [[int]], list of endpoints (post-adjustment)
    * orig: ViewportCard or None
    * dest: ViewportCard or None
    * dragging_end = when dragging, an index into nodes/coords, else None
    * make_new_card = when dragging, whether we can make a new card if the
        end gets dragged to nowhere.
    * highlighted_card = when dragging, the card we're highlighting (property)
    '''
    def __init__(self, viewport, gpfile, edge, orig, dest, make_new_card=False):
        '''
        Either load an edge from the datastore, or start creating
        a new one. If edge is None, we're creating a new edge and
        one of orig or dest should be None. Otherwise, edge should be a
        model.Edge and orig and dest should both be ViewportCards
        corresponding to the cards in edge.
        
        Arguments:
        * viewport: GPViewport this edge lives in
        * gpfile: GPFile, needed for committing
        * edge: model.Edge that we will be managing, or None if creating a new edge.
        * orig: ViewportCard or None, if dragging a new edge
        * dest: as above, but more likely.
        * make_new_card: bool, optional. If this is a new edge, and we get
            dropped off of a card, make a new one.
        '''
        # store all the arguments
        self.edge = edge
        self.viewport = viewport
        self.canvas = viewport.canvas
        self.gpfile = gpfile
        # callback attrs needed before setting nodes
        self.geom_callbacks = [None, None]
        self.deletion_callbacks = [None, None]
        self.nodes = [None, None]
        # set nodes
        self.orig = orig
        self.dest = dest
        # we basically need to decide whether to start off dragging
        if edge:
            # member vars are all good, theoretically.
            # just need to self self.coords
            self.reset_coords()
            # not dragging.
            self.dragging_end = None # or 0 or 1
        else:
            # we start off dragging
            if self.orig:
                self.dragging_end = 1
                nondrag = self.orig
            elif self.dest:
                self.dragging_end = 0
                nondrag = self.dest
            # use fake initial pos
            initpos = nondrag.canvas_coords()
            self.coords = [initpos, (initpos[0] + 10, initpos[1] + 10)]
        self._highlighted_card = None
        self.make_new_card = make_new_card
        # draw self
        self.itemid = self.canvas.create_line(
            # have to unpack self.get_coords as first args, not last
            *(self.get_coords()),
            arrow='last',
            smooth='raw',
            width=7,
            fill='blue',
            activefill='#6060ff'
        )
        self.canvas.addtag_withtag('edge_tag', self.itemid)
        self.canvas.tag_bind(self.itemid, "<Button-1>", self.click)
        self.canvas.tag_bind(self.itemid, "<B1-Motion>", self.mousemove)
        self.canvas.tag_bind(self.itemid, "<ButtonRelease-1>", self.mouseup)

    def refresh(self):
        self.canvas.coords(self.itemid, *self.get_coords())

    def reset_coords(self):
        '''
        Set self.coords based on current cards. Only call when orig and
        dest are valid. Straight line between the centers of orig and dest.
        '''
        # watch out for loss of sync between viewport cards and model card
        # also, this will have to be rewritten at some point so any
        # endpoint can be mouse-driven rather than card-driven
        orig = self.edge.orig
        dest = self.edge.dest
        start_point = (orig.x + orig.w/2, orig.y + orig.h/2)
        end_point = (dest.x + dest.w/2, dest.y + dest.h/2)
        #adjust both points to be on edges of cards
        start_point = adjust_point(start_point, card_box(orig), end_point)
        end_point = adjust_point(end_point, card_box(dest), start_point)
        self.coords = [start_point, end_point]

    def get_coords(self):
        "return self.coords in a flattened list"
        return self.coords[0][0], self.coords[0][1], self.coords[1][0], self.coords[1][1]

    def set_node(self, index, newcard):
        # clear old callbacks, if needed
        oldcard = self.nodes[index]
        if self.geom_callbacks[index] is not None:
            oldcard.remove_geom_signal(self.geom_callbacks[index])
            oldcard.remove_deletion_signal(self.deletion_callbacks[index])
        # register with new card, if needed
        self.nodes[index] = newcard
        if newcard is not None:
            self.geom_callbacks[index] = newcard.add_geom_signal(self.geometry_callback)
            self.deletion_callbacks[index] = newcard.add_deletion_signal(self.delete)
            if self.edge:
                setattr(self.edge, ['orig', 'dest'][index], newcard.card)

    def geometry_callback(self, card, x, y, w, h):
        "For passing to ViewportCard slots"
        # we know here that both ends are card-based, no mouse and no loose ends
        box = (x, y, w, h)
        point = (x + w/2, y + h/2) # point in middle of whatever card moved
        # we have to adjust both points, the moved point by the passed box and
        # the other point by the stored box
        if card is self.orig:
            self.coords[0] = adjust_point(point, box, self.coords[1])
            otherbox = card_box(self.dest.card)
            self.coords[1] = adjust_point(box_center(otherbox), otherbox, point)
        elif card is self.dest:
            self.coords[1] = adjust_point(point, box, self.coords[0])
            otherbox = card_box(self.orig.card)
            self.coords[0] = adjust_point(box_center(otherbox), otherbox, point)
        else:
            raise RuntimeError('Card must be either orig or dest.')
        # adjust both ends
        self.refresh()

    def delete(self):
        '''
        Called when any card connected is deleted,
        or when an end is disconnected
        '''
        # delete canvas item, for now
        # TODO: get this object actually deleted. as it is,
        # it just sits in viewport.edges
        self.canvas.delete(self.itemid)
        # strictly speaking, this is unnecessary, but a good idea
        # don't delete, card will do that when these callbacks finish
        # this may be called before we're settled, so make sure edge exists
        if self.edge:
            self.edge.delete()
            self.gpfile.commit()
        # clear any callbacks
        self.orig = None
        self.dest = None

    def click(self, event):
        '''
        Determine which end of the edge was clicked on
        '''
        # event coords are window coords, not canvas coords
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        start_x, start_y = self.coords[0]
        end_x, end_y = self.coords[1]
        to_orig = sqrt((start_x - x)**2 + (start_y - y)**2)
        to_dest = sqrt((end_x - x)**2 + (end_y - y)**2)
        #print locals()
        if to_orig < to_dest:
            self.dragging_end = 0
        elif to_dest < to_orig:
            self.dragging_end = 1
        else:
            print 'seriously?'

    def mousemove(self, event):
        '''
        Update dragging_end based on mousemove. Notify Viewport.
        Later, highlight card.
        '''
#        print 'mousemove', event.x, event.y, self.dragging_end
        if self.dragging_end is not None:
            self.coords[self.dragging_end] = (
                self.canvas.canvasx(event.x),
                self.canvas.canvasy(event.y)
            )
            # adjust other endpoint
            non_dragging_end = int(not self.dragging_end)
            non_drag_box = card_box(self.nodes[non_dragging_end].card)
            self.coords[non_dragging_end] = adjust_point(
                box_center(non_drag_box),
                non_drag_box,
                self.coords[self.dragging_end]
            )
            self.refresh()
            # highlight the card the mouse is over, if it's not
            # the other end of this edge
            hover_card = self.viewport.card_collision(self.coords[self.dragging_end])
            if hover_card is not self.nodes[non_dragging_end]:
                self.highlighted_card = hover_card

    def mouseup(self, event):
        '''
        Choose card to land on. reset coords
        '''
#        print 'mouseup'
        if self.dragging_end is not None:
            # set new end
            non_dragging_end = int(not self.dragging_end)
            card = self.viewport.card_collision(self.coords[self.dragging_end])
            if card is not None:
                # don't allow both nodes to be the same
                if card is not self.nodes[non_dragging_end]:
                    self.set_node(self.dragging_end, card)
                    # create edge if needed (if this is first time edge is finished)
                    if self.edge is None:
                        self.edge = self.gpfile.graph.new_edge(
                            orig = self.orig.card,
                            dest = self.dest.card
                        )
                else:
                    # landed on starting node
                    # if creating a new edge, need to cancel
                    if self.edge is None:
                        self.delete()
                        self.highlighted_card = None
                        return
            else:
                print 'dropped nowhere', self.make_new_card
                # we got dropped nowhere
                if self.make_new_card:
                    print 'making new card'
                    new_geom = new_card_geometry(
                        (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)),
                        self.coords[non_dragging_end],
                        int(self.gpfile.config.get('default_card_w', 200)),
                        int(self.gpfile.config.get('default_card_h', 150))
                    )
                    new_card = self.viewport.new_card(*new_geom)
                    self.set_node(
                        self.dragging_end,
                        new_card
                    )
                    if self.edge is None:
                        self.edge = self.gpfile.graph.new_edge(
                            orig = self.orig.card,
                            dest = self.dest.card
                        )
                    self.gpfile.commit()
                else:
                    print 'canceling'
                    # else, cancel
                    self.delete() # does right thing when not settled.
                    self.highlighted_card = None
                    return
            self.make_new_card = False
            # update graphics
            self.reset_coords()
            self.refresh()
            self.dragging_end = None
            self.highlighted_card = None
            self.gpfile.commit()

    def get_highlighted_card(self):
        return self._highlighted_card
    def set_highlighted_card(self, new):
        if new is not self._highlighted_card:
            if self._highlighted_card is not None:
                self._highlighted_card.unhighlight()
            if new is not None:
                new.highlight()
            self._highlighted_card = new
        # else, no-op
    highlighted_card = property(get_highlighted_card, set_highlighted_card)

    def get_orig(self):
        return self.nodes[0]
    def set_orig(self, orig):
        self.set_node(0, orig)
    orig = property(get_orig, set_orig)

    def get_dest(self):
        return self.nodes[1]
    def set_dest(self, dest):
        self.set_node(1, dest)
    dest = property(get_dest, set_dest)

    @property
    def non_dragging_end(self):
        if self.dragging_end is not None:
            # assume correct value of 0 or 1
            return int(not self.dragging_end)
        return None

def adjust_point(p1, box, p2):
    '''
    Moves p1 along the line p1<->p2 to be on an edge of box

    Args:
    * p1: (x:int, y:int)
    * box: (x:int, y:int, w:int, h:int)
    * p2: (x2:int, y2:int)

    Returns:
    (x:int, y:int), new version of p1
    '''
    # fn for line <--p1--p2-->
    rise = p2[1] - p1[1]
    run  = p2[0] - p1[0]
    # remember, y - y1 = m(x - x1), m = rise/run
    y = lambda x: int( rise*(x - p1[0])/run  + p1[1] )
    x = lambda y: int(  run*(y - p1[1])/rise + p1[0] )
    # coords of side wall and top/bot of box facing p2
    relevant_x = box[0] if run < 0 else box[0] + box[2]
    relevant_y = box[1] if rise < 0 else box[1] + box[3]
    # bail early if edge is vertical or horizontal
    if run == 0:
        return p1[0], relevant_y
    if rise == 0:
        return relevant_x, p1[1]
    # see if the x-coord of the relevant side wall of the wall gives
    # us a valid y-value. if so, return it
    wall_y = y(relevant_x)
    if box[1] <= wall_y <= box[1] + box[3]:
        return (relevant_x, wall_y)
    # if we get here, we know the intersection is on the top or bottom
    return x(relevant_y), relevant_y

def new_card_geometry(mouse, other_end, new_width, new_height):
    '''
    Figure out how to place a new box so it fits nicely with
    the old box and current edge position

    Arguments:
    * mouse: (x, y), mouse pos
    * other_end: (x, y), other end of edge
    * new_width, new_height, size that new card should be

    Returns (x, y, w, h) of new card.
    '''
    print 'geom'
    edge_rise = mouse[1] - other_end[1]
    edge_run = (mouse[0] - other_end[0]) or .0001 # cheater's way out of zero-div
    edge_slope = float(edge_rise) / edge_run
    new_box_aspect = float(new_height) / new_width
    # determine if arrow comes in on side or top/bot of new card
    if abs(edge_slope) < abs(new_box_aspect):
        # on side
        if edge_run < 0:
            new_x = mouse[0] - new_width
        else:
            new_x = mouse[0]
        new_y = mouse[1] - new_height / 2
    else:
        if edge_rise < 0:
            new_y = mouse[1] - new_height
        else:
            new_y = mouse[1]
        new_x = mouse[0] - new_width / 2
    print '  ', locals()
    return (new_x, new_y, new_width, new_height)

def card_box(card):
    '''
    return bounding box of card as (x, y, w, h)
    card is a model.Card
    '''
    return card.x, card.y, card.w, card.h

def box_center(box):
    '''
    center point of box in tuple format, like above fn
    '''
    return (box[0] + box[2]/2, box[1] + box[3]/2)


