from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import Client
from blog.models import Post, Category, Tag
from blog.admin import PostAdmin
from django.http import HttpRequest
from unittest.mock import MagicMock
from unittest.mock import patch


class PostModelFormTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin', password='admin_password', email='admin@example.com'
        )

        self.client = Client()
        self.client.force_login(self.user)

        self.post = Post.objects.create(
            title='Test', body='Test content', excerpt='Short excerpt', author=self.user
        )

    def test_admin_form_renders_excerpt_as_textarea_with_custom_size(self):
        """
        测试 PostModelForm 中 excerpt 字段是否正确渲染了 Textarea
        """
        url = reverse('admin:blog_post_change', args=[self.post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<textarea', html=False)  # 检查是否包含 <textarea> 标签，不做 html 标签结构比对
        self.assertContains(response, 'name="excerpt"')  # 检查 name 属性
        self.assertContains(response, 'rows="5"')  # 检查 rows 属性
        self.assertContains(response, 'cols="80"')  # 检查 cols 属性


class PostAdminPureMockTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = PostAdmin(Post, self.site)
        self.user = User.objects.create_superuser(
            username='admin', password='admin_password', email='admin@example.com'
        )

        # 创建测试分类和标签
        self.category = Category.objects.create(name='Test Category')
        self.tag = Tag.objects.create(name='Test Tag')

        # 创建 Post 实例
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            body='Test content',
            author=self.user,
        )

        self.post.categories.set([self.category])
        self.post.tags.set([self.tag])

        self.client = Client()
        self.client.login(username='admin', password='admin_password')

        self.request = HttpRequest()
        self.request.user = self.user

    def test_post_list_display(self):
        """
        测试 PostAdmin 是否正确显示了预期的字段（list_display）
        """
        url = reverse('admin:blog_post_changelist')  # 后台文章列表页面
        response = self.client.get(url)
        self.assertContains(response, 'title')
        self.assertContains(response, 'id')
        self.assertContains(response, 'created_time')
        self.assertContains(response, 'modified_time')
        self.assertContains(response, 'categories')
        self.assertContains(response, 'author')

    def test_post_admin_form_fields(self):
        """
        测试在 Post 编辑界面中，表单字段是否按预期显示
        """
        url = reverse('admin:blog_post_change', args=[self.post.id])  # 后台编辑页面
        response = self.client.get(url)
        self.assertContains(response, 'title')
        self.assertContains(response, 'slug')
        self.assertContains(response, 'body')
        self.assertContains(response, 'excerpt')
        self.assertContains(response, 'categories')
        self.assertContains(response, 'tags')

    @patch('blog.admin.render_markdown')  # 模拟 render_markdown 函数，避免调用真实的 Markdown 渲染逻辑
    @patch('blog.admin.super')  # 模拟 super() 调用，以便断言是否被正确调用
    def test_save_model_sets_author_and_renders_body_on_change(self, mock_super, mock_render_markdown):
        """
        测试 save_model 方法是否在 body 字段变化时设置 author 和重新渲染 body
        """
        # 设置 render_markdown 返回值，模拟渲染后的 HTML
        mock_render_markdown.return_value = '<p>Rendered content</p>\n'

        # 模版表单，指定 changed_data 包含 'body'，表示 body 字段已更改
        mock_form = MagicMock()
        mock_form.changed_data = ['body']

        # 构造一个模拟请求对象，指定 user 为当前用户
        request = MagicMock()
        request.user = self.user

        # 调用被测试的 save_model 方法
        self.admin.save_model(request, self.post, mock_form, change=True)

        # 检查 author 字段是否被正确设置为当前用户
        self.assertEqual(self.post.author, self.user)

        # 检查 render_markdown 是否被调用
        mock_render_markdown.assert_called_once_with(self.post.body)

        # 检查最终是否调用了 super().save_model
        mock_super().save_model.assert_called_once()

    @patch('blog.admin.render_markdown')
    @patch('blog.admin.super')
    def test_save_model_does_not_render_body_if_not_changed(self, mock_super, mock_render_markdown):
        """
        测试当 body 字段没有变化时，是否没有重新渲染 body
        """
        # 创建一个模拟的 Post 实例，完全不访问数据库
        mock_post = MagicMock(spec=Post)
        mock_post.rendered_body = '<p>Already rendered</p>'  # 非空，避免触发 markdown 渲染
        mock_post.body = 'Unchanged body'

        # mock save 方法以避免 DB 写入
        mock_post.save = MagicMock()

        mock_form = MagicMock()
        mock_form.changed_data = []  # 表示没有字段修改

        request = MagicMock()
        request.user = self.user

        self.admin.save_model(request, mock_post, mock_form, change=True)

        # 验证逻辑：没有触发 markdown 渲染
        mock_render_markdown.assert_not_called()

        # 只会调用 obj.save() 一次（不是带 update_fields 的那种）
        mock_post.save.assert_called_once_with()

        # 验证 super().save_model 被调用
        mock_super().save_model.assert_called_once()

    @patch('blog.admin.render_markdown')
    @patch('blog.admin.super')
    def test_save_model_renders_body_if_initially_empty(self, mock_super, mock_render_markdown):
        """
        测试当 rendered_body 初始为空时，是否可以正常渲染生成 rendered_body
        """
        mock_post = MagicMock(spec=Post)
        mock_post.rendered_body = ''
        # self.post.rendered_body = ''
        mock_render_markdown.return_value = '<p>Rendered content</p>\n'

        mock_form = MagicMock()
        mock_form.changed_data = []

        request = MagicMock()
        request.user = self.user

        self.admin.save_model(request, self.post, mock_form, change=True)

        mock_render_markdown.assert_called_once()
        mock_super().save_model.assert_called_once()
