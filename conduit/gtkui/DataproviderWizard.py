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

class DataproviderWizard(gobject.GObject):
    def __init__(self, main_window, syncset, module_manager, kinds=("source", "twoway"), cond=None):
        gobject.GObject.__init__(self)
        self.main_window = main_window
        self.syncset = syncset
        self.module_manager = module_manager
        self.kinds = kinds
        self.conduit = cond
        
        self._make_add_conduit_dialog()
    
    def _assistant_apply(self, assistant):
        self.assistant.hide()
        mod = self.module_manager.get_module_wrapper_with_instance(self.selected_dataprovider.get_dnd_key())
        if not self.conduit:
            cond = Conduit.Conduit(self.syncset.syncManager)
            cond.add_dataprovider(mod, True)
            self.syncset.add_conduit(cond)
        else:
            self.conduit.add_dataprovider(mod, False)
        
    def _assistant_close(self, assistant):
        self.assistant.hide()
        
    def _dataprovider_tree_selection(self, tree):
        model, iter_ = tree.get_selection().get_selected()
        obj = model.get_value(iter_, 0)
        self.assistant.set_page_complete(self.dataproviders_page, obj is not None)
        if obj:
            self.selected_dataprovider = obj
    
    def _make_add_conduit_dialog(self):
        #dialog = gtk.Dialog("Add Conduit",
        #                    self.mainWindow,
        #                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        #                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
        #                     gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.assistant = gtk.Assistant()
        self.assistant.set_default_size(600, 600)
        self.assistant.connect("apply", self._assistant_apply)
        self.assistant.connect("close", self._assistant_close)
        self.assistant.connect("cancel", self._assistant_close)

        model = gtk.TreeStore(object, str, gtk.gdk.Pixbuf)
        tree = gtk.TreeView()
        tree.set_headers_visible(False)
        tree.set_show_expanders(False)
        tree.set_level_indentation(32)
        tree.set_model(model)
        
        sw = gtk.ScrolledWindow()
        sw.add(tree)
        self.dataproviders_page = sw
        
        pixbufRenderer = gtk.CellRendererPixbuf()
        textRenderer = gtk.CellRendererText()
        tvcolumn0 = gtk.TreeViewColumn("name")
        tvcolumn0.pack_start(pixbufRenderer, False)
        tvcolumn0.add_attribute(pixbufRenderer, 'pixbuf', 2)
        tvcolumn0.pack_start(textRenderer, True)
        tvcolumn0.add_attribute(textRenderer, 'markup', 1)
        tree.append_column(tvcolumn0)        
        #tree.insert_column_with_attributes(-1, "Name", gtk.CellRendererText(), text=1)
        categories = {}
        
        for mod in self.module_manager.get_modules_by_type(*self.kinds):
            #print mod
            if not mod.enabled:
                continue
            if mod.category.key in categories:
                parent = categories[mod.category.key]
            else:
                cat_icon = gtk.icon_theme_get_default().load_icon(mod.category.icon, 16, 0)
                parent = model.append(None, (None, mod.category.name, cat_icon))
                categories[mod.category.key] = parent
            model.append(parent, (mod, mod.name, mod.get_descriptive_icon()))
        
        #dialog.vbox.pack_start(sw)
        #dialog.vbox.show_all()
        tree.connect("cursor-changed", self._dataprovider_tree_selection)
        tree.expand_all()
        sw.show_all()
        tree_page = self.assistant.append_page(sw)
        self.assistant.set_page_type(sw, gtk.ASSISTANT_PAGE_CONFIRM)
        self.assistant.set_page_title(sw, "Choose a dataprovider")
        #return dialog.run()
        self.assistant.set_modal(True)
        self.assistant.set_transient_for(self.main_window)
        
    def show(self):
        self.assistant.show()
