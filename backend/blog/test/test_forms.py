from django.test import TestCase
from blog.forms import PostForm
from django import forms
from django.contrib.auth.models import User
from blog.models import Category, Tag
from django.utils import timezone


class PostFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.category = Category.objects.create(name='Test Category')
        self.tag = Tag.objects.create(name='Test Tag')

    def test_form_has_all_fields(self):
        """
        测试表单是否包含所有模型字段
        """
        form = PostForm()
        self.assertEqual(
            sorted(form.fields.keys()),
            sorted({
                'title', 'slug', 'body', 'toc', 'excerpt',
                'categories', 'tags', 'author',
                'created_time', 'modified_time', 'pin',
            })
        )

    def test_excerpt_widget_is_textarea_with_custom_attrs(self):
        """
        测试 excerpt 字段是否使用 Textarea 小部件，并且具有自定义的 rows 和 cols 属性
        """
        form = PostForm()
        excerpt_widget = form.fields['excerpt'].widget
        self.assertIsInstance(excerpt_widget, forms.Textarea)
        self.assertEqual(excerpt_widget.attrs.get('rows'), 5)
        self.assertEqual(excerpt_widget.attrs.get('cols'), 80)

    def test_form_valid_data(self):
        """测试表单对合法数据的处理"""
        form_data = {
            'title': 'Test Post',
            'slug': 'test-post',
            'body': 'This is a test post content',
            'excerpt': 'Short excerpt',
            'author': self.user,
            'created_time': timezone.now(),
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_missing_required_fields(self):
        """测试必填字段缺失时是否报错"""
        form = PostForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('body', form.errors)

    def test_form_saves_data_correctly(self):
        """测试表单保存数据是否正确"""
        form_data = {
            'title': 'Test Post',
            'body': 'This is a test post content',
            'excerpt': 'Short excerpt',
            'author': self.user,
            'created_time': timezone.now(),
        }
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())
        post = form.save(commit=False)
        post.save()  # 保存 post，生成 id
        post.categories.set([self.category])
        post.tags.set([self.tag])

        self.assertIsNotNone(post.pk)
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.slug, 'test-post')
        self.assertEqual(post.categories.first(), self.category)
        self.assertEqual(post.tags.first(), self.tag)
