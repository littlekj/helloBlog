from django.test import TestCase
from blog.views import BreadcrumbMixin


class BreadcrumbMixinTest(TestCase):
    def setUp(self):
        self.view = BreadcrumbMixin()

    def test_get_breadcrumbs(self):
        breadcrumbs = self.view.get_breadcrumbs()
        self.assertEqual(breadcrumbs, [])

    def test_get_breadcrumbs_mobile(self):
        breadcrumbs_mobile = self.view.get_breadcrumbs_mobile()
        self.assertEqual(breadcrumbs_mobile, [])

    def test_get_context_data(self):
        """在实际使用 Mixin 功能的类和视图上测试"""
        pass
