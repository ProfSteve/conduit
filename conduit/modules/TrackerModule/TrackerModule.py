from gettext import gettext as _
import logging
log = logging.getLogger("modules.Tracker")

import conduit
import conduit.dataproviders.DataProvider as DataProvider
import conduit.utils as Utils
import conduit.Exceptions as Exceptions
import conduit.datatypes.Contact as Contact
import conduit.datatypes.Event as Event
from conduit.datatypes import Rid

Utils.dataprovider_add_dir_to_path(__file__)
import tralchemy
from tralchemy import nco
from tralchemy import ncal
import vobject

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
        for contact in nco.PersonContact.get():
            self.contacts[str(contact.uri)] = contact

    def get_all(self):
        DataProvider.TwoWay.get_all(self)
        return self.contacts.keys()

    def get(self, LUID):
        DataProvider.TwoWay.get(self, LUID)
        tc = self.contacts[LUID]
        c = self._tracker_to_vcard(tc)
        c.set_mtime(tc.modified)
        c.set_UID(LUID)
        return c

    def put(self, obj, overwrite, LUID=None):
        DataProvider.TwoWay.put(self, obj, overwrite, LUID)
        if LUID != None:
            self.delete(LUID)
        c = self._vcard_to_tracker(obj)
        c.commit()
        return Rid(c.uri, mtime=None, hash=None)

    def delete(self, LUID):
        if LUID in self.contacts:
            self.contacts[LUID].delete()

    def finish(self, aborted, error, conflict):
        DataProvider.TwoWay.finish(self)
        self.contacts = None

    def _vcard_to_tracker(self, data):
        vcard = data.vcard

        c = nco.PersonContact.create(commit=False)

        for k, v in vcard.contents.iteritems():
            if k == "account":
                pass
            elif k == "tel":
                pn = nco.PhoneNumber.create(phonenumber=v[0].value)
                c.hasphonenumber = pn
            elif k == "bday":
                c.birthdate = v[0].value
            elif k == "n":
                x = v[0].value
                c.namefamily = x.family
                c.namegiven = x.given
                c.nameadditional = x.additional
                c.namehonorificprefix = x.prefix
                c.namehonorificsuffix = x.suffix
            elif k == "adr":
                x = v[0].value
                adr = nco.PostalAddress.create(commit=False)
                if x.box:
                    adr.pobox = x.box
                if x.extended:
                    adr.extendedaddress = x.extended
                if x.street:
                    adr.streetaddress = x.street
                if x.city:
                    adr.locality = x.city
                if x.code:
                    adr.postalcode = x.code
                if x.country:
                    adr.country = x.country
                adr.commit()
                c.haspostaladdress = adr
            elif k == "version":
                pass
            elif k == "org":
                pass
            elif k == "nickname":
                c.nickname = v[0].value
            elif k == "email":
                ea = nco.EmailAddress.create(emailaddress=v[0].value)
                c.hasemailaddress = ea
            elif k == "fn":
                c.fullname = v[0].value
            elif k == "x-gender":
                c.gender = v[0].value
            else:
                log.warning("Unhandled key: %s" % k)

        return c

    def _tracker_to_vcard(self, tracker):
        c = Contact.Contact()

        for key, value in tracker.properties():
            if key == "nco:gender":
                c.vcard.add('x-gender').value = value
            elif key == "nco:fullName":
                c.vcard.fn.value = value
            elif key == "nco:nickname":
                c.vcard.add('nickname').value = value
            elif key == "nco:note":
                c.vcard.add('note').value = value
            elif key == "nco:hasEmailAddress":
                em = nco.EmailAddress(value)
                c.vcard.add('email').value = em.emailaddress
            elif key == "nco:hasIMAccount":
                im = nco.IMAccount(value)
                proto = im.improtocol
                if proto == "aim":
                    c.vcard.add('x-aim').value = im.imid
                elif proto == "icq":
                    c.vcard.add('x-icq').value = im.imid
                elif proto == "jabber":
                    c.vcard.add('x-jabber').value = im.imid
                elif proto == "msn":
                    c.vcard.add('x-msn').value = im.imid
                elif proto == "yahoo":
                    c.vcard.add('x-yahoo').value = im.imid
                elif proto == "skype":
                    c.vcard.add('x-skype-username').value = im.imid
                elif proto == "gadugadu":
                    c.vcard.add('x-gadugadu').value = im.imid
            elif key == "nco:hasPostalAddress":
                adr = nco.PostalAddress(value)
                vadr = vobject.vcard.Address()
                if adr.pobox:
                    vadr.box = adr.pobox
                if adr.extendedaddress:
                    vadr.extended = adr.extendedaddress
                if adr.streetaddress:
                    vadr.street = adr.streetaddress
                if adr.locality:
                    vadr.city = adr.locality
                if adr.region:
                    vadr.region = adr.region
                if adr.postalcode:
                    vadr.code = adr.postalcode
                if adr.country:
                    vadr.country = adr.country
                c.vcard.add('addr').value = vadr
            elif key == "nco:hasPhoneNumber":
                phone = nco.PhoneNumber(value)
                c.vcard.add('tel').value = phone.phonenumber
            elif key == "nco:url":
                c.vcard.add('url').value = value
            elif key == "nco:websiteurl":
                c.vcard.add('x-website-url').value = value
            elif key == "nco:blogurl":
                c.vcard.add('x-blog-url').value = value
            elif key == "nco:foafurl":
                c.vcard.add('x-foaf-url').value = value
            elif key == "nco:photo":
                """ Points to a photo of vic - embed in vcard """
                pass
            elif key == "nco:sound":
                """ Points to a sound of vic - embed in vcard """
                pass
            elif key == "nco:key":
                """ An encryption key in a file - embed in vcard """
                pass
            elif key == "nco:contactUID":
                c.vcard.add("uid").value = value
            elif key == "nco:hobby":
                c.vcard.add("x-hobby").value = value

        if tracker.namefamily or tracker.namegiven or tracker.nameadditional or tracker.namehonorificprefix or tracker.namehonorificsuffix:
            n = vobject.vcard.Name(family=tracker.namefamily, given=tracker.namegiven, additional=tracker.nameadditional,
                                   prefix=tracker.namehonorificprefix, suffix=tracker.namehonorificsuffix)
            c.vcard.n.value = n

        return c

    def get_UID(self):
        return ""

