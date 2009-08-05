"""
Represents a group of conduits

Copyright: John Stowers, 2007
License: GPLv2
"""
import traceback
import os
import xml.dom.minidom
import gobject
import logging
log = logging.getLogger("SyncSet")

import conduit
import conduit.Conduit as Conduit
import conduit.Settings as Settings
import conduit.SyncSetGConf as SyncSetGConf


class SyncSet(gobject.GObject):
    """
    Represents a group of conduits
    """
    __gsignals__ = {
        #Fired when a new instantiatable DP becomes available. It is described via 
        #a wrapper because we do not actually instantiate it till later - to save memory
        "conduit-added" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [
            gobject.TYPE_PYOBJECT]),    # The ConduitModel that was added
        "conduit-removed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [
            gobject.TYPE_PYOBJECT]),    # The ConduitModel that was removed
        }

    def __init__(self, name, moduleManager, syncManager, xmlSettingFilePath="settings.xml"):
        gobject.GObject.__init__(self)

        self.name = name
        self.moduleManager = moduleManager
        self.syncManager = syncManager
        self.xmlSettingFilePath = xmlSettingFilePath
        self.syncsetGConf = SyncSetGConf.SyncSetGConf(self)
        self.conduits = []

        self.moduleManager.connect("dataprovider-available", self.on_dataprovider_available_unavailable)
        self.moduleManager.connect("dataprovider-unavailable", self.on_dataprovider_available_unavailable)

        # FIXME: temporary hack - need to let factories know about this factory :-\!
        self.moduleManager.emit("syncset-added", self)
        
    def _unitialize_dataproviders(self, cond):
        for dp in cond.get_all_dataproviders():
            if dp.module:
                try:
                    dp.module.uninitialize()
                except Exception:
                    log.warn("Could not uninitialize %s" % dp, exc_info=True)
                
    def _restore_dataprovider(self, cond, wrapperKey, dpName="", dpxml="", xml_version="2", trySourceFirst=True):
        """
        Adds the dataprovider back onto the canvas at the specifed
        location and configures it with the given settings
        """
        log.debug("Restoring %s to (source=%s)" % (wrapperKey,trySourceFirst))
        wrapper = self.moduleManager.get_module_wrapper_with_instance(wrapperKey)
        if dpName:
            wrapper.set_name(dpName)
        if wrapper is not None:
            if dpxml and isinstance(dpxml, basestring):
                wrapper.set_configuration_xml(xmltext=dpxml, xmlversion=xml_version)
            elif dpxml:
                for i in dpxml.childNodes:
                    if i.nodeType == i.ELEMENT_NODE and i.localName == "configuration":
                        wrapper.set_configuration_xml(xmltext=i.toxml(), xmlversion=xml_version)
        cond.add_dataprovider(wrapper, trySourceFirst)

    def on_dataprovider_available_unavailable(self, loader, dpw):
        """
        Removes all PendingWrappers corresponding to dpw and replaces with new dpw instances
        """
        key = dpw.get_key()
        for c in self.get_all_conduits():
            for dp in c.get_dataproviders_by_key(key):
                new = self.moduleManager.get_module_wrapper_with_instance(key)
                #retain configuration information
                new.set_configuration_xml(dp.get_configuration_xml())
                new.set_name(dp.get_name())
                c.change_dataprovider(
                                    oldDpw=dp,
                                    newDpw=new
                                    )

    def emit(self, *args):
        """
        Override the gobject signal emission so that all signals are emitted 
        from the main loop on an idle handler
        """
        gobject.idle_add(gobject.GObject.emit,self,*args)
        
    def create_preconfigured_conduit(self, sourceKey, sinkKey, twoway):
        cond = Conduit.Conduit(self.syncManager)
        self.add_conduit(cond)
        if twoway == True:
            cond.enable_two_way_sync()
        self._restore_dataprovider(cond, sourceKey, trySourceFirst=True)
        self._restore_dataprovider(cond, sinkKey, trySourceFirst=False)

    def add_conduit(self, cond):
        self.conduits.append(cond)
        self.emit("conduit-added", cond)

    def remove_conduit(self, cond):
        self.emit("conduit-removed", cond)
        self._unitialize_dataproviders(cond)
        self.conduits.remove(cond)

    def get_all_conduits(self):
        return self.conduits

    def get_conduit(self, index):
        return self.conduits[index]

    def index (self, conduit):
        return self.conduits.index(conduit)        

    def num_conduits(self):
        return len(self.conduits)

    def clear(self):
        for c in self.conduits[:]:
            self.remove_conduit(c)
            
    def restore(self, xmlSettingFilePath=None):
        #log.info("Restoring Sync Set from %s" % xmlSettingFilePath)
        #from SyncSetGConf import SyncSetGConf
        self.syncsetGConf.restore()
        
    def restore_from_xml(self, xmlSettingFilePath=None):
        from SyncSetXML import SyncSetXML
        if xmlSettingFilePath == None:
            xmlSettingFilePath = self.xmlSettingFilePath
        SyncSetXML().restore_from_xml(self, xmlSettingFilePath)
    
    def save(self, xmlSettingFilePath=None):
        #from SyncSetGConf import SyncSetGConf
        self.syncsetGConf.save()
        
    def save_to_xml(self, xmlSettingFilePath=None):
        from SyncSetXML import SyncSetXML
        if xmlSettingFilePath == None:
            xmlSettingFilePath = self.xmlSettingFilePath
        SyncSetXML().save_to_xml(self, xmlSettingFilePath)

    def quit(self):
        """
        Calls unitialize on all dataproviders
        """
        for c in self.conduits:
            self._unitialize_dataproviders(c)

