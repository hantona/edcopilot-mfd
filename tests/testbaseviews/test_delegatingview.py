import unittest

from baseview.delegatingview import DelegatingView
from baseview.view import View


class DelegatingViewTest(unittest.TestCase):
    # Test that DelegatingView overrides all methods in View
    def test_method_override(self):
        public_methods = [m for m in dir(View) if not  m.startswith("_") and callable(getattr(View, m))]
        delegating_methods = [m for m in DelegatingView.__dict__.keys() if not m.startswith("_")]

        # Remove methods specific to DelegatingView
        delegating_methods.remove("get_delegate")

        # Client allocation is handled by the parent view only
        public_methods.remove("get_client")

        # The base implementation shouldn't need to changed
        public_methods.remove("set_footer_hint")
        public_methods.remove("get_subtitle")

        # Each subclass likely needs to override get_subtitle_list
        public_methods.remove("get_subtitle_list")

        # The base implementation for these is sometimes fine
        public_methods.remove('get_view_items')
        public_methods.remove('get_view_item')
        public_methods.remove('needs_client')

        self.assertEqual(set(public_methods), set(delegating_methods))  # add assertion here


if __name__ == '__main__':
    unittest.main()
