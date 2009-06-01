import os.path
from gettext import gettext as _
import logging
log = logging.getLogger("modules.RemovableDeviceFactory")

import conduit
import conduit.dataproviders.DataProvider as DataProvider
import conduit.dataproviders.DataProviderCategory as DataProviderCategory
import conduit.dataproviders.File as FileDataProvider
import conduit.dataproviders.SimpleFactory as SimpleFactory
import conduit.dataproviders.AutoSync as AutoSync
import conduit.utils as Utils
import conduit.Vfs as Vfs

MODULES = {
    "RemovableDeviceFactory" :  { "type": "dataprovider-factory" }
    }

class RemovableDeviceFactory(SimpleFactory.SimpleFactory):

    def __init__(self, **kwargs):
        SimpleFactory.SimpleFactory.__init__(self, **kwargs)
        self._volumes = {}
        self._categories = {}
        self._vm = Vfs.VolumeMonitor()
        self._vm.connect("volume-mounted",self._volume_mounted_cb)
        self._vm.connect("volume-unmounted",self._volume_unmounted_cb)

    def _volume_mounted_cb(self, monitor, device_udi, mount, label):
        log.info("Volume mounted, %s : (%s : %s)" % (device_udi,mount,label))
        if device_udi:
            self._check_preconfigured(device_udi, mount, label)
            self.item_added(device_udi, mount=mount, label=label)

    def _volume_unmounted_cb(self, monitor, device_udi):
        log.info("Volume unmounted, %s" % device_udi)
        if device_udi and device_udi in self._volumes:
            self.item_removed(device_udi)

    def _make_class(self, udi, folder, name):
        import conduit.modules.FileModule.FileModule as FileModule
        
        log.info("Creating preconfigured folder dataprovider: %s" % folder)
        info = {    
            "DEFAULT_FOLDER":   folder,
            "_udi_"         :   udi
        }
        if name:
            info["_name_"] = name            
        
        klass = type(
                "FolderTwoWay",
                (FileModule.FolderTwoWay,),
                info)
        return klass

    def _check_preconfigured(self, udi, mountUri, label):
        #check for the presence of a mount/.conduit group file
        #which describe the folder sync groups, and their names,
        try:
            groups = FileDataProvider.read_removable_volume_group_file(mountUri)
        except Exception, e:
            log.warn("Error reading volume group file: %s" % e)
            groups = ()
            
        if len(groups) > 0:
            self._volumes[udi] = []
            for relativeUri,name in groups:
                klass = self._make_class(
                                    udi=udi,
                                    #uri is relative, make it absolute
                                    folder="%s%s" % (mountUri,relativeUri),
                                    name=name)
                self._volumes[udi].append(klass)
        else:
            klass = self._make_class(
                                udi=udi,
                                folder=mountUri,
                                name=None)
            self._volumes[udi] = [klass]

    def probe(self):
        """
        Called after initialised to detect already connected volumes
        """
        volumes = self._vm.get_mounted_volumes()
        for device_udi in volumes:
            if device_udi:
                mount,label = volumes[device_udi]
                self._check_preconfigured(device_udi, mount, label)
                self.item_added(device_udi, mount=mount, label=label)
            if device_udi:
                mount,label = volumes[device_udi]
                self.item_added(device_udi, mount=mount, label=label)

    def emit_added(self, klass, initargs, category):
        """
        Override emit_added to allow duplictes. The custom key is based on
        the folder and the udi to allow multiple preconfigured groups per
        usb key
        """
        return SimpleFactory.SimpleFactory.emit_added(self, 
                        klass, 
                        initargs, 
                        category, 
                        customKey="%s-%s" % (klass.DEFAULT_FOLDER, klass._udi_)
                        )

    def get_category(self, udi, **kwargs):
        if not self._categories.has_key(udi):
            self._categories[udi] = DataProviderCategory.DataProviderCategory(
                    kwargs['label'],
                    "drive-removable-media",
                    udi)
        return self._categories[udi]

    def get_dataproviders(self, udi, **kwargs):
         return self._volumes.get(udi,())
         
    def get_args(self, udi, **kwargs):
        return ()

