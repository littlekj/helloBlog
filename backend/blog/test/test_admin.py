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

    @patch('blog.admin.render_markdown')  # 模拟 render_markdown 函数
    def test_save_model_sets_author_and_renders_body_and_toc(self, mock_render_markdown):
        """
        测试 save_model 方法是否在文章创建或更新时，正确设置作者并渲染了 body 和 toc
        """
        # 设置 render_markdown 模拟的返回值，返回 rendered_body 和 toc
        mock_render_markdown.return_value = '<p>Rendered content</p>\n', '<h2>Rendered toc</h2>'

        # 模拟表单，表明 body 字段已更改
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

        # 检查是否保存了 rendered_body 和 toc
        self.assertEqual(self.post.rendered_body, '<p>Rendered content</p>\n')
        self.assertEqual(self.post.toc, '<h2>Rendered toc</h2>')

    @patch('blog.admin.render_markdown')  # 模拟 rendered_markdown 函数
    def test_save_model_rendered_body_toc_on_create(self, mock_render_markdown):
        """
        测试 save_model 方法是否在文章创建时，正确生成 toc 和 rendered_body
        """
        # 设置 render_markdown 模拟的返回值，返回 rendered_body 和 toc
        mock_render_markdown.return_value = '<p>Rendered content</p>\n', '<h2>Rendered toc</h2>'

        # 模拟表单，表明 body 字段尚未修改
        mock_form = MagicMock()
        mock_form.changed_data = []
        mock_form.save.return_value = self.post  # 确保 save 方法返回 post 实例

        # 模拟请求对象
        request = MagicMock()
        request.user = self.user

        # 调用被测试的 save_model 方法
        self.admin.save_model(request, self.post, mock_form, change=False)

        # 检查 author 字段是否正确设置
        self.assertEqual(self.post.author, self.user)

        # 检查 render_markdown 是否被调用
        mock_render_markdown.assert_called_once_with(self.post.body)

        # 检查是否保存了 rendered_body 和 toc
        self.assertEqual(self.post.rendered_body, '<p>Rendered content</p>\n')
        self.assertEqual(self.post.toc, '<h2>Rendered toc</h2>')

    @patch('blog.admin.render_markdown')  # 模拟 render_markdown 函数
    def test_save_model_does_not_render_on_no_change(self, mock_render_markdown):
        """
        测试 save_model 方法是否在 body 未更改时，不渲染正文和目录
        """
        # 让 render_markdown 返回默认值
        mock_render_markdown.return_value = '<p>No content</p>\n', '<h2>No toc</h2>'

        # 模拟表单，表示 body 字段没有更改
        mock_form = MagicMock()
        mock_form.changed_data = []
        mock_form.save.return_value = self.post  # 确保 save() 方法模拟成功

        # 保存当前 post 的原始状态，用于后续验证是否有变化
        original_rendered_body = self.post.rendered_body
        original_toc = self.post.toc

        # 模拟请求对象
        request = MagicMock()
        request.user = self.user

        # 调用 save_model 方法
        self.admin.save_model(request, self.post, mock_form, change=True)

        # 断言无变化
        self.assertEqual(self.post.rendered_body, original_rendered_body)
        self.assertEqual(self.post.toc, original_toc)
