import gobject
import gconf
GCONF_PATH = "/apps/conduit/Accounts"

class AccountManager(gobject.GObject):
    def __init__(self, *kwargs):
        gobject.GObject.__init__(self, *kwargs)
        self._client = gconf.client_get_default()

    def list_accounts(self, name):
        items = []
        for path in self._client.all_dirs(GCONF_PATH + '/' + name):
            account_name = path.split("/")[-1]
            items.append(account_name)
        return items
    
    def account_properties(self, name, account_name, properties):
        props = []
        for entry in self._client.all_entries('/'.join((GCONF_PATH, name, account_name))):
            prop_name = entry.key.split("/")[-1]
            prop_value = entry.value            
            if prop_name in properties:
                prop_type = properties[prop_name]
                props.append(self._get_property(prop_value, prop_type))
        return props
    
    def _get_property(self, value, vtype):
        if vtype is bool:
            return value.get_bool()
        elif vtype is str:
            return value.get_string()
        elif vtype is int:
            return value.get_int()
        elif vtype in (list, tuple):
            l = []
            for i in value.get_list():
                l.append(i.get_string())
            return l    