class TrackerCalendar(DataProvider.TwoWay):

    _name_ = _("Tracker Calendar")
    _description_ = _("Synchronize your calendar")
    _category_ = conduit.dataproviders.CATEGORY_OFFICE
    _module_type_ = "twoway"
    _in_type_ = "event"
    _out_type_ = "event"
    _icon_ = "x-office-calendar"

    def __init__(self):
        DataProvider.TwoWay.__init__(self)

    def refresh(self):
        DataProvider.TwoWay.refresh(self)
        self.events = {}
        for event in ncal.Event.get():
            self.events[str(event.uri)] = event

    def get_all(self):
        DataProvider.TwoWay.get_all(self)
        return self.events.keys()

    def get(self, LUID):
        DataProvider.TwoWay.get(self, LUID)
        tc = self.events[LUID]
        c = self._tracker_to_ical(tc)
        c.set_mtime(tc.modified)
        c.set_UID(LUID)
        return c

    def put(self, obj, overwrite, LUID=None):
        DataProvider.TwoWay.put(self, obj, overwrite, LUID)
        if LUID != None:
            self.delete(LUID)
        c = self._ical_to_tracker(obj)
        c.commit()
        return Rid(c.uri, mtime=None, hash=None)

    def delete(self, LUID):
        if LUID in self.events:
            self.events[LUID].delete()

    def finish(self, aborted, error, conflict):
        DataProvider.TwoWay.finish(self)
        self.events = None

    def _ical_to_tracker(self, data):
        ical = data.iCal

        c = ncal.Event.create(commit=False)

        for k, v in ical.contents.iteritems():
            if k == "description":
                c.description = v
            elif k == "summary":
                c.summary = v
            elif k == "dtstart":
                c.dtstart = v
            elif k == "dtend":
                c.dtend = v
            elif k == "duration":
                c.duration = v
            elif k == "uid":
                c.uid = v
            elif k == "url":
                c.url = v
            elif k == 'recurrence-id':
                c.recurrenceid = v
            elif k == "location":
                c.location = v
            elif k == "priority":
                c.priority = v
            elif k == "last-modified":
                c.lastmodified = v
            elif k == "categories":
                c.categories = v
            elif k == "contact":
                c.contact = v
            elif k == "status":
                # 'TENTATIVE' etc to an EventStatus instance
                pass
            else:
                log.warning("Unhandled key: %s" % k)

        return c

    def _tracker_to_ical(self, tracker):
        e = Event.Event()

        for key, value in tracker.properties():
            if key == "ncal:description":
                e.iCal.add("description").value = value
            elif key == "ncal:summary":
                e.iCal.add("summary").value = value
            elif key == "ncal:dtstart":
                e.iCal.add('dtstart').value = value
            elif key == "ncal:dtend":
                e.iCal.add('dtend').value = value
            elif key == "ncal:duration":
                e.iCal.add('duration').value = value
            elif key == "ncal:uid":
                e.iCal.add('uid').value = value
            elif key == "ncal:url":
                e.iCal.add('url').value = value
            elif key == "ncal:recurrenceId":
                e.iCal.add('recurrence-id').value = value
            elif key == "ncal:location":
                e.iCal.add('location').value = value
            elif key == "ncal:priority":
                e.iCal.add('priority').value = value
            elif key == "ncal:lastModified":
                e.iCal.add('last-modified').value = value
            elif key == "ncal:categories":
                e.iCal.add('categories').value = value
            elif key == "ncal:contact":
                e.iCal.add('contact').value = value
            elif key == "ncal:status":
                # An instance of ncal:EventStatus to represent TENTATIVE etc
                pass
            else:
                log.warning("Unhandled key: %s" % key)

        return e

    def get_UID(self):
        return ""

