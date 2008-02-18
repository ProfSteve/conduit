"""
An Example DataSource and DataType implementation.
"""
import random
import logging
log = logging.getLogger("modules.Example")

import conduit
import conduit.Exceptions as Exceptions
import conduit.Utils as Utils
import conduit.datatypes.DataType as DataType
import conduit.dataproviders.DataProvider as DataProvider

MODULES = {
    "ExampleDataProviderTwoWay" :   { "type": "dataprovider" },
    "ExampleConverter"          :   { "type": "converter" }
}

class ExampleDataProviderTwoWay(DataProvider.TwoWay):
    """
    An example dataprovider demonstrating how to partition
    funtionality in such a way
    """

    _name_ = "Example Dataprovider"
    _description_ = "Demonstrates a Twoway Dataprovider"
    _category_ = conduit.dataproviders.CATEGORY_MISC
    _module_type_ = "twoway"
    _in_type_ = "exampledata"
    _out_type_ = "exampledata"
    _icon_ = "applications-internet"

    DEFAULT_FOO_VALUE = 42

    def __init__(self):
        """
        Constructor should call the base constructor and initialize
        all variables that are restored from configuration
        """
        DataProvider.TwoWay.__init__(self)
        self.data = []
        self.foo = 0

    def _data_exists(self, LUID):
        """
        @returns: True if data at the LUID exists
        """
        return random.randint(0,1)

    def _get_data(self, LUID):
        """
        @returns: A ExampleDataType with the specified LUID
        """
        data = ExampleDataType(
                        uri=LUID,
                        data=self.foo*random.randint(1,100)
                        )
        return data

    def _put_data(self, data):
        """
        @returns: Rid
        """
        data = ExampleDataType(
                        uri=random.randint(1,100),
                        data=self.foo*random.randint(1,100)
                        )
        return data.get_rid()

    def _replace_data(self, LUID, data):
        """
        Some dataproviders assign a new LUID when data is replaced. This
        is the purpose of having replace in a different function to _put
        """
        data.set_UID(random.randint(1,100))
        return data.get_rid()

    def configure(self, window):
        """
        Uses the L{conduit.DataProvider.DataProviderSimpleConfigurator} class
        to show a simple configuration dialog which is just a gtk.Enry
        where the user can enter one or more GNOME wiki pages names,
        seperated by commas

        @param window: The parent window (used for modal dialogs)
        @type window: C{gtk.Window}
        """
        #lazy import gtk so if conduit is run from command line arg, or
        #a non gtk system, this dp will still load. There should be no need
        #to use gtk outside of this function
        import gtk
        import conduit.gtkui.SimpleConfigurator as SimpleConfigurator
        
        def set_foo(param):
            self.foo = int(param)
        
        items = [
                    {
                    "Name" : "Value of Foo:",
                    "Widget" : gtk.Entry,
                    "Callback" : set_foo,
                    "InitialValue" : str(self.foo)
                    }                    
                ]
        #We just use a simple configuration dialog
        dialog = SimpleConfigurator.SimpleConfigurator(window, self._name_, items)
        #This call blocks
        dialog.run()
        
    def refresh(self):
        """
        The refresh method should do whatever is needed to ensure that a 
        subseqent call to get_all returns the correct result.

        The refresh method is always called before the sync step. DataSources 
        should always call the base classes refresh() method.
        """
        DataProvider.TwoWay.refresh(self)
        self.data = [str(random.randint(1,100)) for i in range(10)]

    def get_all(self):
        """
        Returns the LUIDs of all items to synchronize.        
        DataSources should always call the base classes get_all() method
        @return: A list of string LUIDs
        """
        DataProvider.TwoWay.get_all(self)
        return self.data
            
    def get(self, LUID):
        """
        Returns the data identified by the supplied LUID.
        @param LUID: A LUID which uniquely represents data to return
        @type LUID: C{str}
        """
        DataProvider.TwoWay.get(self, LUID)
        data = self._get_data(LUID)
        #datatypes can be shared between modules. For this reason it is
        #necessary tp explicity set parameters like the LUID
        data.set_UID(LUID)
        data.set_open_URI("file:///home/")
        return data

    def put(self, data, overwrite, LUID):
        """
        @returns: The Rid of the page at location LUID
        """
        DataProvider.TwoWay.put(self, data, overwrite, LUID)
        #If LUID is None, then we have once-upon-a-time uploaded this data
        if LUID != None:
            #Check if the remote data exists (i.e. has it been deleted)
            if self._data_exists(LUID):
                #The remote page exists
                if overwrite == False:
                    #Only replace the data if it is newer than the remote one
                    oldData = self._get_data(LUID)
                    comp = data.compare(oldData)
                    if comp == conduit.datatypes.COMPARISON_NEWER:
                        return self._replace_data(LUID, data)
                    elif comp == conduit.datatypes.COMPARISON_EQUAL:
                        #We are the same, so return either rid
                        return oldData.get_rid()
                    else:
                        #If we are older that the remote page, or if the two could not
                        #be compared, then we must ask the user what to do via a conflict
                        raise Exceptions.SynchronizeConflictError(comp, data, oldData)

        #If we get here then the data is new
        return self._put_data(data)

    def delete(self, LUID):
        """
        Not all dataproviders support delete
        """
        DataProvider.TwoWay.delete(self, LUID)
            
    def get_configuration(self):
        """
        Returns a dict of key:value pairs. Key is the name of an internal
        variable, and value is its current value to save.

        It is important the the key is the actual name (minus the self.) of the
        internal variable that should be restored when the user saves
        their settings. 
        """
        return {"foo" : self.foo}

    def set_configuration(self, config):
        """
        If you override this function then you are responsible for 
        checking the sanity of values in the config dict, including setting
        any instance variables to sane defaults
        """
        self.foo = config.get("foo",ExampleDataProviderTwoWay.DEFAULT_FOO_VALUE)

    def is_configured(self, isSource, isTwoWay):
        """
        @returns: True if this instance has been correctly configured, and data
        can be retrieved/stored into it
        """
        return self.foo != 0

    def get_UID(self):
        """
        @returns: A string uniquely representing this dataprovider.
        """
        return "Example UID %s" % self.foo
        
