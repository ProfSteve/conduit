try:
    import gnomevfs
except ImportError:
    from gnome import gnomevfs # for maemo

import conduit.Vfs as Vfs
import conduit.platform

import logging
log = logging.getLogger("Settings")

class FileImpl(conduit.platform.File):
    SCHEMES = ("file://","http://","ftp://","smb://")
    def __init__(self, URI):
        self._URI = gnomevfs.URI(URI)
        self.close()

    def _open_file(self):
        if not self.triedOpen:
            self.triedOpen = True
            self.fileExists = gnomevfs.exists(self._URI)
            
    def _get_file_info(self):
        self._open_file()
        #get_file_info works more reliably on remote vfs shares
        #than self.vfsFileHandle.get_file_info().
        if self.fileInfo == None:
            if self.exists():
                self.fileInfo = gnomevfs.get_file_info(self._URI, gnomevfs.FILE_INFO_DEFAULT)

    def get_text_uri(self):
        return str(self._URI)
        
    def get_local_path(self):
        if self.is_local():
            return self._URI.path
        else:
            return None
        
    def is_local(self):
        return self._URI.is_local
        
    def is_directory(self):
        self._get_file_info()
        return self.fileInfo.type == gnomevfs.FILE_TYPE_DIRECTORY
        
    def delete(self):
        #close the file and the handle so that the file info is refreshed
        self.close()
        result = gnomevfs.unlink(self._URI)
        
    def exists(self):
        self._open_file()
        return self.fileExists
        
    def set_mtime(self, timestamp=None, datetime=None):
        newInfo = gnomevfs.FileInfo()
        newInfo.mtime = timestamp
        
        try:
            gnomevfs.set_file_info(self._URI,newInfo,gnomevfs.SET_FILE_INFO_TIME)
            self.close()
            return timestamp
        except gnomevfs.NotSupportedError:
            #dunno what this is
            return None
        except gnomevfs.AccessDeniedError:
            #file is on readonly filesystem
            return None
        except gnomevfs.NotPermittedError:
            #file is on readonly filesystem
            return None
        
    def set_filename(self, filename):
        #gnomevfs doesnt seem to like unicode filenames
        filename = str(filename)
        oldname = str(self.get_filename())
    
        newInfo = gnomevfs.FileInfo()
        newInfo.name = filename
        
        olduri = self.get_text_uri()
        newuri = olduri.replace(oldname, filename)

        try:
            gnomevfs.set_file_info(self._URI,newInfo,gnomevfs.SET_FILE_INFO_NAME)
            #close so the file info is re-read
            self._URI = gnomevfs.URI(newuri)
            self.close()
        except gnomevfs.NotSupportedError:
            #dunno what this is
            return None
        except gnomevfs.AccessDeniedError:
            #file is on readonly filesystem
            return None
        except gnomevfs.NotPermittedError:
            #file is on readonly filesystem
            return None
        except gnomevfs.FileExistsError:
            #I think this is when you rename a file to its current name
            pass

        return newuri
        
    def get_mtime(self):
        self._get_file_info()
        try:
            return self.fileInfo.mtime
        except:
            return None

    def get_filename(self):
        self._get_file_info()
        return self.fileInfo.name
        
    def get_contents(self):
        return gnomevfs.read_entire_file(self.get_text_uri())
        
    def get_mimetype(self):
        self._get_file_info()
        try:
            return self.fileInfo.mime_type
        except ValueError:
            #Why is gnomevfs so stupid and must I do this for local URIs??
            return gnomevfs.get_mime_type(self.get_text_uri())

    def get_size(self):
        self._get_file_info()
        try:
            return self.fileInfo.size
        except:
            return None

    def close(self):
        self.fileInfo = None
        self.fileExists = False
        self.triedOpen = False

class FileTransferImpl(conduit.platform.FileTransfer):
    def __init__(self, source, dest):
        self._source = source._URI
        self._dest = gnomevfs.URI(dest)
        self._cancel_func = lambda : False
        
    def _xfer_progress_callback(self, info):
        #check if cancelled
        try:
            if self._cancel_func():
                log.info("Transfer of %s -> %s cancelled" % (info.source_name, info.target_name))
                return 0
        except Exception, ex:
            log.warn("Could not call gnomevfs cancel function")
            return 0
        return True
        
    def set_destination_filename(self, name):
        #if it exists and its a directory then transfer into that dir
        #with the new filename
        if gnomevfs.exists(self._dest):
            info = gnomevfs.get_file_info(self._dest, gnomevfs.FILE_INFO_DEFAULT)
            if info.type == gnomevfs.FILE_TYPE_DIRECTORY:
                #append the new filename
                self._dest = self._dest.append_file_name(name)
        
    def transfer(self, overwrite, cancel_func):
        self._cancel_func = cancel_func
    
        if overwrite:
            mode = gnomevfs.XFER_OVERWRITE_MODE_REPLACE
        else:
            mode = gnomevfs.XFER_OVERWRITE_MODE_SKIP

        log.debug("Transfering File %s -> %s" % (self._source, self._dest))

        #recursively create all parent dirs if needed
        parent = str(self._dest.parent)
        if not gnomevfs.exists(parent):
            Vfs.uri_make_directory_and_parents(parent)

        #Copy the file
        try:        
            result = gnomevfs.xfer_uri(
                        source_uri=self._source,
                        target_uri=self._dest,
                        xfer_options=gnomevfs.XFER_NEW_UNIQUE_DIRECTORY,
                        error_mode=gnomevfs.XFER_ERROR_MODE_ABORT,
                        overwrite_mode=mode,
                        progress_callback=self._xfer_progress_callback
                        )
            #FIXME: Check error
            return True, FileImpl(str(self._dest))
        except gnomevfs.InterruptedError:
            return False, None
        except Exception, e:
            log.warn("File transfer error: %s" % e)
            return False, None
    
    
    


            
