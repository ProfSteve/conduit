from gettext import gettext as _
import logging
log = logging.getLogger("modules.Tracker")

import conduit
import conduit.dataproviders.DataProvider as DataProvider
import conduit.utils as Utils
import conduit.Exceptions as Exceptions
import conduit.datatypes.Contact as Contact

Utils.dataprovider_add_dir_to_path(__file__)
import tralchemy
from tralchemy.nco import Contact as TrackerContact

MODULES = {
    "TrackerContacts": { "type": "dataprovider" },
}

class TrackerContacts(DataProvider.TwoWay):

    _name_ = _("Tracker Contacts")
    _description_ = _("Synchronize your contacts")
    _category_ = conduit.dataproviders.CATEGORY_OFFICE
    _module_type_ = "twoway"
    _in_type_ = "contact"
    _out_type_ = "contact"
    _icon_ = "x-office-address-book"

    def __init__(self):
        DataProvider.TwoWay.__init__(self)

    def refresh(self):
        DataProvider.TwoWay.refresh(self)
        self.contacts = {}
        for contact in Contact.get():
            self.contacts[contact.uri] = contact

    def get_all(self):
        DataProvider.TwoWay.get_all(self)
        return self.contacts.keys()

    def get(self, LUID):
        DataProvider.TwoWay.get(self, LUID)
        tc = self.contact[LUID]
        c = self._tracker_to_vcard(tc)
        c.set_UID(LUID)
        return c

    def put(self, obj, overwrite, LUID=None):
        DataProvider.TwoWay.put(self, obj, overwrite, LUID)
        if LUID != None:
            self.delete(LUID)
        c = self._vcard_to_tracker(obj)
        c.commit()

    def delete(self, LUID):
        if LUID in self.contacts:
            self.contacts[LUID].delete()

    def finish(self, aborted, error, conflict):
        DataProvider.TwoWay.finish(self)
        self.contacts = None

    def _vcard_to_tracker(self, data):
        vcard = data.vcard

        c = TrackerContact()

        for k, v in vcard.iteritems():
            if k == "account":
            elif k == "tel":
            elif k == "bday":
            elif k == "n":
                c.namefamily = v.value.family
                c.namegiven = v.value.given
                c.nameadditional = v.value.additional
                c.namehonorificprefix = v.value.prefix
                c.namehonorificsuffix = v.value.suffix
            elif k == "version":
            elif k == "org":
            elif k == "nickname":
                c.nickname = v
            elif k == "email":
            elif k == "fn":
                c.fullname = v
            else:
                log.warning("Unhandled key: %s" % k)

        return c

    def _tracker_to_vcard(self, tracker):
        c = Contact.Contact()

        if tracker.fullname:
            c.vcard.('fn') = tracker.fullname

        if tracker.nickname:
            c.vcard.add('nickname') = tracker.nickname

        if tracker.namefamily or tracker.namegiven or tracker.nameadditional or
            tracker.namehonorificprefix or tracker.namehonorificsuffix:
            n = vobject.vcard.Name(family=tracker.namefamily, given=tracker.namegiven, additional=tracker.nameadditional,
                                   prefix=tracker.namehonorificprefix, suffix=tracker.namehonorificsuffix)
            c.add('n') = n

        return c

    def get_UID(self):
        return ""

