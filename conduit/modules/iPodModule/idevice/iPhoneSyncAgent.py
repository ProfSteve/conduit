#! /usr/bin/env python

from plist import *
from imobiledevice import *

import sys, re, time, datetime

''' Synchronization Classes '''

class iPhoneSyncAgent():
    EMPTY_PARAM = "___EmptyParameterString___"
    SYNC_TYPES = [
        "SDSyncTypeFast",
        "SDSyncTypeSlow",
        "SDSyncTypeReset"
    ]
    _phone = None
    _lckd = None
    _mobile_sync = None

    def __init__(self):
        pass

    def connect(self, uuid=None):
        self._phone = idevice()
        if uuid:
            if not self._phone.init_device_by_uuid(uuid):
                print "Couldn't connect to iPhone/iPod touch with uuid %s." % (uuid)
                return False
        else:
            if not self._phone.init_device():
                print "Couldn't connect to iPhone/iPod touch."
                return False

        self._lckd = self._phone.get_lockdown_client()
        if not self._lckd:
            print "Lockdown session couldn't be established."
            return False

        self._mobile_sync = self._lckd.get_mobilesync_client()
        if not self._mobile_sync:
            print "Mobilesync session couldn't be established."
            return False

        # Lockdown is not needed anymore and has to be closed or it times out
        del self._lckd

        return True

    def get_uuid(self):
        self._phone.get_uuid()

    def set_debug_level(self, mask):
        self._phone.set_debug_level(1)

    def synchronize(self, sync_type):
        # we request just the changes only on fast sync
        if sync_type == self.SYNC_TYPES[0]:
            self.get_changes_from_device()
        else:
            self.get_all_records_from_device()

        # from device
        if not self.receive_changes_from_device():
            return False

        # switch sync direction
        self.ping()

        # to device
        # FIXME: Functionality to send records to device
        #if not self.send_changes_to_device():
        #    return False

        return True

    def receive_changes_from_device(self):
        msg = self._get_next_message()
        while not self._is_device_ready_to_receive_changes(msg):
            if not self.sync_data_storage.commit_records(msg):
                self.cancel_session("Could not commit changes from device.")
                return False
            self.acknowledge_changes()
            msg = self._get_next_message()
        return True

    def send_changes_to_device(self):
        msg = self.sync_data_storage.get_next_change_for_device()
        while msg:
            self._mobile_sync.send(msg)

            response = self._mobile_sync.receive()
            if response[0].get_value() == "SDMessageRemapRecordIdentifiers":
                self.sync_data_storage.remap_record_identifiers(response)

        return True

    def set_data_storage(self, sync_data_storage):
        self.sync_data_storage = sync_data_storage

    def start_session(self):
        # Start the synchronization
        start_sync_msg = Array()
        start_sync_msg.append( String("SDMessageSyncDataClassWithDevice") )
        start_sync_msg.append( String(self.sync_data_storage.get_name()) )

        device_anchor = self.sync_data_storage.get_device_anchor()
        host_anchor = self.sync_data_storage.get_host_anchor()

        # exchange anchors
        start_sync_msg.append( String(device_anchor) )
        start_sync_msg.append( String(host_anchor) )

        start_sync_msg.append( Integer(self.sync_data_storage.get_version() ) )
        start_sync_msg.append( String(self.EMPTY_PARAM) )
        self._mobile_sync.send(start_sync_msg)

        response = self._mobile_sync.receive()
        if response[0].get_value() == "SDMessageSyncDataClassWithComputer":
            sync_type = response[4].get_value()
            if sync_type in self.SYNC_TYPES:
                # set new anchor for next sync
                new_device_anchor = response[2].get_value()
                self.sync_data_storage.set_host_anchor(host_anchor)
                self.sync_data_storage.set_device_anchor(new_device_anchor)
                return sync_type

        if response[0].get_value() == "SDMessageRefuseToSyncDataClassWithComputer":
            print "Device refused synchronization. Reason: %s" % (response[2].get_value())

        self._report_if_device_cancelled_session(response)

        return False

    # FIXME: send: {SDMessageProcessChanges, com.apple.Bookmarks, SyncDeviceLinkEntityNamesKey, SyncDeviceLinkAllRecordsOfPulledEntityTypeSentKey, com.apple.bookmarks.Folder}
    # FIXME: recv: {SDMessageRemapRecordIdentifiers, com.apple.Bookmarks, ___EmptyParameterString___}

    def get_changes_from_device(self):
        msg = Array()
        msg.append( String("SDMessageGetChangesFromDevice") )
        msg.append( String(self.sync_data_storage.get_name()) )
        self._mobile_sync.send(msg)

    def get_all_records_from_device(self):
        msg = Array()
        msg.append( String("SDMessageGetAllRecordsFromDevice") )
        msg.append( String(self.sync_data_storage.get_name()) )
        self._mobile_sync.send(msg)

    def clear_all_records_on_device(self):
        msg = Array()
        msg.append( String("SDMessageClearAllRecordsOnDevice") )
        msg.append( String(self.sync_data_storage.get_name()) )
        self._mobile_sync.send(msg)

        response = self._mobile_sync.receive()
        if response[0].get_value() == "SDMessageDeviceWillClearAllRecords":
            return True
        return False

    def _get_next_message(self):
        msg = self._mobile_sync.receive()
        return msg

    def _is_device_ready_to_receive_changes(self, msg):
        if msg[0].get_value() == "SDMessageDeviceReadyToReceiveChanges":
            return True
        return False

    def _report_if_device_cancelled_session(self, msg):
        if msg[0].get_value() == "SDMessageCancelSession":
            print "Device cancelled session. Reason: %s" % (msg[2].get_value())

    def acknowledge_changes(self):
        msg = Array()
        msg.append( String("SDMessageAcknowledgeChangesFromDevice") )
        msg.append( String(self.sync_data_storage.get_name()) )
        self._mobile_sync.send(msg)

    def cancel_session(self, reason):
        msg = Array()
        msg.append( String("SDMessageCancelSession") )
        msg.append( String(self.sync_data_storage.get_name()) )
        msg.append( String(reason) )
        self._mobile_sync.send(msg)

    def finish_session(self):
        msg = Array()
        msg.append( String("SDMessageFinishSessionOnDevice") )
        msg.append( String(self.sync_data_storage.get_name()) )
        self._mobile_sync.send(msg)

        response = self._mobile_sync.receive()
        if response[0].get_value() == "SDMessageDeviceFinishedSession":
            return True

        self._report_if_device_cancelled_session(response)

        return False

    def ping(self):
        msg = Array()
        msg.append( String("DLMessagePing") )
        msg.append( String("Preparing to get changes for device") )
        self._mobile_sync.send(msg)

    def disconnect(self):
        msg = Array()
        msg.append( String("DLMessageDisconnect") )
        msg.append( String("All done, thanks for the memories") )
        self._mobile_sync.send(msg)

    def __del__(self):
        if self._mobile_sync:
            del(self._mobile_sync)
        if self._lckd:
            del(self._lckd)
        if self._phone:
            del(self._phone)

