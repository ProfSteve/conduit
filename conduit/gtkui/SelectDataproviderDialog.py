"""
Copyright: Alexandre Rosenfeld, 2009
License: GPLv2
"""
import thread
import gobject
import gtk, gtk.glade
import os.path
import gettext
import threading
from gettext import gettext as _
import logging
log = logging.getLogger("gtkui.UI")

import conduit
import conduit.Web as Web
import conduit.Conduit as Conduit
import conduit.gtkui.Canvas as Canvas
import conduit.gtkui.MsgArea as MsgArea
import conduit.gtkui.Tree as Tree
import conduit.gtkui.ConflictResolver as ConflictResolver
import conduit.gtkui.Database as Database

class SelectDataproviderDialog(object):

    def __init__(self, filter_mime_in = None, filter_mime_out = None):
        #self.window = gtk.Assistant()
        self.window = gtk.Dialog("My dialog",
                     None,
                     gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                     (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                      gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        self.dp_model = gtk.ListStore(gtk.gdk.Pixbuf, str)
        
        dpw_list = conduit.GLOBALS.moduleManager.get_modules_by_type("source","sink","twoway")
        module_wrapper_list = [m for m in dpw_list if m.enabled]
        
        #Add them to the module
        for mod in module_wrapper_list:
            #if (not filter_mime_in or mod.in_type == filter_mime_in) and
            #   (not filter_mime_out or mod.out_type == filter_mime_out):
            self.dp_model.append((mod.get_descriptive_icon(), mod.name,))
        
        self.combobox = gtk.ComboBox(self.dp_model)

        pixbuf_render = gtk.CellRendererPixbuf()
        self.combobox.pack_start(pixbuf_render, False)
        self.combobox.set_attributes(pixbuf_render, pixbuf = 0)
        
        txt_render = gtk.CellRendererText()
        self.combobox.pack_start(txt_render)
        self.combobox.set_attributes(txt_render, text = 1)
        #self.combobox.insert_column_with_attributes(0, "Dps", gtk.CellRendererText(), text = 0)
        
        self.window.get_content_area().pack_start(self.combobox)
        
    def run(self):
        self.window.show_all()
        self.window.run()
        self.window.hide()
        return ""
            
