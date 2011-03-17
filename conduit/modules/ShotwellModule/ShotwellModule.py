
import conduit
import conduit.dataproviders.DataProvider as DataProvider
import conduit.datatypes.Photo as Photo
import conduit.utils as Utils

import logging
log = logging.getLogger('modules.Shotwell')

from gettext import gettext as _

try:
    import shotwell
except ImportError:
    Utils.dataprovider_add_dir_to_path(__file__)
    import shotwell

if Utils.program_installed("shotwell"):
    MODULES = {
        "ShotwellDataProvider" : { "type": "dataprovider" }
    }
else:
    MODULES = {}
    log.info("Shotwell not installed")

def _flatten(lst):
    for elem in lst:
        if type(elem) in (tuple, list):
            for i in _flatten(elem):
                yield i
        else:
            yield elem

class ShotwellDataProvider(DataProvider.DataSource):

    _name_ = _('Shotwell')
    _description_ = _('Sync from your Shotwell photo library')
    _icon_ = 'shotwell'
    _category_ = conduit.dataproviders.CATEGORY_PHOTOS
    _module_type_ = 'source'
    _configurable_ = True
    _out_type_ = 'file/photo'

    _enabled = False
    _selected_tag_names = []
    _shotwell_photos = []

    def __init__(self, *args):
        DataProvider.DataSource.__init__(self)
        self.update_configuration(tags = ([], self.set_tags, self.get_tags))
        try:
            shotwell_db = shotwell.ShotwellDB()
            shotwell_db.close()
            self._enabled = True
        except:
            log.warn(_('Disabling Shotwell module, unable to open sqlite3 data source'))

    def initialize(self):
        DataProvider.DataSource.initialize(self)
        return self._enabled

    def set_tags(self, tags):
        self._selected_tag_names = map(lambda x: str(x), tags)
        log.debug('Configuring to sync tags: %s', str(self._selected_tag_names))

    def get_tags(self):
        return self._selected_tag_names

    def config_setup(self, config):
        shotwell_db = shotwell.ShotwellDB()
        config.add_section(_('Tags'))
        all_tag_names = map(lambda sTag: sTag.name, shotwell_db.tags())
        config.add_item(_('Tags'), 'list', config_name = 'tags', choices = all_tag_names)
        shotwell_db.close()

    def refresh(self):
        DataProvider.DataSource.refresh(self)
        shotwell_db = shotwell.ShotwellDB()
        tags = filter(lambda sTag: sTag.name in self._selected_tag_names, shotwell_db.tags())
        log.debug('Tags to sync:')
        if log.isEnabledFor(logging.DEBUG):
            for sTag in tags:
                log.debug('\t%s', str(sTag))
        tagged_photos = list(_flatten(map(lambda sTag: sTag.photoIDs, tags)))
        log.debug('Photo IDs for tags(%s): %s', str(tags), str(tagged_photos))
        log.debug('All Photo IDs: %s', map(lambda x: str(x.id), shotwell_db.photos()))
        self._shotwell_photos = filter(lambda sPhoto: str(sPhoto.id) in tagged_photos, shotwell_db.photos())
        log.debug('%i photos (from %i tags) to sync', len(self._shotwell_photos), len(tags))
        shotwell_db.close()

    def get_all(self):
        DataProvider.DataSource.get_all(self)
        return map(lambda sPhoto: str(sPhoto.id), self._shotwell_photos)

    def get(self, LUID):
        DataProvider.DataSource.get(self, LUID)
        sPhoto = filter(lambda sPhoto: str(sPhoto.id) == LUID, self._shotwell_photos)[0]
        photo = Photo.Photo('file://' + sPhoto.filename)
        photo.set_UID(LUID)
        log.debug('Returning photo(%s) for LUID(%s)', sPhoto.filename, LUID)
        return photo

    def get_UID(self):
        return Utils.get_user_string()

