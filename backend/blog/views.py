from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from blog.models import Post, Category, Tag
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from blog.utils import render_markdown

from django.views.generic import DetailView
from django.views.generic import ListView
from django.urls import reverse
from django.db.models import Case, When, Value, F

from django.contrib import messages
from django.db.models import Q

from haystack.query import SearchQuerySet
from haystack.inputs import Exact
from haystack.inputs import AutoQuery
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from blog.utils import normalize_highlight, is_highlight_title_first

from django.db.models import Count
from django.db.models.functions import Coalesce, ExtractYear, TruncYear
from django.views.generic import TemplateView
from django.db.models import Prefetch
from blog.utils import update_obsidian_links

from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()


# def index(request):
#     return render(request, 'blog/index.html', context={
#         'title': '博客首页',
#         'welcome': '欢迎访问我的博客'
#     })


class BreadcrumbMixin:
    """
    为视图提供通用的面包屑导航支持。
    提供 PC 和移动端两套 breadcrumbs，上下文变量分别为：
    - breadcrumbs
    - breadcrumbs_mobile
    """

    def get_breadcrumbs(self):
        """
        返回 PC 端的面包屑导航列表。
        子类可重写此方法，自定义导航结构。
        """
        return []

    def get_breadcrumbs_mobile(self):
        """
        返回移动端的面包屑导航列表。
        默认与 PC 端相同，可在子类中重写。
        """
        return self.get_breadcrumbs()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'breadcrumbs': self.get_breadcrumbs(),
            'breadcrumbs_mobile': self.get_breadcrumbs_mobile(),
        })
        return context


# 用于处理 Post 模型对象列表的视图逻辑
class IndexView(BreadcrumbMixin, ListView):
    """
    类的继承顺序影响类的继承链（MRO，方法解析顺序）。
    类的继承链：IndexView -> BreadcrumbMixin -> ListView -> TemplateView -> View -> object
    get_context_data 未显式定义时，super() 会按 MRO 顺序查找 get_context_data 方法。
    所以，首先，会调用 BreadcrumbMixin 中的 get_context_data 方法；
    然后，其中的 super().get_context_data(**kwargs)，会触发调用下一个类 ListView 中的 get_context_data 方法，最终返回正确的上下文数据。
    """
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    # 指定 paginate_by 属性后开启分页功能，其值代表每页有多少个文章
    paginate_by = 10

    # # 先按照文章创建时间倒序排列，如果创建时间相同，则按照文章修改时间倒序排列
    # # 这样的排序对那些没有 modified_time 的文章会有问题，不适合modified_time字段为空的情况
    # ordering = ['-modified_time', '-created_time']

    def get_queryset(self):
        # 获取基础查询集
        queryset = super().get_queryset() \
            .only('pk', 'title', 'slug', 'excerpt', 'created_time', 'modified_time') \
            .prefetch_related(Prefetch('categories', queryset=Category.objects.only('name')))

        # 首先按修改时间排序，如果么有，使用创建时间排序，动态选择合适的时间字段用于排序
        return queryset.annotate(  # 使用 annotate() 方法添加额外的字段
            ordering_time=Case(
                When(modified_time__isnull=False, then=F('modified_time')),
                When(modified_time__isnull=True, then=F('created_time')),
                default=F('created_time'),
            )
        ).order_by('-ordering_time')

    def get_breadcrumbs(self):
        return [
            {'title': '首页', 'url': reverse('blog:index')},
        ]

    def get_breadcrumbs_mobile(self):
        return [
            {'title': '首页'}
        ]


class PostDetailView(BreadcrumbMixin, DetailView):
    model = Post
    template_name = 'blog/post.html'
    context_object_name = 'post'

    def get_queryset(self):
        # 获取查询集：优化查询，关联外键字段
        queryset = Post.objects.select_related('author').prefetch_related('categories', 'tags')
        return queryset

    def get_object(self, queryset=None):
        """重写方法，获取特定文章对象"""
        queryset = self.get_queryset()
        return get_object_or_404(queryset, slug=self.kwargs.get('slug'))

    def get_context_data(self, **kwargs):
        """重写方法，添加额外的上下文数据"""
        context = super().get_context_data(**kwargs)  # 返回包含上下文数据的的字典
        post = self.object  # 获取当前文章对象

        # 阅读量 +1
        post.increase_views()

        # 如果文章的正文或目录为空，则使用 Markdown 渲染器进行渲染
        if not post.rendered_body or not post.toc:
            post.rendered_body, post.toc = render_markdown(post.body, title=post.title)

        # 将处理后的 post 对象传递给模板
        context['post'] = post

        return context

    def get_breadcrumbs(self):
        post = getattr(self, 'object', None)
        if not post:
            post = self.get_object()
        return [
            {'title': '首页', 'url': reverse('blog:index')},
            {'title': post.title, 'url': ''}  # 当前页通常不设链接
        ]

    def get_breadcrumbs_mobile(self):
        return [
            {'title': '文章'}
        ]


