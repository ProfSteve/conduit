import subprocess
import signal
import os
import time
import shutil

server = subprocess.Popen(["./syncml-server.sh", "text/x-vcalendar", "Calendar", "calendar"], cwd="test/python-tests")

# no way to tell syncml-ds-tool is running :(
time.sleep(1)

#common sets up the conduit environment
from common import *

import conduit.datatypes.File as File
import conduit.utils as Utils

#setup the conduit
test = SimpleSyncTest()
sourceW = test.get_dataprovider("FolderTwoWay")
sinkW = test.get_dataprovider("SyncmlEventsTwoWay")
test.prepare(sourceW, sinkW)
test.set_two_way_policy({"conflict":"ask","deleted":"ask"})

#tempdir
tempdir = Utils.new_tempdir()
for f in get_files_from_data_dir("*.ical"):
    shutil.copy(f, tempdir)

#configure the source and sink
config = {}
config["folder"] = "file://" + tempdir
config["folderGroupName"] = "Tomboy"
test.configure(source=config)

#check they refresh ok
#test.refresh()
#a = test.get_source_count()
#ok("Got notes to sync (%s)" % a, a > 0)

#sync
test.set_two_way_sync(True)
test.sync()
#a,b = test.sync()
#abort,error,conflict = test.get_sync_result()
#ok("Sync completed", abort == False)
#ok("All notes transferred (%s,%s)" % (a,b), a == b)

os.kill(server.pid, signal.SIGINT)

finished()
