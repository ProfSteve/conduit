import soup

def make_testcase(wrp):
    class TestDataprovider(soup.TestCase):
        wrapperclass = wrp

        @classmethod
        def name(self):
            return "TestDataProvider%s" % self.wrapperclass.name()

        def setUp(self):
            super(TestDataprovider, self).setUp()
            self.wrapper = self.wrapperclass(self)
            self.dp = self.wrapper.dp
            self.data = self.wrapper.dataclass()

        def tearDown(self):
            self.dp = None

        def test_add(self):
            """ Should be able to add items """
            self.dp.refresh()
            for obj in self.data.iter_samples():
                self.dp.put(obj, False, None)
            self.dp.finish(False, False, False)

        def test_replace(self):
            """ Should be able to replace items """
            obj = self.data.iter_samples().next()
            self.dp.refresh()
            rid = self.dp.put(obj, False, None)
            self.dp.finish(False, False, False)

            self.dp.refresh()
            self.dp.put(obj, True, rid.get_UID())
            self.dp.finish(False, False, False)

        def test_delete(self):
            """ Should be able to delete items """
            obj = self.data.iter_samples().next()
            self.dp.refresh()
            rid = self.dp.put(obj, False, None)
            self.dp.finish(False, False, False)

            self.dp.refresh()
            self.dp.delete(rid.get_UID())
            self.dp.finish(False, False, False)

        def test_refresh(self):
            """ Refresh shouldnt throw exceptions """
            self.dp.refresh()
            self.dp.finish(False, False, False)

        def test_finish(self):
            """ Should be able to call finish on cold """
            self.dp.finish(False, False, False)

        def test_get_num_items(self):
            """ Number of items in a fresh dataprovider should be 0 """
            self.dp.refresh()
            assert self.dp.get_num_items() == 0

    return TestDataprovider


# Generate TestCase objects for each dataprovider wrapper
self = soup.get_module(__name__)
for wrapper in soup.modules.get_all():
    testklass = make_testcase(wrapper)
    setattr(self, testklass.name(), testklass)


# Allow people to run the test case directly
if __name__ == "__main__":
    import unittest
    unittest.main()