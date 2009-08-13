
import xml.dom.minidom
import os
import logging
log = logging.getLogger("SyncSetGConf")
import traceback

import gobject
try:
    import gconf
    client = gconf.client_get_default()
    GCONF_ENABLED = True
except:
    GCONF_ENABLED = False
    log.warning("GConf is not availiable to save and restore SyncSets")

import conduit
import conduit.Conduit as Conduit
import conduit.Settings as Settings

SYNCSET_PATH = "/apps/conduit/SyncSet"

class Error(Exception):
    pass

class SyncSetGConf(gobject.GObject):
    def __init__(self, syncset):
        gobject.GObject.__init__(self)
        self.loading = False
        self.syncset = syncset
        self.syncset.connect("conduit-added", self._on_conduit_added)
        self.syncset.connect("conduit-removed", self._on_conduit_removed)

    def get_value(self, value):
        #value = client.get(path)
        if value is None:
            return None
        if value.type == gconf.VALUE_PAIR:
            log.critical("Dont know how to handle pairs: %s" % value.to_string())
            return None
        return {gconf.VALUE_BOOL: value.get_bool, 
         gconf.VALUE_FLOAT: value.get_float, 
         gconf.VALUE_INT: value.get_int, 
         gconf.VALUE_LIST: value.get_list,
         gconf.VALUE_PAIR: value.to_string, 
         gconf.VALUE_STRING: value.get_string
        }[value.type]()
        
    def set_value(self, path, value):
        vtype = type(value)
        if vtype is bool:
            client.set_bool(path, value)
        elif vtype is str:
            client.set_string(path, value)
        elif vtype is int:
            client.set_int(path, value)
        elif vtype in (list, tuple):
            #FIXME We should support more then string lists
            client.set_list(path, gconf.VALUE_STRING, [str(i) for i in value])
        else:
            log.error("We cant handle %s yet" % (repr(vtype)))

    def restore(self):
        if not GCONF_ENABLED:
            return False
        log.info("Restoring SyncSet from GConf: %s" % (SYNCSET_PATH + "/" + self.syncset.name))
        
        self.loading = True
        try:
            for path in client.all_dirs(SYNCSET_PATH + "/" + self.syncset.name):
                cond_name = path.split("/")[-1]
                cond_path = path + "/"
                if client.get_string(cond_path + "uid") is None:
                    continue
                try:                    
                    #create a new conduit
                    cond = Conduit.Conduit(self.syncset.syncManager, client.get_string(cond_path + "uid"))

                    #restore conduit specific settings
                    twoway = client.get_bool(cond_path + "twoway")
                    if twoway == True:
                        cond.enable_two_way_sync()
                    #auto = Settings.string_to_bool(conds.getAttribute("autosync"))
                    autosync = client.get_bool(cond_path + "autosync")
                    if autosync == True:
                        cond.enable_auto_sync()
                    for policyName in Conduit.CONFLICT_POLICY_NAMES:
                        policy = client.get_string(cond_path + "%s_policy" % policyName)
                        if policy:
                            cond.set_policy(policyName, policy)

                    num_sinks = client.get_int(cond_path + "sinks")
                    
                    if client.dir_exists(cond_path + "source"):
                        source_path = cond_path + "source/"
                        source_key = client.get_string(source_path + "key")
                        source_name = client.get_string(source_path + "name")
                        source_config = client.get_string(source_path + "configxml")
                        #FIXME Use config values instead of XML
                        config = {}
                        for entry in client.all_entries(source_path + "config"):
                            config[entry.key] = self.get_value(entry.value)
                        #print config
                        self.syncset._restore_dataprovider(cond, source_key, source_name, source_config, "2")
                        
                    for i in range(num_sinks):
                        sink_path = cond_path + "sink%d/" % i
                        if not client.dir_exists(cond_path + "sink%d" % i):
                            raise Error("Sink %d not found" % i)
                        sink_key = client.get_string(sink_path + "key")
                        sink_name = client.get_string(sink_path + "name")
                        sink_config = client.get_string(sink_path + "configxml")
                        self.syncset._restore_dataprovider(cond, sink_key, sink_name, sink_config, "2")

                    #cond.connect("parameters-changed", self._on_conduit_parameters_changed)
                    self.syncset.add_conduit(cond)
                except Exception:
                    #log.warning("Unable to restore conduit %s from %s. %s" % (cond_name, self.syncset.name, traceback.format_exc()))
                    #FIXME: On production we probably dont want to raise this exception
                    raise
        finally:
            self.loading = False
                

    def _on_conduit_parameters_changed(self, cond):
        log.info("Conduit paremeters changed, saving to GConf")
        self.save_conduit(cond)
        
    def _on_conduit_removed(self, syncset, cond):
        self.remove_conduit(cond)
    
    def _on_conduit_added(self, syncset, cond):
        #TODO: Not sure this actually works, it still saves conduits right after
        # loading them
        
        # Dont save conduits if we are still loading them
        if not self.loading:
            self.save_conduit(cond)
        cond.connect("parameters-changed", self._on_conduit_parameters_changed)
    
    def save_conduit(self, cond, with_dps = False):
        log.critical("Saving conduit")
        if not GCONF_ENABLED:
            return False
        conduit_path = "/".join((SYNCSET_PATH, self.syncset.name, cond.uid)) + "/"
        client.set_string(conduit_path + "uid", cond.uid)
        client.set_bool(conduit_path + "twoway", cond.is_two_way())
        client.set_bool(conduit_path + "autosync", cond.do_auto_sync())
        for policyName in Conduit.CONFLICT_POLICY_NAMES:
            client.set_string(conduit_path + ("%s_policy" % policyName),
                cond.get_policy(policyName)
            )
            
        if with_dps:
            #Store the source
            source = cond.datasource
            if source is not None:
                self.save_dataprovider(cond, source, "source")
            #Store all sinks
            for i, sink in enumerate(cond.datasinks):
                self.save_dataprovider(cond, sink, "sink%s" % i)
                
            client.set_int(conduit_path + "sinks", len(cond.datasinks))        
    
    def remove_conduit(self, cond):
        if not GCONF_ENABLED:
            return False
        conduit_path = "/".join((SYNCSET_PATH, self.syncset.name, cond.uid))
        client.recursive_unset(conduit_path, 0)
    
    def save_dataprovider(self, cond, dp, position = "sink"):
        if not GCONF_ENABLED:
            return False
        dp_path = "/".join((SYNCSET_PATH, self.syncset.name, cond.uid, position)) + "/"
        client.set_string(dp_path + "key", dp.get_key())
        client.set_string(dp_path + "name", dp.get_name())
        #Store dp settings
        client.set_string(dp_path + "configxml", dp.get_configuration_xml())
        for key, value in dp.module.get_configuration().iteritems():
            self.set_value(dp_path + "config/" + key, value)    

    def save(self):
        if not GCONF_ENABLED:
            return False
        log.info("Saving SyncSet to GConf: %s" % (SYNCSET_PATH + "/" + self.syncset.name))
    
        syncset_path = SYNCSET_PATH + "/" + self.syncset.name + "/"
        client.recursive_unset(SYNCSET_PATH + "/" + self.syncset.name, 0)
        
        #Store the conduits
        for cond in self.syncset.conduits:
            self.save_conduit(cond, with_dps=True)
