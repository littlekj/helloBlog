from django.test import TestCase
from django.urls import reverse
from blog.models import Post
from django.contrib.auth import get_user_model
from xml.etree import ElementTree as ET


class RSSFeedTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpassword')
        self.post = Post.objects.create(
            title='Test RSS Post',
            body='This is the body of the RSS post.',
            excerpt='Excerpt of the post.',
            author=self.user
        )
        self.url = reverse('blog:rss_feed')

    def test_rss_feed_response(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/rss+xml; charset=utf-8')

        # 检查是否包含文章标题和摘要
        content = response.content.decode()
        self.assertIn(self.post.title, content)
        self.assertIn(self.post.excerpt, content)

    def test_rss_feed_structure(self):
        response = self.client.get(self.url)
        # 使用 ElementTree 解析 XML 响应内容
        root = ET.fromstring(response.content)

        # 验证根节点是 <rss>，确保响应是一个标准的 RSS 文档
        self.assertEqual(root.tag, 'rss')

        # 检查是否包含 <channel> 节点
        channel = root.find('channel')
        self.assertIsNotNone(channel)

        # 检查至少存在一个 <item>
        items = channel.findall('item')
        self.assertEqual(len(items), 1)

        # 检查第一个 item 的各个字段
        item = items[0]

        # 检查 <title> 字段
        title = item.find('title')
        self.assertIsNotNone(title)
        self.assertEqual(self.post.title, title.text)

        # 检查 <link> 字段
        link = item.find('link')
        self.assertIsNotNone(link)
        self.assertTrue(link.text.startswith('http://') or link.text.startswith('https://'))

        # 检查 <description> 字段
        description = item.find('description')
        self.assertIsNotNone(description)
        self.assertTrue(len(description.text) > 0)

        # 检查 <pubDate> 字段是否存在并为有效字符串
        pub_date = item.find('pubDate')
        self.assertIsNotNone(pub_date)
        # 验证日期格式符合标准 RSS 日期格式（如 Tue, 07 May 2024 12:00:00 GMT）
        self.assertRegex(pub_date.text, r'\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} .+')

        # 检查 <dc:creator> 字段，解析命名空间标签
        namespaces = {'dc': 'http://purl.org/dc/elements/1.1/'}
        creator = item.find('dc:creator', namespaces)
        self.assertIsNotNone(creator)
        self.assertEqual(self.user.username, creator.text)
