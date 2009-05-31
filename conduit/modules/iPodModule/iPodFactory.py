"""
Provides a number of dataproviders which are associated with
removable devices such as USB keys.

It also includes classes specific to the ipod.
This file is not dynamically loaded at runtime in the same
way as the other dataproviders as it needs to be loaded all the time in
order to listen to HAL events

Copyright: John Stowers, 2006
License: GPLv2
"""
import os
import logging
import threading
import gobject
log = logging.getLogger("modules.iPodFactory")

import conduit
import conduit.dataproviders.DataProvider as DataProvider
import conduit.dataproviders.DataProviderCategory as DataProviderCategory
import conduit.dataproviders.VolumeFactory as VolumeFactory
import conduit.utils as Utils
import conduit.datatypes.Note as Note
import conduit.datatypes.Contact as Contact
import conduit.datatypes.Event as Event
import conduit.datatypes.File as File
import conduit.datatypes.Audio as Audio
import conduit.datatypes.Video as Video

from gettext import gettext as _

MODULES = {
            "iPodFactory" :         { "type":   "dataprovider-factory"  },
        }

class iPodFactory(VolumeFactory.VolumeFactory):

    def _get_mount_path(self, props):
        return str(props["volume.mount_point"])

    def is_interesting(self, udi, props):
        if props.get("info.parent"):
            parent = self._get_properties(props["info.parent"], None)
            if parent.get("storage.model") == "iPod":
                props.update(parent)
                return True
        return False

    def get_category(self, udi, **kwargs):
        label = kwargs['volume.label']
        if not label:
            label = "Apple iPod Music Player"
        return DataProviderCategory.DataProviderCategory(
                    label,
                    "multimedia-player-ipod-standard-color",
                    self._get_mount_path(kwargs))

    def get_dataproviders(self, udi, **kwargs):
        import iPodModule
        if not iPodModule.availiable:
            return None
        #Read information about the ipod, like if it supports
        #photos or not
        d = gpod.itdb_device_new()
        gpod.itdb_device_set_mountpoint(d,self._get_mount_path(kwargs))
        supportsPhotos = gpod.itdb_device_supports_photo(d)
        gpod.itdb_device_free(d)
        if supportsPhotos:
            return [IPodMusicTwoWay, IPodVideoTwoWay, IPodNoteTwoWay, IPodContactsTwoWay, IPodCalendarTwoWay, IPodPhotoSink]
        else:
            log.info("iPod does not report photo support")
            return [IPodMusicTwoWay, IPodVideoTwoWay, IPodNoteTwoWay, IPodContactsTwoWay, IPodCalendarTwoWay]

    def get_args(self, udi, **kwargs):
        """
        iPod needs a local path to the DB, not a URI
        """
        kwargs["mount_path"] = self._get_mount_path(kwargs)
        return (kwargs['mount_path'], udi)
