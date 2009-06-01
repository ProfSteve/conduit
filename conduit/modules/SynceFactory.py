import conduit
import conduit.utils as Utils
import conduit.dataproviders.DataProvider as DataProvider
import conduit.dataproviders.DataProviderCategory as DataProviderCategory
import conduit.dataproviders.HalFactory as HalFactory
import conduit.datatypes.Note as Note
import conduit.datatypes.Contact as Contact
import conduit.Exceptions as Exceptions

import xml.dom.minidom
import vobject

import logging
log = logging.getLogger("modules.SynCEFactory")

import os.path
import traceback
import dbus
import threading
import gobject
import array

from gettext import gettext as _

MODULES = {
    "SynceFactory" :        { "type": "dataprovider-factory" },
}

class SynceFactory(HalFactory.HalFactory):

    SUPPORTED_PARTNERSHIPS = ("Calendar", "Contacts", "Tasks")

    def __init__(self, **kwargs):
        HalFactory.HalFactory.__init__(self, **kwargs)
        self._found = False
        self._item_types = {}
        self._partnerships = []
        
    def _get_item_types_rx(self, item_types):
        self._item_types = item_types

    def _get_partnerships_rx(self, partnerships):  
        self._partnerships = partnerships
        
    def _create_partnership_rx(self, guid):
        print args
        
    def _create_partnership_error(self, e):
    	log.warn("Failed to create partnership: %s" % e._dbus_error_name)
        
    def _on_create_partnership_clicked(self, sender, mod):
        #create partnerships for Contact, Calendar, Tasks
        ids = [id for id, name in self._item_types.items() if str(name) in self.SUPPORTED_PARTNERSHIPS]
        self.engine.CreatePartnership(
                            "Conduit",      #partnership name
                            ids,            #ids of those items to sync
            	            reply_handler=self._create_partnership_rx,
            	            error_handler=self._create_partnership_error
            	            )
        
    def _found_device(self):
        self._found = True
        
        #call async so we dont block at startup
        #reply_handler will be called with the method's return values as arguments; or
        #the error_handler
        self.engine = dbus.Interface(
                    dbus.SessionBus().get_object('org.synce.SyncEngine', '/org/synce/SyncEngine'),
                    'org.synce.SyncEngine'
                    )
    	self.engine.GetItemTypes(
    	            reply_handler=self._get_item_types_rx,
    	            error_handler=lambda *args: None
    	            )
        self.engine.GetPartnerships(
    	            reply_handler=self._get_partnerships_rx,
    	            error_handler=lambda *args: None
    	            )

    def probe(self):
        """
        Enumerate HAL for any entries of interest
        """        
        for device in self.hal.FindDeviceStringMatch("sync.plugin", "synce"):
            self._maybe_new(str(device))

    def is_interesting(self, device, props):
        if props.has_key("sync.plugin") and props["sync.plugin"]=="synce":
            self._found_device()        
            return True
        return False

    def get_category(self, udi, **kwargs):
        return DataProviderCategory.DataProviderCategory(
                    "Windows Mobile",
                    "windows",
                    udi)

    def get_dataproviders(self, udi, **kwargs):
        from SynceModule import SynceContactsTwoWay, SynceCalendarTwoWay, SynceTasksTwoWay
        return [SynceContactsTwoWay, SynceCalendarTwoWay, SynceTasksTwoWay]
        
    def setup_configuration_widget(self):
    
        if self._found:
            import gtk
            import socket
            
            vbox = gtk.VBox(False,5)
            mod = gtk.ListStore(
                            gobject.TYPE_PYOBJECT,      #parnership id
                            gobject.TYPE_PYOBJECT,      #parnership guid
                            str,str,str)                #device name, pc name, items
            treeview = gtk.TreeView(mod)
            
            #Three colums: device name, pc name, items
            index = 2
            for name in ("Device", "Computer", "Items to Synchronize"):
                col = gtk.TreeViewColumn(
                                    name, 
                                    gtk.CellRendererText(),
                                    text=index)
                treeview.append_column(col)
                index = index + 1
            vbox.pack_start(treeview,True,True)

            btn = gtk.Button(None,gtk.STOCK_ADD)
            btn.set_label("Create Partnership")
            btn.connect("clicked", self._on_create_partnership_clicked, mod)
            vbox.pack_start(btn, False, False)

            #add the existing partnerships
            for id,guid,name,hostname,devicename,storetype,items in self._partnerships:
                mod.append((
                        id,
                        guid,
                        str(devicename),
                        str(hostname),
                        ", ".join([str(self._item_types[item]) for item in items]))
                        )
                #disable partnership if one exists
                if str(hostname) == socket.gethostname():
                    btn.set_sensitive(False)
                    
            return vbox
        return None

    def save_configuration(self, ok):
        pass
