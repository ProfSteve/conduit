import gobject
import dbus
import logging
log = logging.getLogger("dataproviders.HalFactory")

import conduit.utils as Utils
import conduit.dataproviders.SimpleFactory as SimpleFactory

class HalFactory(SimpleFactory.SimpleFactory):

    def __init__(self, **kwargs):
        SimpleFactory.SimpleFactory.__init__(self, **kwargs)

        # Connect to system HAL
        self.bus = dbus.SystemBus()
        self.hal_obj = self.bus.get_object("org.freedesktop.Hal", "/org/freedesktop/Hal/Manager")
        self.hal = dbus.Interface(self.hal_obj, "org.freedesktop.Hal.Manager")

        # Hookup signals
        self.hal.connect_to_signal("DeviceAdded", self._device_added)
        self.hal.connect_to_signal("DeviceRemoved", self._device_removed)
        self.hal.connect_to_signal("NewCapability", self._new_capability)

    def _maybe_new(self, device_udi):
        def check_interesting(props):
            if self.is_interesting(device_udi, props):
                self.item_added(device_udi, **props)
        self._get_properties(device_udi, handler = check_interesting)

    def _device_added(self, device_udi, *args):
        self._maybe_new(device_udi)

    def _new_capability(self, device_udi, *args):
        if not device_udi in self.items.keys():
            self._maybe_new(device_udi)

    def _device_removed(self, device_udi):
        self.item_removed(device_udi)

    def _get_properties(self, device, handler):
        buf = {}
        #log.critical("Properties for: %s" % device)
        def properties_handler(props):
            log.critical("Properties for: %s" % device)
            for key, value in props.items():
                buf[str(key)] = value
            handler(buf)
        def error_handler(excp):
            log.warn("Could not get HAL properties for %s" % device_udi)
        device_dbus_obj = self.bus.get_object("org.freedesktop.Hal" ,device)
        if handler:
            device_dbus_obj.GetAllProperties(dbus_interface="org.freedesktop.Hal.Device", 
                reply_handler = properties_handler, error_handler = error_handler)
        else:
            for x, y in device_dbus_obj.GetAllProperties(dbus_interface="org.freedesktop.Hal.Device").items():
                #DBus *still* does not marshal dbus.String to str correctly,
                #so we force it to
                buf[str(x)] = y
            return buf
        '''
        try:
            device_dbus_obj = self.bus.get_object("org.freedesktop.Hal" ,device)
            for x, y in device_dbus_obj.GetAllProperties(dbus_interface="org.freedesktop.Hal.Device", 
                    reply_hanlder = properties_handler).items():
                #DBus *still* does not marshal dbus.String to str correctly,
                #so we force it to
                buf[str(x)] = y
        except:
            log.warn("Could not get HAL properties for %s" % device_udi)
        return buf
        '''

    def probe(self):
        """
        Enumerate HAL for any entries of interest
        """
        #devices = self.hal.GetAllDevices()
        
        for device in self.hal.GetAllDevices():
            self._maybe_new(str(device))

    def get_args(self, udi, **kwargs):
        return (udi,)

