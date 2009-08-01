
import xml.dom.minidom
import os
import logging
log = logging.getLogger("SyncSetGConf")
import traceback
import gconf
client = gconf.client_get_default()


import conduit
import conduit.Conduit as Conduit
import conduit.Settings as Settings

SYNCSET_PATH = "/apps/conduit/SyncSet"

class Error(Exception):
    pass

class SyncSetGConf(object):
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

    #FIXME: Modularize each component, making it possible to only alter parts
    #       of a syncset.
    def restore(self, syncset):
        log.info("Restoring SyncSet from GConf: %s" % (SYNCSET_PATH + "/" + syncset.name))
    
        for path in client.all_dirs(SYNCSET_PATH + "/" + syncset.name):
            cond_name = path.split("/")[-1]
            cond_path = path + "/"
            try:
                #create a new conduit
                cond = Conduit.Conduit(syncset.syncManager, client.get_string(cond_path + "uid"))

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
                    syncset._restore_dataprovider(cond, source_key, source_name, source_config, "2")
                    
                for i in range(num_sinks):
                    sink_path = cond_path + "sink%d/" % i
                    if not client.dir_exists(cond_path + "sink%d" % i):
                        raise Error("Sink not found")
                    sink_key = client.get_string(sink_path + "key")
                    sink_name = client.get_string(sink_path + "name")
                    sink_config = client.get_string(sink_path + "configxml")
                    syncset._restore_dataprovider(cond, sink_key, sink_name, sink_config, "2")

                syncset.add_conduit(cond)
            except Exception:
                #log.warning("Unable to restore conduit %s from %s. %s" % (cond_name, syncset.name, traceback.format_exc()))
                raise

    def save(self, syncset):
        log.info("Saving SyncSet to GConf: %s" % (SYNCSET_PATH + "/" + syncset.name))
    
        syncset_path = SYNCSET_PATH + "/" + syncset.name + "/"
        
        client.recursive_unset(SYNCSET_PATH + "/" + syncset.name, 0)
        
        #Store the conduits
        for cond in syncset.conduits:
            conduit_path = syncset_path + cond.uid + "/"
            client.set_string(conduit_path + "uid", cond.uid)
            client.set_bool(conduit_path + "twoway", cond.is_two_way())
            client.set_bool(conduit_path + "autosync", cond.do_auto_sync())
            for policyName in Conduit.CONFLICT_POLICY_NAMES:
                client.set_string(conduit_path + ("%s_policy" % policyName),
                                cond.get_policy(policyName)
                                )
            
            #Store the source
            source = cond.datasource
            if source is not None:
                source_path = conduit_path + "source/"
                client.set_string(source_path + "key", source.get_key())
                client.set_string(source_path + "name", source.get_name())
                #Store source settings
                #configxml = xml.dom.minidom.parseString(source.get_configuration_xml())
                client.set_string(source_path + "configxml", source.get_configuration_xml())
                for key, value in source.module.get_configuration().iteritems():
                    self.set_value(source_path + "config/" + key, value)
            
            #Store all sinks
            #sinksxml = doc.createElement("datasinks")
            for i, sink in enumerate(cond.datasinks):
                sink_path = conduit_path + "sink%s/" % i
                client.set_string(sink_path + "key", sink.get_key())
                client.set_string(sink_path + "name", sink.get_name())
                #configxml = xml.dom.minidom.parseString(sink.get_configuration_xml())
                client.set_string(sink_path + "configxml", sink.get_configuration_xml())
                for key, value in sink.module.get_configuration().iteritems():
                    self.set_value(sink_path + "config/" + key, value)
            client.set_int(conduit_path + "sinks", len(cond.datasinks))
