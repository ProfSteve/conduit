# -*- coding: utf-8 -*-
import logging
log = logging.getLogger("modules.iPhone")

import conduit
import conduit.dataproviders.DataProvider as DataProvider
import conduit.datatypes.DataType as DataType
import conduit.utils as Utils
import conduit.Exceptions as Exceptions

import conduit.datatypes.Contact as Contact
import conduit.datatypes.Event as Event
import conduit.datatypes.Event as Bookmark

from iPhoneDataStorage import *
from iPhoneSyncAgent import *
from vCardOutput import *
from iCalendarOutput import *

class iPhoneBaseTwoWay(DataProvider.TwoWay):
    def __init__(self, *args):
        self.agent = iPhoneSyncAgent()
        self.uuid = str(args[0])
        self.model = str(args[1])
        if self.agent.connect(self.uuid):
            log.info("Connected to %s with uuid %s" % (self.model, self.uuid))
        else:
            log.info("Failed to connect to iPhone/iPod Touch")

    def uninitialize(self):
        self.agent.disconnect()

    def _replace_data(self, LUID, data):
        #FIXME implement replace data
        return LUID

    def _put_data(self, data):
        #FIXME implement put data
        i = 0
        return "%s@iphone-%s" % (i, self._phone_uuid)

    def _get_data(self, LUID):
        storage = self.data_class.get_storage_for_entity(self.storage_entity)
        return storage[LUID.split("@iphone")[0]]

    def _data_exists(self, LUID):
        if (None != _get_data(LUID)):
            return true
        return false

    def refresh(self):
        DataProvider.TwoWay.refresh(self)
        self._refresh()

    def _refresh(self):
        self.agent.set_data_storage(self.data_class);
        if self.agent.start_session():
            self._phone_uuid = self.agent._phone.get_uuid()
            self.agent.synchronize()
        self.agent.finish_session()

    def get_all(self):
        res = []
        storage = self.data_class.get_storage_for_entity(self.storage_entity)
        for k, i in storage.iteritems():
            res.append("%s@iphone-%s" % (i.id, self._phone_uuid))
        return res

    def put(self, data, overwrite, LUID=None):
        DataProvider.TwoWay.put(self, data, overwrite, LUID)
        if overwrite and LUID:
            LUID = self._replace_data(LUID, data)
        else:
            if LUID and self._data_exists(LUID):
                oldData = self._get_data(LUID)
                comp = data.compare(oldData)
                #Possibility 1: If LUID != None (i.e this is a modification/update of a
                #previous sync, and we are newer, the go ahead an put the data
                if LUID != None and comp == conduit.datatypes.COMPARISON_NEWER:
                    LUID = self._replace_data(LUID, data)
                #Possibility 3: We are the same, so return either rid
                elif comp == conduit.datatypes.COMPARISON_EQUAL:
                    return oldData.get_rid()
                #Possibility 2, 4: All that remains are conflicts
                else:
                    raise Exceptions.SynchronizeConflictError(comp, data, oldData)
            else:
                #Possibility 5:
                LUID = self._put_data(data)

        #now return the rid
        if not LUID:
            raise Exceptions.SyncronizeError("Error putting/updating data")
        else:
            return self._get_data(LUID).get_rid()



