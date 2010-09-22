#! /usr/bin/env python

from plist import *
from imobiledevice import *

from iPhoneRecordEntities import *

import sys, re, time, datetime

ODD_EPOCH = 978307200 # For some reason Apple decided the epoch was on a different day?

class iCalendarOutput():
    def __init__(self, data_class):
        self.data_class = data_class

    def serialize(self):
        storage = self.data_class.get_storage_for_entity(iPhoneCalendarRecordEntity)
        l = len(storage)

        result = ""
        skip = 0
        for key, i in storage.iteritems():
            if skip > 0 and skip < l:
                result += "\n"
            result += "BEGIN:VCALENDAR\n"
            result += "VERSION:2.0\n"
            result += "PRODID:-//iphonesync//NONSGML %s//EN\n" % (i.data.title)
            result += "X-WR-CALNAME:%s\n" % (i.data.title)
            events = self.data_class.get_children_of_record_by_type(i, iPhoneEventRecordEntity)
            for event in events:
                result += self.to_vevent(event) + "\n"
            result += "END:VCALENDAR"
            skip += 1
        return result

    def _format_date(self, date_format, date):
        return time.strftime(date_format, time.localtime(time.mktime(time.strptime(date, "%Y-%m-%d %H:%M:%S"))+ODD_EPOCH))

    def to_vevent(self, record):
        result = "BEGIN:VEVENT\n"
        result += "UID:%s@iphone\n" % record.id

        # Determine if it is an all day event
        date_format = ":%Y%m%dT%H%M%S"

        if record.has_value("all day"):
            date_format = ";VALUE=DATE:%Y%m%d"

        # Handle all of the event information
        result += "DTSTART%s\n" % (self._format_date(date_format, record.data.start_date))
        result += "DTEND%s\n" % (self._format_date(date_format, record.data.end_date))
        summary = record.data.summary
        if summary != "":
            result += "SUMMARY:%s\n" % (summary)
        if record.has_value("location"):
            result += "LOCATION:%s\n" % (record.data.location)
        if record.has_value("description"):
            result += "DESCRIPTION:%s\n" % (record.data.description)

        # Handle recurrences
        rrule = ""
        children = self.data_class.get_children_of_record_by_type(record, iPhoneRecurrenceRecordEntity)
        for recurrence in children:
            v = recurrence.data.frequency
            if v != '':
                rrule += "FREQ=%s;" % (v.upper())
            v = recurrence.data.interval
            if v != '':
                rrule += "INTERVAL=%s;" % (v)
            v = recurrence.data.bymonth
            if v != '':
                rrule += "BYMONTH=%s;" % (v)
            v = recurrence.data.bymonthday
            if v != '':
                recurrence += "BYMONTHDAY=%s;" % (v)
        if rrule != "":
            result += "RRULE:%s\n" % (rrule[0:-1])

        # Handle alarms
        children = self.data_class.get_children_of_record_by_type(record, iPhoneDisplayAlarmRecordEntity)
        for child in children:
            result += self._to_valarm(child, summary)

        children = self.data_class.get_children_of_record_by_type(record, iPhoneAudioAlarmRecordEntity)
        for child in children:
            result += self._to_valarm(child, summary)

        result += "END:VEVENT"

        return result

    def _to_valarm(self, record, summary=""):
        result = "BEGIN:VALARM\n"
        if isinstance(record, iPhoneDisplayAlarmRecordEntity):
            result += "ACTION:DISPLAY\n"
        elif isinstance(record, iPhoneAudioAlarmRecordEntity):
            result += "ACTION:AUDIO\n"
        if summary != "":
            result += "DESCRIPTION:%s\n" % (summary)
        if record.has_value("triggerduration"):
            # Convert from the silly unsigned int represent a signed int
            time_before = int(record.data.triggerduration)
            minutes_before = ((2**64) - time_before) / 60
            result += "TRIGGER;VALUE=DURATION;RELATED=START:-P%sM\n" % (minutes_before)
        result += "END:VALARM\n"

        return result

