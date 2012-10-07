#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from scrolled_window import ScrolledWindow
from theme import ui_theme
from window import Window
from draw import draw_text, draw_vlinear
from utils import get_content_size
from new_treeview import TreeView, TreeItem
from constant import DEFAULT_FONT_SIZE
import gobject
import gtk

poplist_grab_window = gtk.Window(gtk.WINDOW_POPUP)
poplist_grab_window.move(0, 0)
poplist_grab_window.set_default_size(0, 0)
poplist_grab_window.show()
root_poplists = []
poplist_grab_window_press_flag = False

def poplist_grab_window_focus_in():
    '''
    Handle `focus-in` signal of poplist_grab_window.
    '''
    poplist_grab_window.grab_add()
    gtk.gdk.pointer_grab(
        poplist_grab_window.window, 
        True,
        gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.ENTER_NOTIFY_MASK | gtk.gdk.LEAVE_NOTIFY_MASK,
        None, None, gtk.gdk.CURRENT_TIME)
    
def poplist_grab_window_focus_out():
    '''
    Handle `focus-out` signal of poplist_grab_window.
    '''
    global root_poplists
    global poplist_grab_window_press_flag
    
    for root_poplist in root_poplists:
        root_poplist.hide()
    
    root_poplists = []    
    
    gtk.gdk.pointer_ungrab(gtk.gdk.CURRENT_TIME)
    poplist_grab_window.grab_remove()
    
    poplist_grab_window_press_flag = False
    
def is_press_on_poplist_grab_window(window):
    '''
    Whether press on poplist of poplist_grab_window.
    
    @param window: gtk.Window or gtk.gdk.Window
    '''
    for toplevel in gtk.window_list_toplevels():
        if isinstance(window, gtk.Window):
            if window == toplevel:
                return True
        elif isinstance(window, gtk.gdk.Window):
            if window == toplevel.window:
                return True
            
    return False        

def poplist_grab_window_button_press(widget, event):
    '''
    Handle `button-press-event` signal of poplist_grab_window.

    @param widget: Poplist widget.
    @param event: Button press event.
    '''
    global poplist_active_item
    global poplist_grab_window_press_flag

    poplist_grab_window_press_flag = True
    
    if event and event.window:
        event_widget = event.window.get_user_data()
        if is_press_on_poplist_grab_window(event.window):
            poplist_grab_window_focus_out()
        elif isinstance(event_widget, ScrolledWindow) and hasattr(event_widget, "belong_to_polist"):
            event_widget.event(event)
        elif isinstance(event_widget, Poplist):
            event_widget.event(event)
        else:
            event_widget.event(event)
            poplist_grab_window_focus_out()
            
def poplist_grab_window_enter_notify(widget, event):
    '''
    Handle `enter-notify` signal of poplist_grab_window.

    @param widget: Poplist widget.
    @param event: Enter notify event.
    '''
    if event and event.window:
        event_widget = event.window.get_user_data()
        if isinstance(event_widget, ScrolledWindow) and hasattr(event_widget, "belong_to_polist"):
            event_widget.event(event)

def poplist_grab_window_leave_notify(widget, event):
    '''
    Handle `leave-notify` signal of poplist_grab_window.

    @param widget: Poplist widget.
    @param event: Leave notify event.
    '''
    if event and event.window:
        event_widget = event.window.get_user_data()
        if isinstance(event_widget, ScrolledWindow) and hasattr(event_widget, "belong_to_polist"):
            event_widget.event(event)
            
def poplist_grab_window_scroll_event(widget, event):
    '''
    Handle `scroll` signal of poplist_grab_window.

    @param widget: Poplist widget.
    @param event: Scroll event.
    '''
    global root_poplists
    
    if event and event.window:
        for poplist in root_poplists:
            poplist.treeview.scrolled_window.event(event)
            
def poplist_grab_window_key_press(widget, event):
    '''
    Handle `key-press-event` signal of poplist_grab_window.

    @param widget: Poplist widget.
    @param event: Key press event.
    '''
    global root_poplists
    
    if event and event.window:
        for poplist in root_poplists:
            poplist.event(event)

def poplist_grab_window_key_release(widget, event):
    '''
    Handle `key-release-event` signal of poplist_grab_window.

    @param widget: Poplist widget.
    @param event: Key release event.
    '''
    global root_poplists
    
    if event and event.window:
        for poplist in root_poplists:
            poplist.event(event)

def poplist_grab_window_button_release(widget, event):
    '''
    Handle `button-release-event` signal of poplist_grab_window.

    @param widget: Poplist widget.
    @param event: Button release event.
    '''
    global root_poplists
    global poplist_grab_window_press_flag

    poplist_grab_window_press_flag = False
    
    if event and event.window:
        event_widget = event.window.get_user_data()
        if isinstance(event_widget, ScrolledWindow) and hasattr(event_widget, "belong_to_polist"):        
            event_widget.event(event)
        else:
            # Make scrolledbar smaller if release out of scrolled_window area.
            for poplist in root_poplists:
                poplist.treeview.scrolled_window.make_bar_smaller(gtk.ORIENTATION_HORIZONTAL)
                poplist.treeview.scrolled_window.make_bar_smaller(gtk.ORIENTATION_VERTICAL)
    
