import logging
log = logging.getLogger("dataproviders.AccountFactory")

import conduit
import conduit.dataproviders.DataProvider as DataProvider
import conduit.dataproviders.DataProviderCategory as DataProviderCategory
import conduit.utils as Utils
import conduit.dataproviders.SimpleFactory as SimpleFactory


class AccountFactory(SimpleFactory.SimpleFactory):

    def __init__(self, **kwargs):
        SimpleFactory.SimpleFactory.__init__(self, **kwargs)
        self.account_manager = conduit.GLOBALS.accountManager
        #emit_added(self, klass, initargs, category, customKey=None)
        
    def probe(self):
        for account in self.account_manager.list_accounts(self._name_):
            self.item_added(account)
        
    def get_category(self, key, **kwargs):
        return DataProviderCategory.DataProviderCategory(
                    key,
                    self._icon_,
                    self._name_)

    def get_args(self, key, **kwargs):
        return tuple(self.account_manager.account_properties(self._name_, key, self._properties_))

