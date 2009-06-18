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
from datetime import timedelta

MODULES = {
    "TrackerContacts": { "type": "dataprovider" },
    "TrackerCalendar": { "type": "dataprovider" },
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
        return Rid(c.uri, mtime=c.modified, hash=None)

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
                if x.family:
                    c.namefamily = x.family
                if x.given:
                    c.namegiven = x.given
                if x.additional:
                    c.nameadditional = x.additional
                if x.prefix:
                    c.namehonorificprefix = x.prefix
                if x.suffix:
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

        name = vobject.vcard.Name()
        c.vcard.n.value = name

        for key, value in tracker.properties():
            if key == "nco:gender":
                c.vcard.add('x-gender').value = value
            elif key == "nco:fullname":
                c.vcard.fn.value = value
            elif key == "nco:nickname":
                c.vcard.add('nickname').value = value
            elif key == "nco:birthDate":
                c.vcard.add("bday").value = value
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
                c.vcard.add('adr').value = vadr
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
            elif key == "nco:nameFamily":
                name.family = value
            elif key == "nco:nameGiven":
                name.given = value
            elif key == "nco:nameAdditional":
                name.additonal = value
            elif key == "nco:nameHonorificPrefix":
                name.prefix = value
            elif key == "nco:nameHonorificSuffix":
                name.suffix = value
            else:
                log.warning("Unhandled %s" % key)

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
        return Rid(c.uri, mtime=c.modified, hash=None)

    def delete(self, LUID):
        if LUID in self.events:
            self.events[LUID].delete()

    def finish(self, aborted, error, conflict):
        DataProvider.TwoWay.finish(self)
        self.events = None

    def _create_tracker_recurrence(self, v):
        t = ncal.RecurrenceRule.create(commit=False)
        for pair in v[0].value.split(";"):
            key, value = pair.split("=")
            key, value = key.lower(), value.lower()
            if key == "bysecond":
                t.bysecond = int(value)
            elif key == "byminute":
                t.byminute = int(value)
            elif key == "byhour":
                t.byhour = int(value)
            elif key == "byday":
                #t.byday
                pass
            elif key == "bymonthday":
                t.bymonthday = int(value)
            elif key == "bymonth":
                t.bymonth = int(value)
            elif key == "bysetpos":
                t.bysetpos = int(value)
            elif key == "byweekno":
                t.byweekno = int(value)
            elif key == "byyearday":
                t.byyearday = int(value)
            elif key == "count":
                t.count = int(value)
            elif key == "freq":
                #t.freq
                pass
            elif key == "interval":
                t.interval = int(value)
            elif key == "until":
                t.until = value
            elif key == "wkst":
                #t.wkst ncal:Weekday
                pass
            else:
                log.debug("Unknown rrule property: %s" % key)
        t.commit()
        return t

    def _create_ical_recurrence(self, t):
        v = ""
        for key, value in t.properties():
            if key in ("ncal:bysecond", "ncal:byminute", "ncal:byhour", "ncal:bymonthday",
                       "ncal:bymonth", "ncal:bysetpos", "ncal:byweekno", "ncal:byyearday",
                       "ncal:count", "ncal:interval"):
                k = key[5:].upper()
                v += "%s=%s" % (k, value)
            elif key == "byday":
                #v.byday
                pass
            elif key == "freq":
                #v.freq
                pass
            elif key == "until":
                pass
            elif key == "wkst":
                #v.wkst ncal:Weekday
                pass
            else:
                log.debug("Unknown rrule property: %s" % key)
        return v

    def _ical_to_tracker(self, data):
        ical = data.iCal
        if ical.name == "VCALENDAR":
            ical = ical.vevent

        c = ncal.Event.create(commit=False)

        for k, v in ical.contents.iteritems():
            if k == "description":
                c.description = v[0].value
            elif k == "summary":
                c.summary = v[0].value
            elif k == "dtstart":
                c.dtstart = ncal.NcalDateTime.create(datetime=v[0].value)
            elif k == "dtend":
                c.dtend = ncal.NcalDateTime.create(datetime=v[0].value)
            elif k == "duration":
                c.duration = v[0].value.seconds / (60 * 60)
            elif k == "uid":
                c.uid = v[0].value
            elif k == "url":
                c.url = v[0].value
            elif k == 'recurrence-id':
                c.recurrenceid = v[0].value
            elif k == "location":
                c.location = v[0].value
            elif k == "priority":
                c.priority = v[0].value
            elif k == "last-modified":
                c.lastmodified = v[0].value
            elif k == "categories":
                c.categories = v[0].value
            elif k == "contact":
                c.contact = v[0].value
            elif k == "rrule":
                c.rrule = self._create_tracker_recurrence(v)
            elif k == "exrule":
                c.exrule = self._create_tracker_recurrence(v)
            elif k == "status":
                # 'TENTATIVE' etc to an EventStatus instance
                pass
            else:
                log.warning("Unhandled key: %s" % k)

        return c

    def _tracker_to_ical(self, tracker):
        e = Event.Event()
        cal = e.iCal
        ev = e.iCal.add('vevent')

        for key, value in tracker.properties():
            if key == "ncal:description":
                ev.add("description").value = value
            elif key == "ncal:summary":
                ev.add("summary").value = value
            elif key == "ncal:dtstart":
                dt = ncal.NcalDateTime(value)
                ev.add('dtstart').value = dt.datetime
            elif key == "ncal:dtend":
                dt = ncal.NcalDateTime(value)
                ev.add('dtend').value = dt.datetime
            elif key == "ncal:duration":
                ev.add('duration').value = timedelta(0, int(value)*60*60, 0)
            elif key == "ncal:uid":
                ev.add('uid').value = value
            elif key == "ncal:url":
                ev.add('url').value = value
            elif key == "ncal:recurrenceId":
                ev.add('recurrence-id').value = value
            elif key == "ncal:location":
                ev.add('location').value = value
            elif key == "ncal:priority":
                ev.add('priority').value = value
            elif key == "ncal:lastModified":
                ev.add('last-modified').value = value
            elif key == "ncal:categories":
                ev.add('categories').value = value
            elif key == "ncal:contact":
                ev.add('contact').value = value
            elif key == "ncal:rrule":
                rrule = ncal.RecurrenceRule(value)
                ev.add('rrule').value = self._create_ical_recurrence(rrule)
            elif key == "ncal:exrule":
                rrule = ncal.RecurrenceRule(value)
                ev.add('exrule').value = self._create_ical_recurrence(rrule)
            elif key == "ncal:status":
                # An instance of ncal:EventStatus to represent TENTATIVE etc
                pass
            else:
                log.warning("Unhandled key: %s" % key)

        return e

    def get_UID(self):
        return ""

