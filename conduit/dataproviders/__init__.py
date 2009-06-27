import DataProviderCategory

#Default Categories for the DataProviders

CATEGORY_FILES = 'CATEGORY_FILES'
CATEGORY_NOTES = 'CATEGORY_NOTES'
CATEGORY_PHOTOS = 'CATEGORY_PHOTOS'
CATEGORY_OFFICE = 'CATEGORY_OFFICE'
CATEGORY_SETTINGS = 'CATEGORY_SETTINGS'
CATEGORY_MISC = 'CATEGORY_MISC'
CATEGORY_MEDIA = 'CATEGORY_MEDIA'
CATEGORY_BOOKMARKS = 'CATEGORY_BOOKMARKS'
CATEGORY_TEST = 'CATEGORY_TEST'

CATEGORIES = {
    CATEGORY_FILES : DataProviderCategory.DataProviderCategory("Files and Folders", "computer"),
    CATEGORY_NOTES : DataProviderCategory.DataProviderCategory("Notes", "tomboy"),
    CATEGORY_PHOTOS : DataProviderCategory.DataProviderCategory("Photos", "image-x-generic"),
    CATEGORY_OFFICE : DataProviderCategory.DataProviderCategory("Office", "applications-office"),
    CATEGORY_SETTINGS : DataProviderCategory.DataProviderCategory("Settings", "applications-system"),
    CATEGORY_MISC : DataProviderCategory.DataProviderCategory("Miscellaneous", "applications-accessories"),
    CATEGORY_MEDIA : DataProviderCategory.DataProviderCategory("Media", "applications-multimedia"),
    CATEGORY_BOOKMARKS : DataProviderCategory.DataProviderCategory("Bookmarks", "user-bookmarks"),
    CATEGORY_TEST : DataProviderCategory.DataProviderCategory("Test")
}
