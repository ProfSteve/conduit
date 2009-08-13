import os.path
from gettext import gettext as _
import logging
log = logging.getLogger("modules.File")

import conduit
import conduit.dataproviders.DataProvider as DataProvider
import conduit.dataproviders.DataProviderCategory as DataProviderCategory
import conduit.dataproviders.File as FileDataProvider
import conduit.dataproviders.SimpleFactory as SimpleFactory
import conduit.dataproviders.AutoSync as AutoSync
import conduit.utils as Utils
import conduit.Vfs as Vfs

MODULES = {
    "FileSource" :              { "type": "dataprovider" },
    "FolderTwoWay" :            { "type": "dataprovider" },
}

class FileSource(FileDataProvider.FileSource):

    _name_ = _("Files")
    _description_ = _("Source for synchronizing multiple files")
    _configurable_ = True

    def __init__(self, *args):
        FileDataProvider.FileSource.__init__(self)
        self.file_configurator = None
        self.files = None
        self.folders = None
        self.update_configuration(
            files_and_folders = ({'files':[], 'folders':[]}, self._set_files_folders, self._get_files_folders)
        )
        
    def _set_files_folders(self, value):
        for f in value['files']:
            self._add_file(f)
        for folder in value['folders']:
            folder, group = folder
            self._add_folder(folder, group)

    def get_config_container(self, configContainerKlass, name, icon, configurator):
        if not self.file_configurator:
            Utils.dataprovider_add_dir_to_path(__file__, "")
            import FileConfiguration
            self.file_configurator = FileConfiguration._FileSourceConfigurator(self, configurator, self.db)

            self.file_configurator.name = name
            self.file_configurator.icon = icon
            self.file_configurator.connect('apply', self.config_apply)
            self.file_configurator.connect('cancel', self.config_cancel)
            self.file_configurator.connect('show', self.config_show)
            self.file_configurator.connect('hide', self.config_hide)

        return self.file_configurator
    
    def _get_files_folders(self):
        files = []
        folders = []
        for uri,ftype,group in self.db.select("SELECT URI,TYPE,GROUP_NAME FROM config"):
            if ftype == FileDataProvider.TYPE_FILE:
                files.append(uri)
            else:
                folders.append((uri,group))
        return {'files': files, 'folders':folders}
    
    def get_files(self):
        self._get_files_folders(get_files = True)

    def get_folders(self):
        self._get_files_folders(get_folders = True)        

    def get_UID(self):
        return Utils.get_user_string()

class FolderTwoWay(FileDataProvider.FolderTwoWay, AutoSync.AutoSync):
    """
    TwoWay dataprovider for synchronizing a folder
    """

    _name_ = _("Folder")
    _description_ = _("Synchronize folders")
    _configurable_ = True

    DEFAULT_FOLDER = "file://"+os.path.expanduser("~")
    DEFAULT_GROUP = "Home"
    DEFAULT_HIDDEN = False
    DEFAULT_COMPARE_IGNORE_MTIME = False
    DEFAULT_FOLLOW_SYMLINKS = False

    def __init__(self, *args):
        FileDataProvider.FolderTwoWay.__init__(self,
                self.DEFAULT_FOLDER,
                self.DEFAULT_GROUP,
                self.DEFAULT_HIDDEN,
                self.DEFAULT_COMPARE_IGNORE_MTIME,
                self.DEFAULT_FOLLOW_SYMLINKS
                )
        self.update_configuration(
            folder = self.DEFAULT_FOLDER,
            includeHidden = self.DEFAULT_HIDDEN,
            compareIgnoreMtime = self.DEFAULT_COMPARE_IGNORE_MTIME,
            followSymlinks = self.DEFAULT_FOLLOW_SYMLINKS,
        )     
        AutoSync.AutoSync.__init__(self)

        self._monitor = Vfs.FileMonitor()
        self._monitor.connect("changed", self._monitor_folder_cb)

        self.update_configuration(
            folder = (self.DEFAULT_FOLDER, self._set_folder, lambda: self.folder),
            includeHidden = self.DEFAULT_HIDDEN,
            compareIgnoreMtime = self.DEFAULT_COMPARE_IGNORE_MTIME,
            followSymlinks = self.DEFAULT_FOLLOW_SYMLINKS
        )

    def __del__(self):
        self._monitor.cancel()

    def _set_folder(self, f):
        log.debug("Setting folder: %s" % f)
        self.folder = f
        self._monitor.add(f, self._monitor.MONITOR_DIRECTORY)

    def config_setup(self, config):
        config.add_item("Select folder", "filebutton", order = 1,
            config_name = "folder",
            directory = True,
        )
        config.add_section("Advanced")
        config.add_item("Include hidden files", "check", config_name = "includeHidden")
        config.add_item("Ignore file modification times", 'check', config_name = "compareIgnoreMtime")
        config.add_item("Follow symbolic links", 'check', config_name = "followSymlinks")
            
    def get_UID(self):
        return self.folder
        
    def get_name(self):
        return Vfs.uri_get_filename(self.folder)

    def _monitor_folder_cb(self, sender, event_uri, event):
        """
        Called when a file in the current folder is changed, added or deleted
        """
        # supported events = CHANGED, DELETED, CREATED
        if event == self._monitor.MONITOR_EVENT_CREATED:
            self.handle_added(event_uri)
        elif event == self._monitor.MONITOR_EVENT_CHANGED:
            self.handle_modified(event_uri)
        elif event == self._monitor.MONITOR_EVENT_DELETED:
            self.handle_deleted(event_uri)

