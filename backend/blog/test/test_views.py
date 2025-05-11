from django.urls import reverse
from django.test import TestCase
from blog.models import Post, Category, Tag
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from unittest.mock import patch
from blog.views import CategoryListView, CategoryDetailView
from django.contrib.messages import get_messages
from unittest.mock import MagicMock


class IndexViewTest(TestCase):
    def setUp(self):
        # 创建测试数据
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.category = Category.objects.create(name='Category 1')
        self.post_1 = Post.objects.create(
            title='Post 1',
            slug='post-1',
            excerpt='Excerpt for post 1',
            body='Body for post 1',
            author=self.user,
        )
        self.post_1.categories.set([self.category])

        self.post_2 = Post.objects.create(
            title='Post 2',
            slug='post-2',
            excerpt='Excerpt for post 2',
            body='Body for post 2',
            author=self.user,
        )
        self.post_2.categories.set([self.category])
        self.url = reverse('blog:index')  # IndexView 的 URL 名称是 'index'

    def test_get_queryset(self):
        """测试 get_queryset 方法是否返回符合预期的查询集"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('post_list' in response.context)

        # 确保查询集返回的文章数量为 2
        post_list = response.context['post_list']
        self.assertEqual(len(post_list), 2)

    def test_get_breadcrumbs(self):
        """测试 get_breadcrumbs 方法，确保返回首页的面包屑"""
        response = self.client.get(self.url)
        self.assertEqual(response.context['breadcrumbs'], [('首页', '/')])

    def test_get_breadcrumbs_mobile(self):
        """测试 get_breadcrumbs_mobile 方法，确保返回首页的面包屑"""
        response = self.client.get(self.url)
        self.assertEqual(response.context['breadcrumbs_mobile'], ['首页'])

    def test_pagination(self):
        """测试分页功能"""
        # 创建更多的文章，确保分页生效
        for i in range(3, 13):
            Post.objects.create(
                title=f'Post {i}',
                slug=f'post-{i}',
                excerpt=f'Excerpt for post {i}',
                body=f'Body for post {i}',
                author=self.user
            ).categories.set([self.category])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        post_list = response.context['post_list']
        self.assertEqual(len(post_list), 10)

        self.assertTrue('paginator' in response.context)
        self.assertTrue('page_obj' in response.context)
        paginator = response.context['paginator']
        self.assertEqual(paginator.num_pages, 2)

    def test_post_ordering(self):
        post_3 = Post.objects.create(
            title='Post 3',
            slug='post-3',
            excerpt='Excerpt for post 3',
            body='Body for post 3',
            author=self.user
        ).categories.set([self.category])

        response = self.client.get(self.url)
        post_list = response.context['post_list']
        self.assertEqual(post_list[0].title, 'Post 3')  # 确保 Post 3 出现在最前面


class PostDetailViewTest(TestCase):
    """
    测试 PostDetailView 的功能:
    - 测试视图是否能够正确渲染文章详情页面
    - 验证视图的上下文数据
    - 测试文章的浏览次数是否正确增加
    - 确保文章的 Markdown 渲染正确
    - 测试 Breadcrumb 是否正确显示
    """

    def setUp(self):
        # 创建一个用户
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password'
        )

        # 创建分类和标签
        self.category = Category.objects.create(name='Django')
        self.tag = Tag.objects.create(name='Python')

        # 创建一篇文章
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            body='Test Body',
            excerpt='Test Excerpt',
            author=self.user
        )

        self.post.categories.add(self.category)
        self.post.tags.add(self.tag)

    def test_post_detail_view_status_code(self):
        url = reverse('blog:detail', kwargs={'slug': self.post.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_detail_view_context(self):
        url = reverse('blog:detail', kwargs={'slug': self.post.slug})
        response = self.client.get(url)

        # 检查模板是否正确渲染
        self.assertTemplateUsed(response, 'blog/post.html')  # 页面模板是 'blog/index.html'

        # 验证视图上下文
        self.assertIn('post', response.context)
        self.assertEqual(response.context['post'], self.post)

        # 验证 breadcrumbs
        self.assertIn('breadcrumbs', response.context)
        self.assertEqual(
            response.context['breadcrumbs'], [('首页', '/'), (self.post.title, self.post.get_absolute_url())]
        )

        # 验证 breadcrumbs_mobile
        self.assertIn('breadcrumbs_mobile', response.context)
        self.assertEqual(response.context['breadcrumbs_mobile'], ['文章'])

        # 验证 giscus_src
        self.assertIn('giscus_src', response.context)
        self.assertEqual(response.context['giscus_src']['term'], f'posts/{self.post.id}/')

    """
    判断 patch 路径正确性的规则：始终 patch “使用它的地方”，不是 “定义它的地方”。
    patch 使用：@patch('那个模块.xxx')
    """

    @patch('blog.views.PostDetailView.get_object')
    def test_increase_views(self, mock_get_object):
        # 模拟返回文章对象
        mock_get_object.return_value = self.post

        url = reverse('blog:detail', kwargs={'slug': self.post.slug})
        self.client.get(url)  # 访问文章页面

        # 检查浏览次数是否增加
        self.assertEqual(self.post.views, 1)  # 初始阅读量为 0

    @patch('blog.views.MarkdownIt.render')
    def test_markdown_rendering(self, mock_render):
        mock_render.return_value = '<h1>Test</h1>'

        url = reverse('blog:detail', kwargs={'slug': self.post.slug})
        response = self.client.get(url)

        # response.content 是原始的 HTTP 响应体，它的类型是 bytes。
        # 通常默认使用 UTF-8 编码
        self.assertIn('<h1>Test</h1>', response.content.decode())


class CategoryListViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='password')

        # 创建一些分类
        self.category1 = Category.objects.create(name='Technology')
        self.category2 = Category.objects.create(name='Lifestyle')

        # 为每个分类创建文章
        self.post1 = Post.objects.create(title='Test Post 1', body='Content 1', author=self.user)
        self.post1.categories.add(self.category1)

        self.post2 = Post.objects.create(title='Test Post 2', body='Content 2', author=self.user)
        self.post2.categories.add(self.category1)

        self.post3 = Post.objects.create(title='Test Post 3', body='Content 3', author=self.user)
        self.post3.categories.add(self.category2)

        # 获取视图的 URL
        self.url = reverse('blog:categories')

    def test_category_list_view_context(self):
        # 访问分类列表视图
        response = self.client.get(self.url)

        # 检查响应状态码是否为 200（OK）
        self.assertEqual(response.status_code, 200)

        # 检查模板是否正确渲染
        self.assertTemplateUsed(response, 'blog/categories.html')

        # 检查上下文中是否包含 category_list 和对应的 posts_list
        self.assertIn('category_list', response.context)
        categories = response.context['categories']
        self.assertEqual(len(categories), 2)  # 期望两个分类

        # 验证第一个分类的 posts_list
        self.assertTrue(hasattr(categories[0], 'posts_list'))
        self.assertEqual(len(categories[0].posts_list), 1)  # Lifestyle 分类下只有 1 篇文章

        # 验证第二个分类的 posts_list
        self.assertTrue(hasattr(categories[1], 'posts_list'))
        self.assertEqual(len(categories[1].posts_list), 2)  # Technology 分类下有 2 篇文章

    def test_get_breadcrumbs(self):
        view = CategoryListView()
        breadcrumbs = view.get_breadcrumbs()
        self.assertEqual(breadcrumbs, [('首页', '/'), ('分类', '/categories/')])

    def test_get_breadcrumbs_mobile(self):
        view = CategoryListView()
        breadcrumbs_mobile = view.get_breadcrumbs_mobile()
        self.assertEqual(breadcrumbs_mobile, ['分类'])


class CategoryDetailViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='password')

        # 创建一些分类
        self.category1 = Category.objects.create(name='Technology')
        self.category2 = Category.objects.create(name='Lifestyle')

        # 为每个分类创建文章
        self.post1 = Post.objects.create(title='Test Post 1', body='Content 1', author=self.user)
        self.post1.categories.add(self.category1)

        self.post2 = Post.objects.create(title='Test Post 2', body='Content 2', author=self.user)
        self.post2.categories.add(self.category1)

        self.post3 = Post.objects.create(title='Test Post 3', body='Content 3', author=self.user)
        self.post3.categories.add(self.category2)

        # 获取分类视图的 URL
        self.url = reverse('blog:category_detail', kwargs={'slug': self.category1.slug})

    def test_category_detail_view_context(self):
        # 访问分类详情视图
        response = self.client.get(self.url)

        # 检查视图是否成功返回
        self.assertEqual(response.status_code, 200)

        # 验证上下文中是否包含选择的分类和文章列表
        self.assertIn('selected_category', response.context)
        self.assertEqual(response.context['selected_category'], self.category1)

        related_posts = response.context['related_posts']
        self.assertEqual(len(related_posts), 2)  # Technology 分类下有 2 篇文章
        self.assertIn(self.post1, related_posts)
        self.assertIn(self.post2, related_posts)

    def test_get_breadcrumbs(self):
        view = CategoryDetailView()
        view.selected_category = self.category1  # 手动设置 selected_category
        breadcrumbs = view.get_breadcrumbs()

        self.assertEqual(breadcrumbs, [
            ('首页', '/'),
            ('分类', '/categories/'),
            (self.category1.name, self.category1.get_absolute_url())  # 使用分类的名称和 URL
        ])

    def test_get_breadcrumbs_mobile(self):
        view = CategoryDetailView()
        view.selected_category = self.category1
        breadcrumbs_mobile = view.get_breadcrumbs_mobile()

        self.assertEqual(breadcrumbs_mobile, ['分类'])

    def test_category_detail_view_no_category(self):
        # 测试不存在的分类 slug
        # 假设不存在的 slug 值 "non-existent-category"
        url = reverse('blog:category_detail', kwargs={'slug': 'nonexistent-category'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)


class TagListViewTest(TestCase):
    def setUp(self):
        # 创建用户
        self.user = get_user_model().objects.create_user(username='testuser', password='password')

        # 创建标签
        self.tag1 = Tag.objects.create(name='Python')
        self.tag2 = Tag.objects.create(name='Django')
        self.tag3 = Tag.objects.create(name='JavaScript')

        # 创建文章并关联标签
        self.post1 = Post.objects.create(title='Test Post 1', body='Content 1', author=self.user)
        self.post1.tags.add(self.tag1, self.tag2)

        self.post2 = Post.objects.create(title='Test Post 2', body='Content 2', author=self.user)
        self.post2.tags.add(self.tag1)

        self.post3 = Post.objects.create(title='Test Post 3', body='Content 3', author=self.user)
        self.post3.tags.add(self.tag2, self.tag3)

    def test_get_queryset(self):
        response = self.client.get(reverse('blog:tags'))

        tags = response.context['tag_list']

        # 检查标签列表是否按文章数量降序排列
        self.assertEqual(tags[0].name, 'Python')  # Python 标签下有 2 篇文章
        self.assertEqual(tags[1].name, 'Django')  # Django 标签下有 2 篇文章
        self.assertEqual(tags[2].name, 'JavaScript')  # JavaScript 标签下有 1 篇文章

        # 确保每个标签的 num_posts 被正确计算
        self.assertEqual(tags[0].num_posts, 2)
        self.assertEqual(tags[1].num_posts, 2)
        self.assertEqual(tags[2].num_posts, 1)

    def test_get_breadcrumbs(self):
        # 测试面包屑导航
        response = self.client.get(reverse('blog:tags'))
        self.assertEqual(response.context['breadcrumbs'], [('首页', '/'), ('标签', '/tags/')])

    def test_get_breadcrumbs_mobile(self):
        # 测试移动端面包屑导航
        response = self.client.get(reverse('blog:tags'))
        self.assertEqual(response.context['breadcrumbs_mobile'], ['标签'])


class TagDetailViewTest(TestCase):

    def setUp(self):
        # 创建用户
        self.user = get_user_model().objects.create_user(username='testuser', password='password')

        # 创建标签
        self.tag = Tag.objects.create(name='Python')

        # 创建文章并关联标签
        self.post1 = Post.objects.create(title='Test Post 1', body='Content 1', author=self.user)
        self.post1.tags.add(self.tag)
        self.post2 = Post.objects.create(title='Test Post 2', body='Content 2', author=self.user)
        self.post2.tags.add(self.tag)

        # 获取标签详情视图的 URL
        self.url = reverse('blog:tag_detail', kwargs={'slug': self.tag.slug})

    def test_tag_detail_view_status_code(self):
        # 测试页面是否加载成功
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_tag_detail_view_context(self):
        # 测试上下文是否包含正确的标签和文章列表
        response = self.client.get(self.url)
        context = response.context

        self.assertEqual(context['selected_tag'], self.tag)
        self.assertEqual(len(context['post_list']), 2)  # 标签下有 2 篇文章

    def test_no_post_for_tag(self):
        # 删除所有与标签关联的文章
        self.post1.delete()
        self.post2.delete()

        response = self.client.get(self.url)
        context = response.context

        self.assertEqual(len(context['post_list']), 0)

        # .wsgi_request 是原始的 HTTP 请求对象（包含中间件处理后的完整上下文）
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), '没有找到与此标签相关的文章')

    def test_tag_detail_view_empty_tag(self):
        # 测试不存在的标签返回 404
        # nonexistent 本身是一个字符串，在测试中常用来模拟请求不存在的对象
        response = self.client.get(reverse('blog:tag_detail', kwargs={'slug': 'nonexistent'}))
        self.assertEqual(response.status_code, 404)

    def test_get_breadcrumbs(self):
        # 测试面包屑导航
        response = self.client.get(self.url)
        context = response.context

        breadcrumbs = context['breadcrumbs']
        self.assertEqual(len(breadcrumbs), 3)  # 首页 + 标签 + 当前标签
        # 面包屑导航的最后一项应该是当前标签的名称和 URL
        self.assertEqual(breadcrumbs[2], (self.tag.name, self.tag.get_absolute_url()))

    def test_get_breadcrumbs_mobile(self):
        # 测试移动端面包屑导航
        response = self.client.get(self.url)
        context = response.context

        breadcrumbs_mobile = context['breadcrumbs_mobile']
        self.assertEqual(breadcrumbs_mobile, ['标签'])


class SearchViewTest(TestCase):
    def setUp(self):
        self.url = reverse('blog:search')

    def _create_mock_result(self, title='标题', snippet='正文'):
        mock_obj = MagicMock()
        mock_obj.get_absolute_url.return_value = '/test-url/'
        mock_obj.title = title
        mock_obj.categories.all.return_value = []
        mock_obj.tags.all.return_value = []
        mock_obj.body = snippet

        mock_result = MagicMock()
        mock_result.object = mock_obj
        mock_result.highlighted = [f'{title}\n{snippet}']
        return mock_result

    """
    @patch，按照从内向外装饰的顺序（即最靠近函数定义的 patch 最先被调用），参数注入时要与之完全相反顺序
    参数顺序 = 装饰器从下往上的顺序
    """

    @patch('blog.views.render_to_string')
    @patch('blog.views.normalize_highlight')
    @patch('blog.views.is_highlight_title_first')
    @patch('blog.views.SearchQuerySet')
    def test_search_ajax(
            self,
            mock_searchqueryset,
            mock_highlight_check,
            mock_standardize,
            mock_render_to_string,
    ):
        mock_result = self._create_mock_result('测试标题', '高亮正文内容')

        mock_searchqueryset.return_value.filter.return_value.highlight.return_value = [mock_result]
        mock_highlight_check.return_value = True
        mock_standardize.return_value = '标准化后的高亮内容'
        mock_render_to_string.return_value = '<div>Mock Results HTML</div>'

        # AJAX 请求
        response = self.client.get(
            self.url,
            {'q': '测试', 'page': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('results_html', data)
        self.assertEqual(data['results'][0]['title'], '测试标题')
        self.assertEqual(data['results'][0]['snippet'], '标准化后的高亮内容')

        # 非 AJAX 请求
        response = self.client.get(self.url, {'q': '测试'})  # 没有设置 XMLHttpRequest 头
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['error'], 'Only AJAX requests are supported.')

    @patch('blog.views.SearchQuerySet')
    def test_search_pagination(self, mock_searchqueryset):
        mock_results = [self._create_mock_result(f'标题{i}', f'正文{i}') for i in range(11)]
        # 返回多条搜索结果
        mock_searchqueryset.return_value.filter.return_value.highlight.return_value = [
            mock_result for mock_result in mock_results
        ]

        response = self.client.get(
            self.url,
            {'q': '测试', 'page': 2},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['has_previous'], True)
        self.assertEqual(data['has_next'], False)
        self.assertEqual(data['total_pages'], 2)
        self.assertEqual(len(data['results']), 1)  # 第二页只有 1 条数据

    @patch('blog.views.SearchQuerySet')
    def test_search_no_results(self, mock_searchqueryset):
        mock_searchqueryset.return_value.filter.return_value.highlight.return_value = []

        response = self.client.get(
            self.url,
            {'q': '不存在的关键字', 'page': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['results'], [])
        self.assertEqual(data['total_pages'], 1)
        self.assertEqual(data['has_previous'], False)
        self.assertEqual(data['has_next'], False)

    @patch('blog.views.SearchQuerySet')
    def test_illegal_page_number(self, mock_searchqueryset):
        mock_result = self._create_mock_result()
        mock_searchqueryset.return_value.filter.return_value.highlight.return_value = [mock_result]

        response = self.client.get(
            self.url,
            {'q': '测试', 'page': '9999'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )  # 不合法的页码

        # 检查返回的 JSON 中是否包含预期结果和分页信息
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('has_next', data)
        self.assertIn('has_previous', data)
        self.assertIn('next_page_number', data)
        self.assertIn('previous_page_number', data)
        self.assertIn('total_pages', data)
        self.assertEqual(data['has_previous'], False)
        self.assertEqual(data['has_next'], False)  # 因为只有1页数据，所以没有下一页
        self.assertEqual(data['total_pages'], 1)  # 只有1页数据
        self.assertEqual(data['results'], [{
            'url': '/test-url/',
            'title': '标题',
            'categories': '',
            'tags': '',
            'snippet': '正文'
        }])

    @patch('blog.views.SearchQuerySet')
    def test_invalid_page_input(self, mock_searchqueryset):
        mock_result = self._create_mock_result()

        mock_searchqueryset.return_value.filter.return_value.highlight.return_value = [mock_result]
        response = self.client.get(
            self.url,
            {'q': '测试', 'page': 'invalid'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(data['page'], 1)  # 默认页码为 1
        self.assertEqual(data['has_previous'], False)
        self.assertEqual(data['total_pages'], 1)

    @patch('blog.views.normalize_highlight')
    @patch('blog.views.is_highlight_title_first')
    @patch('blog.views.SearchQuerySet')
    def test_result_without_highlight(
            self,
            mock_searchqueryset,
            mock_highlight_check,
            mock_standardize,
    ):
        mock_result = self._create_mock_result()
        mock_result.highlighted = []

        mock_searchqueryset.return_value.filter.return_value.highlight.return_value = [mock_result]
        mock_highlight_check.return_value = False
        mock_standardize.return_value = '原始正文片段'

        response = self.client.get(
            self.url,
            {'q': '测试', 'page': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['results'][0]['snippet'], '原始正文片段')

    def test_search_without_query_param(self):
        response = self.client.get(
            self.url,
            {'page': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertIn('results', data)
        self.assertEqual(data['results'], [])  # 假设不返回搜索内容


class RobotsTxtTest(TestCase):
    def test_robots_txt_response(self):
        response = self.client.get('/robots.txt')

        # 检查响应状态码
        self.assertEqual(response.status_code, 200)

        # MIME 类型应为 text/plain
        self.assertEqual(response['Content-Type'], 'text/plain')

        # 检查响应内容
        expected_lines = [
            "User-agent: *",
            "Disallow: /admin/",
            "Allow: /",
            "Sitemap: https://quillnk.com/sitemap.xml"
        ]
        """
        response.content：获取响应体的原始字节内容（类型是bytes）
        .decode()：将字节内容解码为字符串，通常是 UTF-8 编码（默认行为）
        .splitlines()：将字符串按行切割，返回一个按行分割的 list
        """
        content_lines = response.content.decode().splitlines()
        for line in expected_lines:
            self.assertIn(line, content_lines)