class ExampleDataType(DataType.DataType):
    """
    A sample L{conduit.DataType.DataType} used to represent a page from
    the GNOME wiki.

    DataSources should try to used the supplied types (Note, File, etc) but
    if they must define their own then this class shows how. 
    """
    
    _name_ = "exampledata"

    def __init__(self, uri, **kwargs):
        """
        It is recommended to have compulsory parameters and then
        kwargs as arguments to the constructor
        """
        DataType.DataType.__init__(self)
        self.data = kwargs.get("data",0)

    def __str__(self):
        """
        The result of str may be shown to the user if there is a conflict.
        It should represent a small descriptive snippet of the Datatype.
        """
        return self.get_string()

    def get_hash(self):
        """
        The hash should be able to detect if the data has been modified, irrespective
        of the mtime - i.e. use the page contents directly
        """
        return hash(self.data)

    def get_string(self):
        return "string %d" % self.data

class ExampleConverter:
    """
    An example showing how to convert data from one type to another
    
    If you define your own DataType then you should define one or more
    converter (methods) for it, because it is likely that other DataSources, 
    such as the ones that ship with conduit will not know how to deal with
    the new DataType.

    @ivar self.conversions: A dictionary mapping conversions to functions
    which perform the conversion
    """
    def __init__(self):
        """
        Fills out the required L{self.conversions} dict

        Simply provide a list of conversions and associated functions
        in the following formatt::
        
            self.conversions =  {    
                                "from_type_name,to_type_name" : convert_function
                                }
        """
        self.conversions =  {    
                            "exampledata,file"   : self.exampledata_to_file
                            }
                            

    def exampledata_to_file(self, data, **kwargs):
        """
        Converts exampledata to a file containing the text
        """
        f = Utils.new_tempfile(
                        contents=data.get_string()
                        )
        return f

