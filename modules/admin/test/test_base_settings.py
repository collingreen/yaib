from ..base_settings import BaseSettings
from nose import with_setup


class TestBaseSettings(object):

    def setup(self):
        self.settings = BaseSettings()

    def test_leaf(self):
        """Test setting a leaf node."""
        self.settings.set('test', 'thing')
        assert(self.settings.get('test') == 'thing')

    def test_doesnt_exist(self):
        """Test getting a key that doesn't exists."""
        assert(self.settings.get('notathing') == None)

    def test_doesnt_exist_with_default(self):
        """Test getting a key that doesn't exists with default."""
        assert(self.settings.get('notathing', default=1) == 1)

    def test_initial_flag(self):
        """
        Test initial flag only sets values if they do not
        already exist.
        """
        self.settings.set('initial_test', '1', initial=True)
        self.settings.set('initial_test', '2', initial=True)
        assert(self.settings.get('initial_test') == '1')

    def test_nested_keys(self):
        """Test setting a nested key."""
        self.settings.set('nested.thing', 'yeah')
        assert(self.settings.get('nested.thing') == 'yeah')
        assert(self.settings.get('nested') == {'thing': 'yeah'})

    def test_nested_keys_dont_break_siblings(self):
        """
        Test setting a nested key does not unset any of
        the siblings.
        """
        self.settings.set('nested.thing', 'yeah')
        self.settings.set('nested.otherthing', 'what')
        assert(self.settings.get('nested.thing') == 'yeah')
        assert(self.settings.get('nested.otherthing') == 'what')
        assert(
                self.settings.get('nested') == \
                    {'thing': 'yeah', 'otherthing': 'what'}
            )

    def test_setting_dict(self):
        """Test setting a tree of keys using a dictionary."""
        self.settings.set('dict_test', {'a': 'A', 'b': {'deep': 'works too'}})
        assert(self.settings.get('dict_test.b.deep') == 'works too')

    def test_set_multi(self):
        """Test multiple keys at once."""
        self.settings.setMulti({'a': 'A', 'b': 'B'})
        assert(self.settings.get('a') == 'A')
        assert(self.settings.get('b') == 'B')

    def test_get_multi(self):
        """Test getting multiple keys at once."""
        self.settings.setMulti({'a': 'A', 'b': 'B'})
        multi = self.settings.getMulti(['a','b'])
        assert(multi['a'] == 'A')
        assert(multi['b'] == 'B')

    def test_get_multi_doesnt_exist(self):
        """Test getting multiple keys, some of which don't exist."""
        self.settings.setMulti({'a': 'A', 'b': 'B'})
        multi = self.settings.getMulti(['a','b','c'])
        assert(multi['c'] is None)

    def test_get_multi_doesnt_exist_default(self):
        """Test getting multiple keys, some of which don't exist."""
        self.settings.setMulti({'a': 'A', 'b': 'B'})
        multi = self.settings.getMulti(['a','b','c'], default='default')
        assert(multi['c'] == 'default')

    def test_lists(self):
        """Test setting lists."""
        test_list = ['a','b','c']
        self.settings.set('list', test_list)
        test_list2 = self.settings.get('list')
        assert(test_list == test_list2)
