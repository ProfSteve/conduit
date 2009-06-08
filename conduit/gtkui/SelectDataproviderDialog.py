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

    def __init__(self, filter_mime = None):
        self.window = gtk.Assistant()
        
        conduit.GLOBALS.moduleManager.get_modules_by_type("source","sink","twoway")

        self.dataproviders_list

