#! /usr/bin/env python

from plist import *
from imobiledevice import *

from iPhoneRecordEntities import *

import sys, re, time, datetime, base64

ODD_EPOCH = 978307200 # For some reason Apple decided the epoch was on a different day?

class vCardOutput():
    def __init__(self, data_class):
        self.data_class = data_class

    def serialize(self):
        storage = self.data_class.get_storage_for_entity(iPhoneContactRecordEntity)
        l = len(storage)

        result = ''
        skip = 0
        for k, i in storage.iteritems():
            if skip > 0 and skip < l:
                result += "\n"
            result += self._to_vcard(i)
            skip += 1
        return result

    def _to_vcard(self, record):
        result = "BEGIN:VCARD\n"
        result += "VERSION:3.0\n"
        result += "UID:%s@iphone\n" % record.id

        # contact groups
        children = self.data_class.get_children_of_record_by_type(record, iPhoneGroupRecordEntity)
        if len(children) > 0:
            categories = ""
            for child in children:
                if categories != "":
                    categories += ","
                categories += child.data.name
            result += "CATEGORIES:%s\n" % (categories)

        if record.has_value("display as company"):
            if record.data.display_as_company == "person":
                result += "N:%s;%s\n" % (record.data.last_name, record.data.first_name)
                result += "FN:%s %s\n" % (record.data.first_name, record.data.last_name)

        if record.has_value("company name"):
            result += "ORG:%s;\n" % (record.data.company_name)

        children = self.data_class.get_children_of_record_by_type(record, iPhonePhoneNumberRecordEntity)
        for child in children:
            teltype = child.data.type.upper()
            # MobileSync sends "mobile" for phones, which according to RFCs is wrong
            if teltype == "MOBILE":
                teltype = "CELL"
            result += "TEL;%s:%s\n" % (teltype, child.data.value)

        children = self.data_class.get_children_of_record_by_type(record, iPhoneStreetAddressRecordEntity)
        for child in children:
            result += "ADR;%s:" % (child.data.type.upper())
            result += ";;%s;" % (child.data.street)
            result += "%s;%s;%s;" % (child.data.city, child.data.country_code, child.data.postal_code)
            result += "%s\n" % (child.data.country)

        children = self.data_class.get_children_of_record_by_type(record, iPhoneEMailAddressRecordEntity)
        for child in children:
            result += "EMAIL;TYPE=%s:%s\n" % (child.data.type.upper(), child.data.value)

        children = self.data_class.get_children_of_record_by_type(record, iPhoneURLRecordEntity)
        for child in children:
            result += "URL:%s\n" % (child.data.value)

        children = self.data_class.get_children_of_record_by_type(record, iPhoneDateRecordEntity)
        for child in children:
            t = child.data.type
            date_str = time.strftime("%Y-%m-%d", time.localtime(time.mktime(time.strptime(child.data.value, "%Y-%m-%dT%H:%M:%SZ"))+ODD_EPOCH))
            if t == "anniversary":
                result += "X-EVOLUTION-ANNIVERSARY:%s\n" % (date_str)
            elif t == "birthday":
                result += "BDAY:%s\n" % (date_str)

        if 'image' in record.data:
            result += "PHOTO;ENCODING=BASE64;TYPE=JPEG:"
            result += base64.b64encode(record.data['image']) + "\n"

        if record.has_value("notes"):
            result += "NOTE:%s\n" % (record.data.notes)

        result += "END:VCARD"
        return result

