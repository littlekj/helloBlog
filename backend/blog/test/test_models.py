from django.test import TestCase
from blog.models import Post, Category, Tag
from django.contrib.auth.models import User
from django.urls import reverse
from blog.utils import slugify_translate


class CategoryModelTest(TestCase):

    def setUp(self):
        # 创建父级和子级分类
        self.parent_category = Category.objects.create(name='Parent Category')
        self.child_category = Category.objects.create(name='Child Category', parent=self.parent_category)

    def test_category_slug_creation(self):
        """测试分类创建时，slug 是否正确生成"""
        category = Category.objects.create(name='Test Category')
        self.assertEqual(category.slug, 'test-category')

    def test_category_get_absolute_url(self):
        """测试分类的 get_absolute_url 方法"""
        # 测试父级分类
        category = Category.objects.create(name='Test Category')
        url = category.get_absolute_url()
        expected_url = reverse('blog:category_detail', kwargs={'slug': 'test-category'})
        self.assertEqual(url, expected_url)

        # 测试带父级分类的子级分类
        url_with_parent = self.child_category.get_absolute_url()
        expected_url_with_parent = reverse('blog:category_detail',
                                           kwargs={'slug': 'parent-category/child-category'})
        self.assertEqual(url_with_parent, expected_url_with_parent)

    def test_category_parent_relation(self):
        """确保父级分类与子级分类关联正常"""
        self.assertEqual(self.child_category.parent, self.parent_category)
        self.assertIn(self.child_category, self.parent_category.children.all())

    def test_category_str_method(self):
        """确保 Category 模型的 __str__ 方法返回正确的字符串"""
        category = Category.objects.create(name='Test Category')
        self.assertEqual(str(category), 'Test Category')


class TagModelTest(TestCase):
    def setUp(self):
        # 创建标签实例
        self.tag = Tag.objects.create(name='Test Tag')

    def test_tag_slug_creation(self):
        """测试标签创建时，slug 是否正确生成"""
        tag = Tag.objects.create(name='Another Tag')
        self.assertEqual(tag.slug, 'another-tag')

    def test_tag_get_absolute_url(self):
        """测试标签的 get_absolute_url 方法"""
        url = self.tag.get_absolute_url()
        expected_url = reverse('blog:tag_detail', kwargs={'slug': 'test-tag'})
        self.assertEqual(url, expected_url)

    def test_tag_str_method(self):
        """确保 Tag 模型的 __str__ 方法返回正确的字符串"""
        self.assertEqual(str(self.tag), 'Test Tag')


class PostModelTest(TestCase):

    def setUp(self):
        # 创建用户
        self.user = User.objects.create_user(username="testuser", password="password")

        # 创建分类和标签
        self.category1 = Category.objects.create(name='Test Category1')
        self.category2 = Category.objects.create(name='Test Category2')
        self.tag1 = Tag.objects.create(name='Test Tag1')
        self.tag2 = Tag.objects.create(name='Test Tag2')

        # 创建 Post 实例
        self.post = Post.objects.create(
            title="测试 Post",
            body="This is a test post content.",
            author=self.user
        )

        self.post.categories.set([self.category1, self.category2])
        self.post.tags.set([self.tag1, self.tag2])

    def test_post_creation(self):
        # 测试文章是否成功创建
        post = self.post
        self.assertEqual(post.title, "测试 Post")
        self.assertEqual(post.body, "This is a test post content.")
        self.assertEqual(post.author.username, "testuser")
        self.assertEqual(post.categories.first().name, "Test Category1")
        self.assertEqual(post.tags.first().name, "Test Tag1")

    def test_slug_generation(self):
        # 测试 slug 是否生成正确
        post = self.post
        expected_slug = slugify_translate(post.title)
        self.assertEqual(post.slug, expected_slug)

    def test_save_with_no_slug(self):
        # 创建没有 slug 的文章
        post = Post.objects.create(
            title="Test Post Without Slug",
            body="This is a test post without slug.",
            author=self.user
        )

        # 验证 slug 是否被自动生成
        self.assertIsNotNone(post.slug)
        self.assertTrue(post.slug.startswith(slugify_translate(post.title)))

    def test_post_string_representation(self):
        # 测试 Post 模型的字符串表示
        self.assertEqual(str(self.post), "测试 Post")

    def test_increase_views(self):
        # 初始浏览量
        initial_views = self.post.views

        # 调用 increase_views 方法
        self.post.increase_views()

        # 验证浏览量是否增加
        self.assertEqual(self.post.views, initial_views + 1)

    def test_get_absolute_url(self):
        # 获取文章的绝对 URL
        expected_url = f"/posts/{self.post.slug}"
        self.assertEqual(self.post.get_absolute_url(), expected_url)
