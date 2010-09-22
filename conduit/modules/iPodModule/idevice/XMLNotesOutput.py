#! /usr/bin/env python

from plist import *
from imobiledevice import *

from iPhoneRecordEntities import *

import sys, re, time, datetime, base64

ODD_EPOCH = 978307200 # For some reason Apple decided the epoch was on a different day?

class XMLNotesOutput():
    XML_DOC = """<?xml version="1.0" encoding="UTF-8"?>
<notes>\n%s\n</notes>"""

    def __init__(self, data_class):
        self.data_class = data_class

    def serialize(self):
        storage = self.data_class.get_storage_for_entity(iPhoneNoteRecordEntity)
        l = len(storage)

        result = ''
        skip = 0
        for k, i in storage.iteritems():
            if skip > 0 and skip < l:
                result += "\n"
            result += self._to_html_note(i)
            skip += 1
        return self.XML_DOC % (result)

    def _format_date(self, date):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.mktime(time.strptime(date, "%Y-%m-%d %H:%M:%S"))+ODD_EPOCH))

    def _to_html_note(self, record):
        result = "\t<note id=\"%s\" created=\"%s\" modified=\"%s\">\n" % (record.id, self._format_date(record.data.dateCreated), self._format_date(record.data.dateModified))
        result += "\t\t<author>%s</author>\n" % (record.data.author)
        result += "\t\t<subject>%s</subject>\n" % (record.data.subject)
        result += "\t\t<content type=\"%s\"><![CDATA[%s]]></content>\n" % (record.data.contentType, record.data.content)
        result += "\t</note>"

        return result

