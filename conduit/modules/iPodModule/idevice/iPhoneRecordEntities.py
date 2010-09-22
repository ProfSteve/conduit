#! /usr/bin/env python

from plist import *
from imobiledevice import *

import sys, re, time, datetime

''' Record Entity Classes '''

class iPhoneRecordEntityData(dict):
    def __getattr__(self, name):
        nname = name.replace("_", " ")
        if nname in self:
            return self[nname].replace("\n", '\\n')
        return ""

class iPhoneRecordEntityBase():
    def __init__(self, data_storage=None):
        """
        :param data_storage: The data storage model with which this record is
            associated.
        """
        self.id = ''
        self.data = iPhoneRecordEntityData()
        self.parent_ids = []
        self.data_storage = data_storage

    def has_parents(self):
        return (len(self.parent_ids) > 0)

    def is_parent(self, parent):
        return (parent.id in self.parent_ids)

    def has_value(self, key):
        return (key in self.data)

class iPhoneCalendarRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.calendars.Calendar"

class iPhoneEventRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.calendars.Event"

class iPhoneDisplayAlarmRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.calendars.DisplayAlarm"

class iPhoneAudioAlarmRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.calendars.AudioAlarm"

class iPhoneRecurrenceRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.calendars.Recurrence"

class iPhoneAttendeeRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.calendars.Attendee"

class iPhoneOrganizerRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.calendars.Organizer"

class iPhoneBookmarkRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.bookmarks.Bookmark"

class iPhoneFolderRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.bookmarks.Folder"

class iPhoneContactRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.contacts.Contact"

class iPhoneGroupRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.contacts.Group"

class iPhoneStreetAddressRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.contacts.Street Address"

class iPhoneEMailAddressRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.contacts.EMail Address"

class iPhonePhoneNumberRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.contacts.Phone Number"

class iPhoneURLRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.contacts.URL"

class iPhoneRelatedNameRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.contacts.Related Name"

class iPhoneIMRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.contacts.IM"

class iPhoneDateRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.contacts.Date"

class iPhoneAccountRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.mail.Account"

class iPhoneNoteRecordEntity(iPhoneRecordEntityBase):
    name = "com.apple.mail.Note"