def poplist_grab_window_motion_notify(widget, event):
    '''
    Handle `motion-notify` signal of poplist_grab_window.

    @param widget: Poplist widget.
    @param event: Motion notify signal.
    '''
    
    global poplist_active_item
    global poplist_grab_window_press_flag
    
    if event and event.window:
        event_widget = event.window.get_user_data()
        if isinstance(event_widget, ScrolledWindow) and hasattr(event_widget, "belong_to_polist"):        
            event_widget.event(event)
        else:
            if poplist_grab_window_press_flag:
                for poplist in root_poplists:
                    motion_notify_event = gtk.gdk.Event(gtk.gdk.MOTION_NOTIFY)
                    motion_notify_event.window = poplist.treeview.scrolled_window.vwindow
                    motion_notify_event.send_event = True
                    motion_notify_event.time = event.time
                    motion_notify_event.x = event.x
                    motion_notify_event.y = event.y
                    motion_notify_event.x_root = event.x_root
                    motion_notify_event.y_root = event.y_root
                    motion_notify_event.state = event.state
                        
                    poplist.treeview.scrolled_window.event(motion_notify_event)
            else:
                if isinstance(event_widget.get_toplevel(), Poplist):
                    event_widget.event(event)
                
poplist_grab_window.connect("button-press-event", poplist_grab_window_button_press)
poplist_grab_window.connect("button-release-event", poplist_grab_window_button_release)
poplist_grab_window.connect("motion-notify-event", poplist_grab_window_motion_notify)
poplist_grab_window.connect("enter-notify-event", poplist_grab_window_enter_notify)
poplist_grab_window.connect("leave-notify-event", poplist_grab_window_leave_notify)
poplist_grab_window.connect("scroll-event", poplist_grab_window_scroll_event)
poplist_grab_window.connect("key-press-event", poplist_grab_window_key_press)
poplist_grab_window.connect("key-release-event", poplist_grab_window_key_release)

class Poplist(Window):
    '''
    class docs
    '''
	
    def __init__(self,
                 items,
                 max_height=None,
                 max_width=None,
                 min_width=130,
                 ):
        '''
        init docs
        '''
        # Init.
        Window.__init__(self)
        self.items = items
        self.max_height = max_height
        self.max_width = max_width
        self.min_width = min_width
        self.treeview = TreeView(self.items,
                                 enable_highlight=False,
                                 enable_multiple_select=False,
                                 enable_drag_drop=False)
        self.treeview.scrolled_window.belong_to_polist = True # tag scrolled_window with poplist type
        
        # Connect widgets.
        self.window_frame.pack_start(self.treeview, True, False)
        
        self.connect("realize", self.realize_poplist)
        self.connect_after("show", self.init_poplist)
        
    def realize_poplist(self, widget):
        treeview_width = self.min_width
        for item in self.treeview.visible_items:
            if hasattr(item, "get_width"):
                treeview_width = max(treeview_width, item.get_width())
                
        treeview_height = int(self.treeview.scrolled_window.get_vadjustment().get_upper())
                
        if self.max_width != None and self.max_height != None: 
            adjust_width = self.max_width
            adjust_height = self.max_height
        elif self.max_height != None:
            adjust_width = treeview_width
            adjust_height = self.max_height
        elif self.max_width != None:
            adjust_width = self.max_width
            adjust_height = treeview_height
        else:
            adjust_width = treeview_width
            adjust_height = treeview_height
            
        self.treeview.set_size_request(adjust_width, adjust_height)
        
        (shadow_padding_x, shadow_padding_y) = self.get_shadow_size()
        window_width = adjust_width + shadow_padding_x * 2
        window_height = adjust_height + shadow_padding_y * 2
        self.set_default_size(window_width, window_height)
        self.set_geometry_hints(
            None,
            window_width,       # minimum width
            window_height,       # minimum height
            window_width,
            window_height,
            -1, -1, -1, -1, -1, -1
            )
        
    def init_poplist(self, widget):
        '''
        Callback after `show` signal.
        
        @param widget: Poplist widget.
        '''
        global root_poplists
        poplist_grab_window_focus_out()
        
        if not gtk.gdk.pointer_is_grabbed():
            poplist_grab_window_focus_in()
        
        if not self in root_poplists:
            root_poplists.append(self)
                            
gobject.type_register(Poplist)        

class TextItem(TreeItem):
    '''
    class docs
    '''
	
    def __init__(self, 
                 text, 
                 text_size = DEFAULT_FONT_SIZE,
                 padding_x = 10,
                 padding_y = 5):
        '''
        init docs
        '''
        # Init.
        TreeItem.__init__(self)
        self.text = text
        self.text_size = text_size
        self.padding_x = padding_x
        self.padding_y = padding_y
        (self.text_width, self.text_height) = get_content_size(self.text)
        
    def render_text(self, cr, rect):
        font_color = ui_theme.get_color("menu_font").get_color()
        if self.is_hover:
            # Draw background.
            draw_vlinear(cr, rect.x, rect.y, rect.width, rect.height, 
                         ui_theme.get_shadow_color("menu_item_select").get_color_info())
        
            # Set font color.
            font_color = ui_theme.get_color("menu_select_font").get_color()
            
        draw_text(cr, 
                  self.text,
                  rect.x + self.padding_x, 
                  rect.y + self.padding_y, 
                  rect.width - self.padding_x * 2, 
                  rect.height - self.padding_y * 2,
                  text_color=font_color)
        
    def get_width(self):
        return self.text_width + self.padding_x * 2
        
    def get_height(self):
        return self.text_size + self.padding_y * 2
    
    def get_column_widths(self):
        return [-1]
    
    def get_column_renders(self):
        return [self.render_text]

    def unhover(self):
        self.is_hover = False

        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def hover(self):
        self.is_hover = True
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
gobject.type_register(TextItem)
