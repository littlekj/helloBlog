from django.test import TestCase, RequestFactory
from unittest.mock import patch
from django.utils import timezone
from blog.models import Post, Tag
from blog.templatetags.blog_tags import show_recent_posts
from blog.templatetags.blog_tags import show_trending_tags
from blog.templatetags.blog_tags import calculate_read_time, share_detail
from django.template import Context
from django.core.cache import cache
from django.contrib.auth import get_user_model
from urllib.parse import quote
from django.urls import reverse
from blog.templatetags.page_tags import meta_data


class ShowRecentPostsTest(TestCase):
    """
    验证：
    - 是否正确返回指定数量的文章
    - 是否按 modified_time(优先)或 created_time 降序排列
    - 缓存是否生效
    - 缓存失效后是否重新查询数据库
    """

    def setUp(self):
        # 清除缓存，确保测试的独立性
        cache.clear()

        # 创建测试数据
        self.user = get_user_model().objects.create_user(username='testuser', password='testpassword')

        for i in range(6):
            Post.objects.create(
                title=f'Post {i}',
                body=f'Content of post {i}.',
                author=self.user,
                created_time=timezone.now()
            )

    def test_show_recent_posts_returns_correct_number(self):
        context = Context({})
        result = show_recent_posts(context, num=2)
        self.assertEqual(len(result['recent_posts']), 2)

    def test_show_recent_posts_ordering(self):
        context = Context({})
        result = show_recent_posts(context, num=3)
        posts = result['recent_posts']

        # 检查文章是否按 modified_time 降序排列
        times = [
            post.modified_time if post.modified_time else post.created_time for post in posts
        ]
        self.assertEqual(times, sorted(times, reverse=True))

    def test_show_recent_posts_caching(self):
        """断言代码块内执行的 SQL 查询次数"""
        context = Context({})

        # 第一次调用，应该会查询数据库
        with self.assertNumQueries(1):
            show_recent_posts(context, num=2)

        # 再次调用，应该会使用缓存，不查询数据库
        with self.assertNumQueries(0):
            show_recent_posts(context, num=2)

    def test_show_recent_posts_cache_key_differs_by_num(self):
        """断言缓存键不同生成不同的缓存"""
        result_3 = show_recent_posts({}, num=3)['recent_posts']
        result_5 = show_recent_posts({}, num=5)['recent_posts']

        self.assertEqual(len(result_3), 3)
        self.assertEqual(len(result_5), 5)
        self.assertNotEqual(result_3, result_5)

    def test_show_recent_posts_fetches_after_cache_expiry(self):
        """断言缓存过期后重新查询数据库"""
        # 设置缓存过期时间为 2 秒
        cache.set('recent_posts', 'dummy', 2)

        # 第一次调用，应该会查询数据库
        with self.assertNumQueries(1):
            show_recent_posts({}, num=2)

        # 再次调用，应该会使用缓存，不查询数据库
        with self.assertNumQueries(0):
            show_recent_posts({}, num=2)

        # 等待缓存过期，手动清除缓存，强制过期
        cache.clear()

        # 再次调用，应该会重新查询数据库
        with self.assertNumQueries(1):
            show_recent_posts({}, num=2)

    @patch('blog.templatetags.blog_tags.print')  # 拦截 print()，使其不输出内容，只记录调用。
    @patch('blog.templatetags.blog_tags.Post.objects.order_by')
    def test_show_recent_posts_handles_exception(self, mock_query, mock_print):
        """断言在查询异常情况下返回空列表"""
        # 模拟查询时抛出异常
        mock_query.side_effect = Exception('DB error')

        result = show_recent_posts({}, num=2)

        self.assertEqual(result['recent_posts'], [])  # 应返回空列表，说明异常被处理
        mock_print.assert_called_once()  # 确保 print 被调用
        self.assertIn('DB error', mock_print.call_args[0][0])  # 检查错误信息内容


class ShowTrendingTagsTest(TestCase):
    """
    验证：
    - 返回结果是否包含指定数量的标签
    - 标签是否按 num_posts 降序排列
    - 是否只包含 num_posts > 0 的标签
    """

    def setUp(self):
        self.user = get_user_model().objects.create(username='testuser', password='testpassword')

        # 创建标签和文章的关系
        for i in range(5):
            tag = Tag.objects.create(name=f'tag{i}', slug=f'tag{i}')
            for _ in range(i):  # i 篇文章关联该标签
                post = Post.objects.create(title=f'Post {i}', body=f'Content of post {i}.', author=self.user)
                post.tags.add(tag)

    def test_show_trending_tags_result(self):
        result = show_trending_tags({}, num=3)
        tags = result['trending_tags']

        # 检查是否包含指定数量的标签
        self.assertEqual(len(tags), 3)

        # 检查标签是否按 num_posts 降序排列
        # num_posts 是通过 annotate() 动态添加到每个 Tag 对象上的字段
        num_posts_list = [tag.num_posts for tag in tags]
        self.assertEqual(num_posts_list, sorted(num_posts_list, reverse=True))

        for tag in tags:
            self.assertGreater(tag.num_posts, 0)