class CategoryListView(BreadcrumbMixin, ListView, ):
    model = Category
    template_name = 'blog/categories.html'
    context_object_name = 'category_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = Category.objects.filter(parent__isnull=True).order_by('name')
        for category in categories:
            # 查询该分类下的文章并仅获取需要的字段
            posts = category.post_set.only('title', 'created_time', 'modified_time').order_by('-created_time')
            # 为每个类别动态设置 posts_list 属性
            category.posts_list = posts

        context['categories'] = categories

        return context

    def get_breadcrumbs(self):
        return [
            {'title': '首页', 'url': reverse('blog:index')},
            {'title': '分类', 'url': ''},  # 当前页通常不设链接
        ]

    def get_breadcrumbs_mobile(self):
        return [
            {'title': '分类'}
        ]


class CategoryDetailView(BreadcrumbMixin, ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'related_posts'

    @cached_property
    def selected_category(self):
        category_slug = self.kwargs.get('slug', None)  # 获取 URL 中的分类 slug 参数
        return get_object_or_404(Category, slug=category_slug)

    def get_queryset(self, **kwargs):
        # 使用 select_related 和prefetch_related 来预加载相关对象，提高查询效率
        # return Post.objects.filter(categories=selected_category).select_related('author').prefetch_related('tags')
        return Post.objects.filter(categories=self.selected_category).only('title', 'created_time', 'modified_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_category'] = getattr(self, 'selected_category', None)  # 使用视图实例中的分类实例

        return context

    def get_breadcrumbs(self):
        return [
            {'title': '首页', 'url': reverse('blog:index')},
            {'title': '分类', 'url': reverse('blog:categories')},
            {'title': self.selected_category.name, 'url': ''},
        ]

    def get_breadcrumbs_mobile(self):
        return [
            {'title': '分类'}
        ]


class TagListView(BreadcrumbMixin, ListView):
    model = Tag
    template_name = 'blog/tags.html'
    context_object_name = 'tag_list'

    def get_queryset(self):
        # 使用annotate来计算每个标签下的文章数量
        return Tag.objects.annotate(
            num_posts=Count('post')  # 聚合函数，计算与每个标签关联的文章数量
        ).order_by('-num_posts')  # 按照文章数量降序排列

    def get_breadcrumbs(self):
        return [
            {'title': '首页', 'url': reverse('blog:index')},
            {'title': '标签', 'url': ''},
        ]

    def get_breadcrumbs_mobile(self):
        return [
            {'title': '标签'}
        ]


class TagDetailView(BreadcrumbMixin, ListView):
    model = Post
    template_name = 'blog/tag.html'
    context_object_name = 'post_list'

    @cached_property
    def selected_tag(self):
        tag_slug = self.kwargs.get('slug', None)  # 获取 URL 中的标签 slug 参数
        return get_object_or_404(Tag, slug=tag_slug)

    # 重写 get_queryset 方法，用于自定义查询集
    def get_queryset(self):
        # 获取该标签下的文章，优化查询：只加载必要的字段并预加载关联字段
        post_list = super().get_queryset() \
            .filter(tags=self.selected_tag) \
            .only('pk', 'title', 'created_time', 'modified_time') \
            .order_by('-created_time')

        return post_list if post_list.exists() else Post.objects.none()

    def get_context_data(self, **kwargs):
        # 获取父类的上下文数据
        context = super().get_context_data(**kwargs)

        # 将当前标签实例添加到上下文中，便于在模板中使用
        context['selected_tag'] = getattr(self, 'selected_tag', None)

        # 如果没有找到相关文章，则添加提示信息
        if not context['post_list']:
            messages.info(self.request, '没有找到与此标签相关的文章')

        return context

    def get_breadcrumbs(self):
        return [
            {'title': '首页', 'url': reverse('blog:index')},
            {'title': '标签', 'url': reverse('blog:tags')},
            {'title': self.selected_tag.name, 'url': ''},
        ]

    def get_breadcrumbs_mobile(self):
        return [
            {'title': '标签'}
        ]


class ArchiveView(BreadcrumbMixin, ListView):
    model = Post
    template_name = 'blog/archives.html'
    context_object_name = 'post_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 使用annotate添加一个新的排序字段sort_time，该字段是modified_time和created_time的降序排列
        # Coalease函数用于处理空值，如果modified_time为空，则使用created_time
        # ExtractYear函数用于提取日期的年份部分
        # posts = super(ArchiveView, self).get_queryset().annotate(
        #     year=ExtractYear(Coalesce('modified_time', 'created_time')),
        # ).order_by('-year', Coalesce('modified_time', 'created_time').desc())

        posts = super(ArchiveView, self).get_queryset().annotate(
            year=ExtractYear(Coalesce('modified_time', 'created_time')),
        ).only('title', 'modified_time', 'created_time') \
            .order_by('-year', Coalesce('modified_time', 'created_time').desc())

        # 按年份分组
        post_list_by_year = {}
        for post in posts:
            year = post.year
            if year not in post_list_by_year:
                post_list_by_year[year] = []
            post_list_by_year[year].append(post)
        context['post_list_by_year'] = post_list_by_year

        return context

    def get_breadcrumbs(self):
        return [
            {'title': '首页', 'url': reverse('blog:index')},
            {'title': '归档', 'url': ''},
        ]

    def get_breadcrumbs_mobile(self):
        return [
            {'title': '归档'}
        ]


class AboutView(BreadcrumbMixin, TemplateView):
    template_name = 'blog/about.html'

    def get_breadcrumbs(self):
        return [
            {'title': '首页', 'url': reverse('blog:index')},
            {'title': '关于', 'url': ''},
        ]

    def get_breadcrumbs_mobile(self):
        return [
            {'title': '关于'}
        ]


# def search(request):
#     # 从 GET 请求中获取搜索关键词 q 的参数值
#     q = request.GET.get('q')
#
#     # 如果 q 为空，则返回一个包含错误消息的 HttpResponse 对象
#     if not q:
#         error_msg = '请输入搜索关键词'
#         messages.add_message(request, messages.ERROR, error_msg)
#         return redirect('blog:index')
#
#     # 使用 Q 对象进行模糊搜索，并返回搜索结果
#     # 查找标题或正文中包含搜索关键词 q 的所有 Post 对象
#     post_list = Post.objects.filter(Q(title__icontains=q) | Q(body__icontains=q))
#
#     # 渲染模板，并将搜索结果传递给模板
#     return render(request, 'blog/index.html', {'post_list': post_list})


def search(request):
    # 从请求中获取查询参数 q，如果没有提供，则默认为空字符串
    query = request.GET.get('q', '')
    # 从请求中获取当前页码，如果没有提供页码，默认设置为 1
    page_number = request.GET.get('page', 1)

    try:
        # sqs = SearchQuerySet().filter(content=query).highlight()
        sqs = SearchQuerySet().filter(content=Exact(query)).highlight()  # 整个关键词作为单一的短语进行匹配，而不会分词

        # 使用 Django 的分页器创建分页对象，假设每页显示 10 条结果
        paginator = Paginator(sqs, 10)

        # 尝试获取用户请求的页码对应的分页内容
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # 如果页码不是整数（例如是字母），则返回第一页
        page_obj = paginator.page(1)
    except EmptyPage:
        # 如果页码超出总页数范围，则返回最后一页
        page_obj = paginator.page(paginator.num_pages)

    # 将搜索结果转换为 JSON 格式
    # 查询匹配的高亮内容是一个列表，每个元素是一个包含高亮内容的字符串
    # 单一匹配项的高亮内容可能包含多个部分，例如标题和正文，可以通过换行符 '\n' 进行分割
    results = [{
        'url': result.object.get_absolute_url(),
        'title': (
            result.highlighted[0].split('\n')[0]
            # if (result.highlighted and (query in result.object.title))
            if is_highlight_title_first(result.highlighted, result.object.title)
            else result.object.title
        ),
        'categories': ', '.join([category.name for category in result.object.categories.all()]),
        'tags': ', '.join([tag.name for tag in result.object.tags.all()]),
        'snippet': (
            normalize_highlight(result.highlighted[0].split('\n')[1:])  # 高亮内容匹配标题的情况
            if is_highlight_title_first(result.highlighted, result.object.title)
            else (
                normalize_highlight(result.highlighted[0])  # 高亮内容不匹配标题的情况
                if result.highlighted
                else normalize_highlight(result.object.body[:150])  # 没有高亮内容时，返回正文前150个字符
            )
        )
    } for result in page_obj]

    # for result in page_obj:
    #     print("result.highlighted:", result.highlighted)

    data = {
        'query': query,
        # 'page_obj': page,  # JSON 序列化时，Page 对象无法直接序列化
        'page': page_obj.number,
        'results': results,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
        'total_pages': paginator.num_pages
    }

    # 判断是否是 AJAX 请求
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 如果是 AJAX 请求，返回 JSON 数据，包含查询结果和分页信息
        results_html = render_to_string('_includes/search-loader.html',
                                        {'query': query, 'page_obj': page_obj, 'results': results})
        data['results_html'] = results_html
        # print("results_html:", results_html)

        return JsonResponse(data)

    # return redirect('/')  # 重定向到首页
    # 非 AJAX 请求处理逻辑（如果有需要返回完整的 HTML 页面，可以在这里处理）
    return JsonResponse({'error': 'Only AJAX requests are supported.'})


def robots_txt(request):
    """用于动态生成 robots.txt 文件"""
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Sitemap: https://quillnk.com/sitemap.xml"
    ]

    return HttpResponse("\n".join(lines), content_type="text/plain")
