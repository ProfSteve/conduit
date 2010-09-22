#! /usr/bin/env python

from plist import *
from imobiledevice import *

from iCalendarOutput import *
from vCardOutput import *
from XMLNotesOutput import *
from iPhoneDataStorage import *
from iPhoneSyncAgent import *
from XBELOutput import *

import sys, re, time, datetime, base64
from lxml import etree

# FIXME: The notification_proxy should be used to show sync screen on device

''' Main '''

class Application():
    def __init__(self):
        # init the data classes
        self.contacts = iPhoneContactsDataStorage()
        self.calendars = iPhoneCalendarsDataStorage()
        self.bookmarks = iPhoneBookmarksDataStorage()
        self.mailaccounts = iPhoneMailAccountsDataStorage()
        self.notes = iPhoneNotesDataStorage()

        self.supported_data_storage_types = [
            self.contacts,
            self.calendars,
            self.bookmarks,
            self.mailaccounts,
            self.notes
        ]

        if (("-h" in sys.argv) or ("--help" in sys.argv)):
            self.print_usage()
            sys.exit()

        if (len(sys.argv) < 2):
            print "ERROR: You must specify at least one data storage type."
            self.print_usage()
            sys.exit(1)

        # remove data classes not specified on command line
        sync_data_storage_types = []
        for data_storage in self.supported_data_storage_types:
            if data_storage.get_name() in sys.argv:
                sync_data_storage_types.append(data_storage)

        if len(sync_data_storage_types) == 0:
            print "ERROR: The data storage type you passed is not supported."
            self.print_usage()
            sys.exit(1)

        # create client for mobilesync message protocol
        uuid = None
        if ("-u" in sys.argv):
            uuid = sys.argv[sys.argv.index("-u") + 1]
        elif ("--uuid" in sys.argv):
            uuid = sys.argv[sys.argv.index("--uuid") + 1]

        agent = iPhoneSyncAgent()

        # try to connect to device and mobilesync service
        if not agent.connect(uuid):
            sys.exit(1)

        if ("-d" in sys.argv) or ("--debug" in sys.argv):
            agent.set_debug_level(1)

        # sync all data tyoes
        for data_storage in sync_data_storage_types:
            agent.set_data_storage(data_storage);
            sync_type = agent.start_session()
            if sync_type:
               if ("-c" in sys.argv) or ("--clear" in sys.argv):
                   if agent.clear_all_records_on_device():
                       print "Successfully cleared all records of %s from device." % (data_storage.get_name())
                   else:
                       print "ERROR: Failed to clear records of %s from device." % (data_storage.get_name())
               else:
                   agent.synchronize(sync_type)
            agent.finish_session()

        # disconnect from mobilesync (important, as it makes the SyncAgent quit)
        agent.disconnect()

        # FIXME: Just dump received records for testing purposes
        self.print_results()

    def print_usage(self):
        print "Usage: %s [OPTION]... [TYPE]..." % (sys.argv[0])
        print "Synchronize data TYPEs on an iPhone or iPod Touch with this computer."
        print ""
        print "Supported data storage TYPEs are:"
        for data_storage in self.supported_data_storage_types:
            print "  %s (version %d)" % (data_storage.get_name(), data_storage.get_version())
        print ""
        print "Options:"
        print "  -o, --output FILE\tSave received records to FILE"
        print "\t\t\tthe saved data will be saved as:"
        print "\t\t\t  vCard for contacts"
        print "\t\t\t  iCalendar for calendars"
        print "\t\t\t  XBEL for bookmarks"
        print "  -u, --uuid UUID\ttarget specifc device by UUID"
        print "  -c, --clear\t\tclear all records from device"
        print "  -d, --debug\t\tenable libiphone debug mode"
        print "  -h, --help\t\tdisplay this help and exit"

    def get_data_storage_type_by_name(self, name):
        for t in self.supported_data_storage_types:
            if t.get_name() == name:
                return t;
        return None

    def print_results(self):
        filename = None
        output = ""

        output_map = {
            'com.apple.Contacts': vCardOutput,
            'com.apple.Calendars': iCalendarOutput,
            'com.apple.Bookmarks': XBELOutput,
            'com.apple.MailAccounts': None,
            'com.apple.Notes': XMLNotesOutput
        }

        if ("-o" in sys.argv):
            filename = sys.argv[sys.argv.index("-o") + 1]
        elif ("--output" in sys.argv):
            filename = sys.argv[sys.argv.index("--output") + 1]

        for name, output_class in output_map.iteritems():
            if name in sys.argv:
               if output_class:
                   data_storage = self.get_data_storage_type_by_name(name)
                   output += output_class(data_storage).serialize()
               else:
                   print "WARNING: Output for type %s is not implemented." % (name)
                   continue

        if filename:
            f = open(filename, "wb")
            f.write( output )
            f.close()
        else:
            print output


if __name__ == '__main__':
    application = Application()

