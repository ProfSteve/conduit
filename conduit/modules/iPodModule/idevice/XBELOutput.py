#! /usr/bin/env python

from plist import *
from imobiledevice import *

from iPhoneRecordEntities import *

import sys, re, time, datetime, base64

class XBELOutput():
    XBEL_DOC = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xbel PUBLIC "+//IDN python.org//DTD XML Bookmark Exchange Language 1.0//EN//XML" "http://pyxml.sourceforge.net/topics/dtds/xbel-1.0.dtd">
<xbel version="1.0">\n%s\n</xbel>"""

    INDENT_CHAR = "\t"

    def __init__(self, data_class):
        self.data_class = data_class

    def serialize(self):
        result = ""

        # get all bookmarks and folders
        bookmark_storage = self.data_class.get_storage_for_entity(iPhoneBookmarkRecordEntity)
        folder_storage = self.data_class.get_storage_for_entity(iPhoneFolderRecordEntity)
        self.storage = {}
        self.storage.update(folder_storage)
        self.storage.update(bookmark_storage)
        self.l = len(self.storage)

        result = self._to_bookmarks()
        return self.XBEL_DOC % (result)

    def _to_bookmarks(self, parent_record=None, indent=""):
        result = ""
        skip = 0
        for k, i in self.storage.iteritems():
            if i.has_parents():
                if not parent_record:
                    continue
                elif not i.is_parent(parent_record):
                    continue
            elif parent_record:
                continue

            if skip > 0 and skip < self.l:
                result += "\n"
            result += self._to_bookmark(i, indent)
            skip += 1
        return result

    def _record_has_children(self, record):
        for k, i in self.storage.iteritems():
            if i.is_parent(record):
                return True
        return False

    def _to_bookmark(self, record, indent=""):
        result = ""
        bookmark_type = record.name.rsplit(".")[-1].lower()
        result += "%s<%s id=\"%s\"" % (indent, bookmark_type, record.id)
        if isinstance(record, iPhoneBookmarkRecordEntity):
            result += " href=\"%s\"" % (record.data.url)
        result += ">\n"
        result += "%s<title>%s</title>\n" % (indent, record.data.name)

        # recurse for parents
        if self._record_has_children(record):
            result += self._to_bookmarks(record, indent + self.INDENT_CHAR)
            result += "\n"

        result += "%s</%s>" % (indent, bookmark_type)
        return result

