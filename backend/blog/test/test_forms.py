from django.test import TestCase
from blog.models import Post
from django import forms


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'body']


class PostFormTest(TestCase):
    def test_valid_form(self):
        form_data = {'title': 'Test Post', 'body': 'This is a test post content'}
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())  # 如果表单有效，应该返回 True

    def test_invalid_form(self):
        form_data = {'title': '', 'body': 'This is a test post content'}
        form = PostForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
