from django.urls import reverse
from django.test import TestCase
from django.contrib.auth.models import User
from blog.models import Post, Category, Tag


class BlogUrlsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='password')
        self.category1 = Category.objects.create(name='Category 1')
        self.category2 = Category.objects.create(name='Category 2')
        self.tag1 = Tag.objects.create(name='Tag 1')
        self.tag2 = Tag.objects.create(name='Tag 2')

        self.post = Post.objects.create(
            title='Test Post',
            body='This is a test post.',
            author=self.user
        )

        self.post.categories.set([self.category1, self.category2])
        self.post.tags.set([self.tag1, self.tag2])

    def test_index_url(self):
        """测试首页 URL"""
        url = reverse('blog:index')  # 反向解析
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)  # 确保返回 200 OK 状态码

    def test_post_detail_url(self):
        """测试文章详情页 URL"""
        url = reverse('blog:detail', args=[self.post.slug])  # 假设 slug 为 'test-slug'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_category_list_url(self):
        """测试分类列表页 URL"""
        url = reverse('blog:categories')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_category_detail_url(self):
        """测试分类详情页 URL"""
        url = reverse('blog:category_detail', args=[self.post.categories.first().slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_tag_list_url(self):
        """测试标签列表页 URL"""
        url = reverse('blog:tags')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_tag_detail_url(self):
        """测试标签详情页 URL"""
        url = reverse('blog:tag_detail', args=[self.post.tags.first().slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_archive_url(self):
        """测试归档页面 URL"""
        url = reverse('blog:archives')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_about_url(self):
        """测试关于页面 URL"""
        url = reverse('blog:about')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_rss_feed_url(self):
        """测试 RSS 订阅 URL"""
        url = reverse('blog:rss_feed')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_search_url(self):
        """测试搜索页面 URL"""
        url = reverse('blog:search')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_sitemap_url(self):
        """测试站点地图 URL"""
        url = reverse('blog:django.contrib.sitemaps.views.sitemap')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_robots_txt_url(self):
        """测试 robot 规则页面 URL"""
        url = reverse('blog:robots_txt')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
