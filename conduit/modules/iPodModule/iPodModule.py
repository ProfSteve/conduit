import sys
import os
import pickle
import logging
import time
import socket
import locale
import weakref
import threading
import gobject
import gio
log = logging.getLogger("modules.iPod")

import conduit
import conduit.dataproviders.DataProvider as DataProvider
import conduit.dataproviders.DataProviderCategory as DataProviderCategory
import conduit.dataproviders.MediaPlayerFactory as MediaPlayerFactory
import conduit.dataproviders.HalFactory as HalFactory
import conduit.utils as Utils
import conduit.datatypes.Note as Note
import conduit.datatypes.Contact as Contact
import conduit.datatypes.Event as Event
import conduit.datatypes.File as File
import conduit.datatypes.Audio as Audio
import conduit.datatypes.Video as Video

from gettext import gettext as _

Utils.dataprovider_add_dir_to_path(__file__)
from idevice import iPhoneContactsTwoWay, iPhoneCalendarsTwoWay
from ipod import IPodMusicTwoWay, IPodVideoTwoWay, IPodNoteTwoWay, IPodContactsTwoWay, IPodCalendarTwoWay, IPodPhotoSink

MODULES = {
    "iPodFactory" :         { "type":   "dataprovider-factory"  },
    "iPhoneFactory" :       { "type":   "dataprovider-factory"  },
}

PROPS_KEY_MOUNT = "CONDUIT_MOUNTPOINT"
PROPS_KEY_NAME  = "CONDUIT_NAME"
PROPS_KEY_ICON  = "CONDUIT_ICON"
PROPS_KEY_UUID  = "CONDUIT_UUID"
PROPS_KEY_TYPE  = "CONDUIT_TYPE"

def _string_to_unqiue_file(txt, base_uri, prefix, postfix=''):
    temp = Utils.new_tempfile(txt)
    uri = os.path.join(base_uri, prefix+temp.get_filename()+postfix)
    temp.transfer(uri, True)
    temp.set_UID(os.path.basename(uri))
    return temp.get_rid()

def _get_apple_label(props):
    return props.get(PROPS_KEY_NAME,
            "Apple " + props.get("ID_MODEL", "Device"))

def _get_apple_icon(props):
    return props.get(PROPS_KEY_ICON, "multimedia-player-apple-ipod")

class iPhoneFactory(HalFactory.HalFactory):

    UDEV_SUBSYSTEMS = ("usb",)

    def is_interesting(self, sysfs_path, props):
        #there is no media-player-info support for the apple iphone, so instead 
        #we have to look for the correct model name instead.
        if "Apple" in props.get("ID_VENDOR", "") and "iPhone" in props.get("ID_MODEL", ""):
            #also have to check the iPhone has a valid serial, as that is used
            #with gvfs to generate the uuid of the moint
            self._print_device(self.gudev.query_by_sysfs_path(sysfs_path))
            if props.get("ID_SERIAL_SHORT"):
                uuid = "afc://%s/" % props["ID_SERIAL_SHORT"]
                for m in gio.volume_monitor_get().get_mounts():
                    root = m.get_root()
                    uri = root.get_uri()
                    if uuid == uri:
                        #check that gvfs has mounted the volume at the expected location
                        #FIXME: this is not very nice, as it depends on an implementation
                        #detail of gvfs-afc backend. It would be best if there was some UUID
                        #that was present in udev and guarenteed to be present in all gio mounts
                        #but experimentation tells me there is no such uuid, it returns None
                        props[PROPS_KEY_MOUNT] = root.get_path()
                        props[PROPS_KEY_NAME]  = m.get_name()
                        props[PROPS_KEY_ICON]  = "phone"
                        props[PROPS_KEY_UUID]  = props["ID_SERIAL_SHORT"]
                        props[PROPS_KEY_TYPE]  = props["ID_MODEL"]
                        return True
                log.warning("iPhone not mounted by gvfs")
            else:
                log.critical("iPhone missing ID_SERIAL_SHORT udev property")
        return False

    def get_category(self, key, **props):
        """ Return a category to contain these dataproviders """
        return DataProviderCategory.DataProviderCategory(
                    _get_apple_label(props),
                    _get_apple_icon(props),
                    key)
    
    def get_dataproviders(self, key, **props):
        """ Return a list of dataproviders for this class of device """
        return [IPodDummy, IPodPhotoSink, iPhoneCalendarsTwoWay]

    def get_args(self, key, **props):
        return (props[PROPS_KEY_UUID], props[PROPS_KEY_TYPE])

class iPodFactory(MediaPlayerFactory.MediaPlayerFactory):

    def is_interesting(self, sysfs_path, props):
        #FIXME:
        #
        # THIS ONLY WORKS DURING PROBE. NO IDEA WHY.
        # When called in response to a Udev added event, gioVolumeMonitor does
        # not return the newly added volumes. There appears to be some sort of
        # race condition
        #
        #just like rhythmbox, we let media-player-info do the matching, and
        #instead just check if it has told us that the media player uses the
        #ipod storage protocol
        access_protocols = self.get_mpi_access_protocol(props)
        if "ipod" in access_protocols.split(";"):
            uuid = props.get("ID_FS_UUID")
            for vol in gio.volume_monitor_get().get_volumes():
                #is this the disk corresponding to the ipod
                #FIXME: we should be able to do gio.VolumeMonitor.get_volume_for_uuid()
                #but that doesnt work
                if vol.get_identifier('uuid') == uuid:
                    #now check it is mounted
                    mount = vol.get_mount()
                    if mount:
                        f = mount.get_root()
                        props[PROPS_KEY_MOUNT] = f.get_path()
                        props[PROPS_KEY_NAME]  = "%s's %s" % (mount.get_name(), props.get("ID_MODEL", "iPod"))
                        props[PROPS_KEY_ICON]  = self.get_mpi_icon(props, fallback="multimedia-player-apple-ipod")
                        return True
                    else:
                        log.warn("ipod not mounted")
            log.warn("could not find volume with udev ID_FS_UUID: %s" % uuid)
        return False

    def get_category(self, key, **props):
        return DataProviderCategory.DataProviderCategory(
                    _get_apple_label(props),
                    _get_apple_icon(props),
                    key)

    def get_dataproviders(self, udi, **props):
        #Read information about the ipod, like if it supports
        #photos or not
        #d = gpod.itdb_device_new()
        #gpod.itdb_device_set_mountpoint(d, props[PROPS_KEY_MOUNT])
        #supportsPhotos = gpod.itdb_device_supports_photo(d)
        #gpod.itdb_device_free(d)
        #if supportsPhotos:
        return [IPodMusicTwoWay, IPodVideoTwoWay, IPodNoteTwoWay, IPodContactsTwoWay, IPodCalendarTwoWay, IPodPhotoSink]
        #else:
        #    log.info("iPod does not report photo support")
        #    return [IPodMusicTwoWay, IPodVideoTwoWay, IPodNoteTwoWay, IPodContactsTwoWay, IPodCalendarTwoWay]

    def get_args(self, key, **props):
        return (props[PROPS_KEY_MOUNT], key)

class IPodDummy(DataProvider.TwoWay):

    _name_ = "Dummy"
    _description_ = "Dummy iPod"
    _module_type_ = "twoway"
    _in_type_ = "file"
    _out_type_ = "file"

    def __init__(self, *args):
        DataProvider.TwoWay.__init__(self)
        print "CONSTRUCTED ", args
        self.args = args or "q"

    def get_UID(self):
        print "-----".join(self.args)


