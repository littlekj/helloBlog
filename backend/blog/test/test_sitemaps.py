from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from blog.models import Post, Tag
from django.contrib.auth import get_user_model
from blog.sitemaps import PostSitemap, HomeSitemap, TagSitemap


class SitemapTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpassword')

        # 创建两个标签
        self.tag1 = Tag.objects.create(name='Python', slug='python')
        self.tag2 = Tag.objects.create(name='Django', slug='django')

        # tag1 对应 10 篇文章，tag2 对应 5 篇文章
        for i in range(10):
            post = Post.objects.create(
                title=f'Python Post {i}',
                body=f'This is the body of test post {i}',
                author=self.user,
                created_time=timezone.now(),
                modified_time=timezone.now()
            )
            post.tags.add(self.tag1)

        for i in range(5):
            post = Post.objects.create(
                title=f'Django Post {i}',
                body=f'This is the body of test post {i}',
                author=self.user,
                created_time=timezone.now(),
                modified_time=timezone.now()
            )
            post.tags.add(self.tag2)

    def test_post_sitemap_items(self):
        sitemap = PostSitemap()
        items = sitemap.items()

        # 检查是否有 15 篇文章
        self.assertEqual(len(items), 15)
        self.assertTrue(all(isinstance(post, Post) for post in items))

        # 检查文章列表是否按 modified_time 降序排列
        modified_times = [post.modified_time for post in items]
        self.assertEqual(modified_times, sorted(modified_times, reverse=True))

    def test_post_sitemap_lastmod(self):
        sitemap = PostSitemap()
        for post in sitemap.items():
            self.assertIsNotNone(sitemap.lastmod(post))

    def test_home_sitemap(self):
        sitemap = HomeSitemap()
        item = sitemap.items()
        self.assertEqual(item, ['blog:index'])
        self.assertEqual(sitemap.location('blog:index'), reverse('blog:index'))

    def test_tag_sitemap_filtering(self):
        sitemap = TagSitemap()
        items = sitemap.items()
        self.assertEqual(len(items), 1)  # 只有 tag1 有超过 5 篇文章

    def test_tag_sitemap_location(self):
        sitemap = TagSitemap()
        items = sitemap.items()
        for tag in items:
            url = sitemap.location(tag)
            self.assertEqual(url, reverse('blog:tag_detail', args=[tag.slug]))