class iPhoneContactsTwoWay(iPhoneBaseTwoWay):
    """
    Contact syncing for iPhone and iPod Touch
    """

    _name_ = "iPhone Contacts"
    _description_ = "iPhone and iPod Touch Contact Dataprovider"
    _category_ = conduit.dataproviders.CATEGORY_MISC
    _module_type_ = "twoway"
    _in_type_ = "contact"
    _out_type_ = "contact"
    _icon_ = "contact-new"

    def __init__(self, *args):
        iPhoneBaseTwoWay.__init__(self, *args)
        DataProvider.TwoWay.__init__(self)
        self.selectedGroup = None
        self.data_class = iPhoneContactsDataStorage()
        self.storage_entity = iPhoneContactRecordEntity

    def get(self, LUID):
        DataProvider.TwoWay.get(self, LUID)
        c = None
        i = self._get_data(LUID)
        if (None != i):
            vcard = vCardOutput(self.data_class)
            c = Contact.Contact()
            c.set_from_vcard_string(vcard._to_vcard(i))
        return c

    def get_UID(self):
        return "iPhoneContactsTwoWay"

    def get(self, LUID):
        # FIXME: This should be rewritten to translate like iPhoneCalendarTwoWay
        # After doing that we can get rid of this method.
        DataProvider.TwoWay.get(self, LUID)
        c = None
        i = self._get_data(LUID)
        if (None != i):
            vcard = vCardOutput(self.data_class)
            c = Contact.Contact()
            c.set_from_vcard_string(vcard._to_vcard(i))
        return c

class iPhoneConduitEvent(DataType.DataType):
    _name_ = 'event/iphone'

    def __init__(self, record):
        super(iPhoneConduitEvent, self).__init__()
        self.record = record
    
    def get_hash(self):
        return hash("".join(self.record.data.values()))

    def get_ical_string(self):
        formatter = iCalendarOutput(self.record.data_storage)
        return formatter.to_vevent(self.record)

    def set_from_ical_string(self, string):
        pass

class iPhoneCalendarsTwoWay(iPhoneBaseTwoWay):
    """
    Contact syncing for iPhone and iPod Touch
    """

    _name_ = "iPhone Calendar"
    _description_ = "iPhone and iPod Touch Calendar Dataprovider"
    _category_ = conduit.dataproviders.CATEGORY_MISC
    _module_type_ = "twoway"
    _in_type_ = "event/iphone"
    _out_type_ = "event/iphone"
    _icon_ = "appointment-new"
    _configurable_ = True

    def __init__(self, *args):
        iPhoneBaseTwoWay.__init__(self, *args)
        DataProvider.TwoWay.__init__(self)
        self.data_class = iPhoneCalendarsDataStorage()
        self.storage_entity = iPhoneEventRecordEntity

        self.update_configuration(
            _calendarId = ""
        )

    def get_UID(self):
        # FIXME: This should include the UUID of the phone as well
        return "iPhoneCalendarsTwoWay-%s" % (self._calendarId)

    # Implement this for faster syncs
    #def get_changes(self):
    #    return (new, changed, deleted)

    def get_all(self):
        """
        Returns a list of all event ids for the configured calendar.
        """
        res = []
        
        events = self.data_class.get_children_of_record_by_type(self.calendar, self.storage_entity)
        for i in events:
            res.append("%s@iphone-%s" % (i.id, self._phone_uuid))
        return res
    
    def get(self, LUID):
        """
        Returns an iPhoneConduitEvent for a given LUID.
        """
        DataProvider.TwoWay.get(self, LUID)
        record = self._get_data(LUID)
        e = None
        if record is not None:
            e = iPhoneConduitEvent(record)
        return e

    def _calendar_names(self):
        """
        Returns a dictionary of calendar ids to their names.
        """
        if not hasattr(self, '_calendarNames'):
            self._calendarNames = []
            
            # Collect the calendars from the phone
            self._refresh()
            calendars = self.data_class.get_storage_for_entity(iPhoneCalendarRecordEntity).values()
            for calendar in calendars:
                self._calendarNames.append((calendar.id, calendar.data.title))
        
        return self._calendarNames

    @property
    def calendar(self):
        """
        Returns the currently configured iPhoneCalendarRecordEntity
        """
        if not hasattr(self, '_calendarNames'):
            self._refresh()

        calendars = self.data_class.get_storage_for_entity(iPhoneCalendarRecordEntity).values()
        matching_calendars = [c for c in calendars if c.id == self._calendarId]
        
        if matching_calendars:
            return matching_calendars[0]
        else:
            return calendars[0]

    def config_setup(self, config):
        config.add_section("Calendar Name")
        config.add_item("Calendar", "combo", config_name = "_calendarId", choices = self._calendar_names())

