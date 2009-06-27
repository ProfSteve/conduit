"""
Copyright: Alexandre Rosenfeld, 2009
License: GPLv2
"""
import os
import logging
import threading
import gobject
log = logging.getLogger("modules.GoogleFactory")

import conduit
import conduit.dataproviders.DataProvider as DataProvider
import conduit.dataproviders.DataProviderCategory as DataProviderCategory
import conduit.dataproviders.AccountFactory as AccountFactory
import conduit.utils as Utils

from gettext import gettext as _

MODULES = {
            "GoogleFactory" :         { "type":   "dataprovider-factory"  },
        }

class GoogleFactory(AccountFactory.AccountFactory):
    _name_ = "Google"
    _properties_ = {"username": str, "password": str}
    _icon_ = "image-missing"
    
    def get_dataproviders(self, key, **kwargs):
        #import GoogleModule
        Utils.dataprovider_add_dir_to_path(__file__)
        from conduit.modules.GoogleModule.GoogleModule import PicasaTwoWay, YouTubeTwoWay, ContactsTwoWay, DocumentsSink
        return PicasaTwoWay, YouTubeTwoWay, ContactsTwoWay, DocumentsSink
