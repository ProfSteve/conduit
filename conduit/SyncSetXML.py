import xml.dom.minidom
import os
import logging
log = logging.getLogger("SyncSetXML")
import traceback

import conduit
import conduit.Conduit as Conduit
import conduit.Settings as Settings

#Increment this number when the xml settings file
#changes format
SETTINGS_VERSION = "2"

class SyncSetXML(object):
    def save_to_xml(self, syncset, xmlSettingFilePath=None):
        """
        Saves the synchronisation settings (icluding all dataproviders and how
        they are connected) to an xml file so that the 'sync set' can
        be restored later
        """
        log.info("Saving XML Sync Set to %s" % xmlSettingFilePath)
        #Build the application settings xml document
        doc = xml.dom.minidom.Document()
        rootxml = doc.createElement("conduit-application")
        rootxml.setAttribute("application-version", conduit.VERSION)
        rootxml.setAttribute("settings-version", SETTINGS_VERSION)
        doc.appendChild(rootxml)
        
        #Store the conduits
        for cond in syncset.conduits:
            conduitxml = doc.createElement("conduit")
            conduitxml.setAttribute("uid",cond.uid)
            conduitxml.setAttribute("twoway",str(cond.is_two_way()))
            conduitxml.setAttribute("autosync",str(cond.do_auto_sync()))
            for policyName in Conduit.CONFLICT_POLICY_NAMES:
                conduitxml.setAttribute(
                                "%s_policy" % policyName,
                                cond.get_policy(policyName)
                                )
            rootxml.appendChild(conduitxml)
            
            #Store the source
            source = cond.datasource
            if source is not None:
                sourcexml = doc.createElement("datasource")
                sourcexml.setAttribute("key", source.get_key())
                sourcexml.setAttribute("name", source.get_name())
                conduitxml.appendChild(sourcexml)
                #Store source settings
                configxml = xml.dom.minidom.parseString(source.get_configuration_xml())
                sourcexml.appendChild(configxml.documentElement)
            
            #Store all sinks
            sinksxml = doc.createElement("datasinks")
            for sink in cond.datasinks:
                sinkxml = doc.createElement("datasink")
                sinkxml.setAttribute("key", sink.get_key())
                sinkxml.setAttribute("name", sink.get_name())
                sinksxml.appendChild(sinkxml)
                #Store sink settings
                configxml = xml.dom.minidom.parseString(sink.get_configuration_xml())
                sinkxml.appendChild(configxml.documentElement)
            conduitxml.appendChild(sinksxml)        

        #Save to disk
        try:
            file_object = open(xmlSettingFilePath, "w")
            file_object.write(doc.toxml())
            #file_object.write(doc.toprettyxml())
            file_object.close()        
        except IOError, err:
            log.warn("Could not save settings to %s (Error: %s)" % (xmlSettingFilePath, err.strerror))
        
    def restore_from_xml(self, syncset, xmlSettingFilePath=None):
        """
        Restores sync settings from the xml file
        """

        log.info("Restoring XML Sync Set from %s" % xmlSettingFilePath)
           
        #Check the file exists
        if not os.path.isfile(xmlSettingFilePath):
            log.info("%s not present" % xmlSettingFilePath)
            return
            
        try:
            #Open                
            doc = xml.dom.minidom.parse(xmlSettingFilePath)
            
            #check the xml file is in a version we can read.
            if doc.documentElement.hasAttribute("settings-version"):
                xml_version = doc.documentElement.getAttribute("settings-version")
                try:
                    xml_version = int(xml_version)
                except ValueError, TypeError:
                    log.error("%s xml file version is not valid" % xmlSettingFilePath)
                    os.remove(xmlSettingFilePath)
                    return
                if int(SETTINGS_VERSION) < xml_version:
                    log.warning("%s xml file is incorrect version" % xmlSettingFilePath)
                    os.remove(xmlSettingFilePath)
                    return
            else:
                log.info("%s xml file version not found, assuming version 1" % xmlSettingFilePath)
                xml_version = 1
            
            #Parse...    
            for conds in doc.getElementsByTagName("conduit"):
                #create a new conduit
                cond = Conduit.Conduit(syncset.syncManager, conds.getAttribute("uid"))
                syncset.add_conduit(cond)

                #restore conduit specific settings
                twoway = Settings.string_to_bool(conds.getAttribute("twoway"))
                if twoway == True:
                    cond.enable_two_way_sync()
                auto = Settings.string_to_bool(conds.getAttribute("autosync"))
                if auto == True:
                    cond.enable_auto_sync()
                for policyName in Conduit.CONFLICT_POLICY_NAMES:
                    cond.set_policy(
                                policyName,
                                conds.getAttribute("%s_policy" % policyName)
                                )

                #each dataprovider
                for i in conds.childNodes:
                    #keep a ref to the dataproider was added to so that we
                    #can apply settings to it at the end
                    #one datasource
                    if i.nodeType == i.ELEMENT_NODE and i.localName == "datasource":
                        key = i.getAttribute("key")
                        name = i.getAttribute("name")
                        #add to canvas
                        if len(key) > 0:
                            syncset._restore_dataprovider(cond, key, name, i, xml_version, True)
                    #many datasinks
                    elif i.nodeType == i.ELEMENT_NODE and i.localName == "datasinks":
                        #each datasink
                        for sink in i.childNodes:
                            if sink.nodeType == sink.ELEMENT_NODE and sink.localName == "datasink":
                                key = sink.getAttribute("key")
                                name = sink.getAttribute("name")
                                #add to canvas
                                if len(key) > 0:
                                    syncset._restore_dataprovider(cond, key, name, sink, xml_version, False)

        except Exception:
            log.warn("Error parsing %s. Exception:\n%s" % (xmlSettingFilePath, traceback.format_exc()))
            os.remove(xmlSettingFilePath)