class CalculateReadTimeTest(TestCase):
    """
    验证：
    - 是否正确计算文章的阅读时间
    - 是否正确处理中英混合或空文章
    - HTML 去标签处理
    - 阅读时间的向上取整计算是否正确
    - 上下文变量是否正确传递
    """

    def test_read_time_mixed_chinese_english(self):
        """是否正确计算混合中英文文章的阅读时间"""
        context = Context()
        content = "This is 混合测试 with 中文 characters"
        calculate_read_time(context, content, wpm=4)
        # 验证上下文变量是否正确传递
        self.assertIn('words', context)
        self.assertIn('read_time', context)
        # 验证阅读时间是否正确计算
        self.assertEqual(context['words'], 10)
        self.assertEqual(context['read_time'], 3)

    def test_html_stripping(self):
        """HTML 标签是否被正确去除"""
        context = Context()
        content = "<p>Hello <strong>world</strong> 中文内容</p>"
        calculate_read_time(context, content, wpm=4)
        self.assertEqual(context['words'], 6)
        self.assertEqual(context['read_time'], 2)

    def test_empty_content(self):
        """空文章是否返回 0"""
        context = Context()
        content = ""
        calculate_read_time(context, content, wpm=4)
        self.assertEqual(context['words'], 0)
        self.assertEqual(context['read_time'], 0)


class ShareDetailTest(TestCase):
    """
    验证：
    - 是否正确生成分享链接
    - 分享链接格式是否符合预期，包含编码后的标题和 URL
    - 上下文变量是否正确传递
    """

    def setUp(self):
        # 创建一个伪造的 HTTP 请求对象，比 Client().get(...) 更底层，适用于直接调用视图函数（不通过 URL 解析）
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create(username='testuser', password='testpassword')
        self.post = Post.objects.create(title='Test Post', body='This is a test post', author=self.user)

    def test_share_detail_generates_expected_link(self):
        # 构造请求对象（伪造 detail 页面访问）
        request = self.factory.get(f'/posts/{self.post.pk}')
        # 设置 mock 方法，用于生成绝对 URL
        request.build_absolute_uri = lambda: f'http://testserver/posts/{self.post.pk}/'

        context = Context({'request': request})

        # 调用模板标签函数
        result = share_detail(context, self.post.pk)

        # 标签本身返回空字符串
        self.assertEqual(result, '')

        # 获取更新后的上下文
        platforms = context['share_platforms']
        self.assertEqual(len(platforms), 1)
        self.assertEqual(platforms[0]['type'], 'Telegram')

        # 验证链接是否包含正确的编码标题和 URL
        expected_title = quote(self.post.title)
        expected_url = quote(request.build_absolute_uri())
        self.assertIn(f'text={expected_title}', platforms[0]['link'])
        self.assertIn(f'url={expected_url}', platforms[0]['link'])

        # 验证额外提示信息是否存在
        self.assertEqual(context['copy_link_tooltip'], '复制链接')
        self.assertEqual(context['copy_link_success'], '链接复制成功！')


class MetaDataTagTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.author = get_user_model().objects.create(username='testuser', password='testpassword')
        self.post = Post.objects.create(
            title='测试标题',
            slug='test-post',
            excerpt='测试摘要',
            author=self.author,
            created_time=timezone.now(),
            modified_time=timezone.now(),
        )
        self.tag = Tag.objects.create(name='Python')
        self.post.tags.add(self.tag)

    def test_meta_on_index_page(self):
        request = self.factory.get(reverse('blog:index'))
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'
        context = Context({'request': request})
        meta_data(context)

        self.assertIn('meta', context)
        self.assertEqual(context['meta']['title'], '羽毛笔轻轻划过')
        self.assertFalse(context['is_mobile'])

    def test_meta_on_detail_page(self):
        request = self.factory.get(reverse('blog:detail', kwargs={'slug': 'test-post'}))
        context = Context({'request': request})
        meta_data(context)

        meta = context['meta']
        self.assertEqual(meta['title'], '测试标题')
        self.assertEqual(meta['description'], '测试摘要')
        self.assertIn('Python', meta['keywords'])
        self.assertEqual(meta['author'], self.author)

    @patch('blog.templatetags.page_tags.logger.warning')
    def test_meta_on_detail_page_post_not_found(self, mock_log):
        request = self.factory.get(reverse('blog:detail', kwargs={'slug': 'not-exist'}))
        context = Context({'request': request})
        meta_data(context)

        meta = context['meta']
        self.assertEqual(meta['title'], '文章未找到')
        self.assertIn('不存在', meta['description'])
        mock_log.assert_called_once()

    def test_is_mobile_flag(self):
        request = self.factory.get(reverse('blog:index'))
        request.META['HTTP_USER_AGENT'] = 'Mobile Safari'
        context = Context({'request': request})
        meta_data(context)

        self.assertTrue(context['is_mobile'])

    def test_meta_has_full_url(self):
        # 模拟一个使用 HTTPS 协议 的 GET 请求，而不是 HTTP
        request = self.factory.get(reverse('blog:index'), secure=True)
        context = Context({'request': request})
        meta_data(context)

        self.assertIn('full_url', context['meta'])
        self.assertTrue(context['meta']['full_url'].startswith('https'))
