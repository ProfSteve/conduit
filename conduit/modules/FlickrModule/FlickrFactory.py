"""
Copyright: Alexandre Rosenfeld, 2009
License: GPLv2
"""
import os
import logging
import threading
import gobject
log = logging.getLogger("modules.FlickrFactory")

import conduit
import conduit.dataproviders.DataProvider as DataProvider
import conduit.dataproviders.DataProviderCategory as DataProviderCategory
import conduit.dataproviders.AccountFactory as AccountFactory
import conduit.utils as Utils

from gettext import gettext as _

MODULES = {
            "FlickrFactory" :         { "type":   "dataprovider-factory"  },
        }

class FlickrFactory(AccountFactory.AccountFactory):
    _name_ = "Flickr"
    _properties_ = {"username": str}
    _icon_ = "image-missing"
    
    def get_dataproviders(self, key, **kwargs):
        from conduit.modules.FlickrModule.FlickrModule import FlickrTwoWay
        return (FlickrTwoWay,)
