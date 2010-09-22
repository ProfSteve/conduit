#! /usr/bin/env python

from plist import *
from imobiledevice import *

from iPhoneRecordEntities import *

import sys, re, time, datetime, base64

''' Data Classes '''

RECORD_ENTITY_NAME_KEY = "com.apple.syncservices.RecordEntityName"

RECORD_ENTITIES = {
    'com.apple.contacts.Contact': iPhoneContactRecordEntity,
    'com.apple.contacts.Group': iPhoneGroupRecordEntity,
    'com.apple.contacts.Email Address': iPhoneEMailAddressRecordEntity,
    'com.apple.contacts.Phone Number': iPhonePhoneNumberRecordEntity,
    'com.apple.contacts.Street Address': iPhoneStreetAddressRecordEntity,
    'com.apple.contacts.URL': iPhoneURLRecordEntity,
    'com.apple.contacts.Related Name': iPhoneRelatedNameRecordEntity,
    'com.apple.contacts.IM': iPhoneIMRecordEntity,
    'com.apple.contacts.Date': iPhoneDateRecordEntity,
    'com.apple.bookmarks.Bookmark': iPhoneBookmarkRecordEntity,
    'com.apple.bookmarks.Folder': iPhoneFolderRecordEntity,
    'com.apple.calendars.Calendar': iPhoneCalendarRecordEntity,
    'com.apple.calendars.Event': iPhoneEventRecordEntity,
    'com.apple.calendars.DisplayAlarm': iPhoneDisplayAlarmRecordEntity,
    'com.apple.calendars.AudioAlarm': iPhoneAudioAlarmRecordEntity,
    'com.apple.calendars.Recurrence': iPhoneRecurrenceRecordEntity,
    'com.apple.calendars.Attendee': iPhoneAttendeeRecordEntity,
    'com.apple.calendars.Organizer': iPhoneOrganizerRecordEntity,
    'com.apple.mail.Account': iPhoneAccountRecordEntity,
    'com.apple.notes.Note': iPhoneNoteRecordEntity
}

class iPhoneDataStorage():
    EMPTY_PARAM = "___EmptyParameterString___"

    name = None
    host_anchor = None
    device_anchor = None
    supported_entities = []
    storage = {}

    def __init__(self):
        # load supported entity types
        if len(self.supported_entities) > 0:
            index = 0
            for entity in self.supported_entities:
                self.storage[index] = {}
                index += 1

        self.device_anchor = self._get_default_anchor()

    def get_name(self):
        return self.name

    def get_version(self):
        return self.version

    def get_children_of_record_by_type(self, record, entity_class):
        """
        Returns a list of all the children of type entity class for the given
        record.
        """
        ids = self.get_storage_for_entity(entity_class)
        parents = []
        for k, i in ids.iteritems():
            if record.id in i.parent_ids:
                parents.append(i)
        return parents

    def get_storage_for_entity(self, entity_class):
        """
        Returns a dictionary containing all the elements of the type
        entity_class. The keys are the record ids and the values are the
        records themselves.
        """
        for index, i in enumerate(self.supported_entities):
            if (i != None) and (entity_class == RECORD_ENTITIES[i]):
                return self.storage[index]
            index += 1
        return {}

    def commit_records(self, node):
        # check message type
        if node[0].get_value() != "SDMessageProcessChanges":
            return False

        # check data storage name
        if node[1].get_value() != self.get_name():
            return False

        # make sure we got a dict node next
        if (node[2].get_type() == PLIST_STRING) and (node[2].get_value() == self.EMPTY_PARAM):
            # skip this record set since we got no change data
            return True
        elif node[2].get_type() != PLIST_DICT:
            return False

        records = node[2]
        for record_id in records:
            record_dict = records[record_id]

            # get entity name
            record_entity_name = record_dict[RECORD_ENTITY_NAME_KEY].get_value()

            # get storage
            storage = self.get_storage_for_entity(RECORD_ENTITIES[record_entity_name])

            # update or create record
            if record_id in storage:
                record = storage[record_id]
            else:
                record = RECORD_ENTITIES[record_entity_name](data_storage=self)
                record.id = record_id

            # map data
            for key_name in record_dict:
                value_node = record_dict[key_name]
                if key_name != RECORD_ENTITY_NAME_KEY:
                    if key_name in ["contact", "parent", "calendar", "owner", "members"]:
                        parents = value_node
                        for i in range(len(parents)):
                            record.parent_ids.append(parents[i].get_value())
                    elif value_node.get_type() in [PLIST_DATA, PLIST_UINT, PLIST_STRING, PLIST_DATE, PLIST_BOOLEAN]:
                        record.data[key_name] = str(value_node.get_value())

            # store record
            storage[record.id] = record

        return True

    def get_next_change_for_device(self):
        return None

    def remap_record_identifiers(self, plist):
        return True

    def _get_default_anchor(self, remote = True):
        return "%s-%s-Anchor" % (self.name.rsplit(".", 1)[1], ("Device" if remote else "Computer"))

    def get_device_anchor(self):
        return self.device_anchor

    def get_host_anchor(self):
        if not self.host_anchor:
            self.host_anchor = time.strftime("%Y-%m-%d %H:%M:%S %z")
        return self.host_anchor

    def set_device_anchor(self, anchor):
        self.device_anchor = anchor

    def set_host_anchor(self, anchor):
        self.host_anchor = anchor

class iPhoneContactsDataStorage(iPhoneDataStorage):
    name = "com.apple.Contacts"
    version = 106
    supported_entities = [
        'com.apple.contacts.Contact',
        'com.apple.contacts.Group',
        'com.apple.contacts.Email Address',
        'com.apple.contacts.Phone Number',
        'com.apple.contacts.Street Address',
        'com.apple.contacts.URL',
        'com.apple.contacts.Related Name',
        'com.apple.contacts.IM',
        'com.apple.contacts.Date'
    ]

class iPhoneBookmarksDataStorage(iPhoneDataStorage):
    name = "com.apple.Bookmarks"
    version = 102
    supported_entities = [
        'com.apple.bookmarks.Bookmark',
        'com.apple.bookmarks.Folder'
    ]

class iPhoneCalendarsDataStorage(iPhoneDataStorage):
    name = "com.apple.Calendars"
    version = 107
    supported_entities = [
        'com.apple.calendars.Calendar',
        'com.apple.calendars.Event',
        'com.apple.calendars.AudioAlarm',
        'com.apple.calendars.DisplayAlarm',
        'com.apple.calendars.Recurrence',
        'com.apple.calendars.Attendee',
        'com.apple.calendars.Organizer'
    ]

class iPhoneMailAccountsDataStorage(iPhoneDataStorage):
    name = "com.apple.MailAccounts"
    version = 102
    supported_entities = [
        'com.apple.mail.Account'
    ]

    def get_host_anchor(self):
        return self._get_default_anchor(False)

class iPhoneNotesDataStorage(iPhoneDataStorage):
    name = "com.apple.Notes"
    version = 102
    supported_entities = [
        'com.apple.notes.Note'
    ]

