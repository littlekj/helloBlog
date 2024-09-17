from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from blog.models import Post, Category, Tag
from django.shortcuts import get_object_or_404

import re
from markdown_it import MarkdownIt
from blog.utils import generate_toc, replace_markdown_symbols, slugify
from mdit_py_plugins.anchors import anchors_plugin

from django.views.generic import DetailView
from django.views.generic import ListView
from django.db.models import Case, When, Value, F

from django.contrib import messages
from django.db.models import Q

from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from blog.utils import standardize_highlight

from django.db.models import Count
from django.db.models.functions import Coalesce, ExtractYear, TruncYear
from django.views.generic import TemplateView

import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()


# def index(request):
#     return HttpResponse("欢迎访问我的博客首页！")


# def index(request):
#     return render(request, 'blog/index.html', context={
#         'title': '博客首页',
#         'welcome': '欢迎访问我的博客'
#     })


# 面包屑导航
class BreadcrumbMixin:
    def get_breadcrumbs(self):
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context


# 用于处理 Post 模型对象列表的视图逻辑
class IndexView(BreadcrumbMixin, ListView):
    """
    类的继承顺序影响方法解析顺序MRO。
    首先调用 BreadcrumbMixin 的 get_context_data 方法中，super().get_context_data(**kwargs)
    super()的指定会调用下一个类 ListView 中的 get_context_data 方法，从而获取基础的上下文数据。
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
        queryset = super().get_queryset()

        # 首先按修改时间排序，如果么有，使用创建时间排序，动态选择合适的时间字段用于排序
        return queryset.annotate(  # 使用 annotate() 方法添加额外的字段
            ordering_time=Case(
                When(modified_time__isnull=False, then=F('modified_time')),
                When(modified_time__isnull=False, then=F('created_time')),
                default=F('created_time'),
            )
        ).order_by('-ordering_time')

    def get_breadcrumbs(self):
        return [
            ('首页', '/'),
        ]


class PostDetailView(BreadcrumbMixin, DetailView):
    model = Post
    template_name = 'blog/post.html'
    context_object_name = 'post'

    # 生成渲染模板时需要的上下文数据
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # 返回包含上下文数据的的字典
        post = self.object  # 获取当前文章对象

        # 阅读量 +1
        post.increase_views()

        # 替换 Markdown 标题中的特殊符号
        post.body = replace_markdown_symbols(post.body)

        # 渲染 Markdown 内容
        md = MarkdownIt('gfm-like')
        md.use(anchors_plugin, min_level=2, max_level=4, slug_func=slugify,
               permalink=True, permalinkSymbol='', permalinkBefore=False, permalinkSpace=True)

        # 生成目录
        post.toc = generate_toc(md, post.body)
        # print("post.toc:", post.toc)

        post.body = md.render(post.body)

        # Prism.js 添加类异常，为代码块添加行号类
        post.body = post.body.replace('<pre><code', '<pre class="line-numbers"><code')

        # 将处理后的 post 对象传递给模板
        context['post'] = post

        # 添加 Giscus 小部件相关的变量
        giscus_src = {
            "origin": self.request.build_absolute_uri(),  # 当前页面的完整 URL
            "repo": "littlekj/helloBlog",  # GitHub 仓库的名称
            "repoId": "R_kgDOMfjaxQ",  # GitHub 仓库的 ID
            "category": "Announcements",  # 评论分类
            "categoryId": "DIC_kwDOMfjaxc4Cie3I",  # 评论分类的 ID
            "theme": "light",  # 主题颜色
            "reactionsEnabled": "1",  # 是否启用表情反应
            "emitMetadata": "0",  # 是否发送元数据
            "inputPosition": "top",  # 输入框的位置
            "term": f"posts/{post.id}/",  # 与当前页面的唯一标识符，用于映射评论与具体的页面或路径
            "description": post.title,  # 评论的描述
            "backLink": self.request.build_absolute_uri()  # 返回链接
        }

        context = {
            'post': post,
            'giscus_src': giscus_src
        }

        # print("context['giscus_src']", context['giscus_src'])
        return context

    def get_breadcrumbs(self):
        return [
            ('首页', '/'),
            (self.object.title, self.object.get_absolute_url()),
        ]


class CategoryListView(BreadcrumbMixin, ListView):
    model = Category
    template_name = 'blog/categories.html'
    context_object_name = 'category_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent__isnull=True).order_by('name')

        return context

    def get_breadcrumbs(self):
        return [
            ('首页', '/'),
            ('分类', '/categories/'),
        ]


class CategoryDetailView(BreadcrumbMixin, ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'related_posts'

    def get_queryset(self, **kwargs):
        category_slug = self.kwargs.get('slug', None)  # 获取URL中的slug参数
        if category_slug:
            selected_category = get_object_or_404(Category, slug=category_slug)
            self.selected_category = selected_category  # 将分类实例保存在视图实例中
            return Post.objects.filter(categories=selected_category)  # 获取该分类下的所有文章

        return Post.objects.none()  # 如果没有分类，返回空的文章列表

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_category'] = getattr(self, 'selected_category', None)  # 使用视图实例中的分类实例

        return context

    def get_breadcrumbs(self):
        return [
            ('首页', '/'),
            ('分类', '/categories/'),
            (self.selected_category, self.selected_category.get_absolute_url()),
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
            ('首页', '/'),
            ('标签', '/tags/'),
        ]


class TagDetailView(BreadcrumbMixin, ListView):
    model = Post
    template_name = 'blog/tag.html'
    context_object_name = 'post_list'

    # 重写 get_queryset 方法，用于自定义查询集
    def get_queryset(self):
        tag_slug = self.kwargs.get('slug', None)
        if tag_slug:
            selected_tag = get_object_or_404(Tag, slug=tag_slug)
            self.selected_tag = selected_tag  # 将标签实例保存在视图实例中
            post_list = super(TagDetailView, self).get_queryset().filter(tags=selected_tag).order_by('-created_time')
            if not post_list.exists():
                messages.info(self.request, '没有找到与此标签相关的文章')
            return post_list
        return super(TagDetailView, self).get_queryset().none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_tag'] = getattr(self, 'selected_tag', None)  # 使用视图实例中的标签实例，None 是当属性不存在时的默认值。
        return context

    def get_breadcrumbs(self):
        return [
            ('首页', '/'),
            ('标签', '/tags/'),
            (self.selected_tag.name, self.selected_tag.get_absolute_url()),
        ]


# def archive(request, year, month):
#     """
#     访问文章归档页
#     :param year: 年份
#     :param month: 月份
#     """
#     post_list = Post.objects.filter(
#         created_time__year=year,  # created_time 是 date 对象，__year 是 date 对象的属性
#         created_time__month=month
#     ).order_by('-created_time')
#
#     return render(request, 'blog/index.html', context={'post_list': post_list})

class ArchiveView(BreadcrumbMixin, ListView):
    model = Post
    template_name = 'blog/archives.html'
    context_object_name = 'post_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 使用annotate添加一个新的排序字段sort_time，该字段是modified_time和created_time的降序排列
        # Coalease函数用于处理空值，如果modified_time为空，则使用created_time
        # ExtractYear函数用于提取日期的年份部分
        posts = super(ArchiveView, self).get_queryset().annotate(
            year=ExtractYear(Coalesce('modified_time', 'created_time')),
        ).order_by('-year', Coalesce('modified_time', 'created_time').desc())
        # print("str(posts.query)", str(posts.query))

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
            ('首页', '/'),
            ('归档', '/archives/'),
        ]


class AboutView(BreadcrumbMixin, TemplateView):
    template_name = 'blog/about.html'

    def get_breadcrumbs(self):
        return [
            ('首页', '/'),
            ('关于', '/about/'),
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

    sqs = SearchQuerySet().filter(content=query).highlight()
    # sqs = SearchQuerySet().filter(content__exact=query).highlight()  # content_exact 表示精确匹配

    # 使用 Django 的分页器创建分页对象，假设每页显示 10 条结果
    paginator = Paginator(sqs, 16)

    try:
        page = paginator.page(page_number)  # 返回从给定页码的 Page 对象数据
    except PageNotAnInteger:
        page = paginator.page(1)  # 如果页码不是整数，则返回第一页的数据
    except EmptyPage:
        page = paginator.page(paginator.num_pages)  # 如果页码超出范围，则返回最后一页的数据

    # for result in page:
    #     print('result:', result)
    #     print('result.highlighted:', result.highlighted)

    # 将搜索结果转换为 JSON 格式
    # 查询匹配的高亮内容是一个列表，每个元素是一个包含高亮内容的字符串
    # 单一匹配项的高亮内容可能包含多个部分，例如标题和正文，可以通过换行符 '\n' 进行分割
    results = [{
        'url': result.object.get_absolute_url(),
        'title': (
            result.highlighted[0].split('\n')[0]
            if (result.highlighted and (query in result.object.title))
            else result.object.title
        ),
        'categories': ', '.join([category.name for category in result.object.categories.all()]),
        'tags': ', '.join([tag.name for tag in result.object.tags.all()]),
        'snippet': (
            standardize_highlight(result.highlighted[0].split('\n')[1:])  # 高亮内容匹配标题的情况
            if result.highlighted and (query in result.object.title)
            else (
                standardize_highlight(result.highlighted[0])  # 高亮内容不匹配标题的情况
                if result.highlighted and (query in result.object.title)
                else standardize_highlight(result.object.body[:150])  # 没有高亮内容时，返回正文前150个字符
            )
        )
    } for result in page]

    data = {
        'query': query,
        # 'page_obj': page,  # JSON 序列化时，Page 对象无法直接序列化
        'results': results,
        'has_next': page.has_next(),
        'has_previous': page.has_previous(),
        'next_page_number': page.next_page_number() if page.has_next() else None,
        'previous_page_number': page.previous_page_number() if page.has_previous() else None,
        'total_pages': paginator.num_pages
    }

    # 判断是否是 AJAX 请求
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 如果是 AJAX 请求，返回 JSON 数据，包含查询结果和分页信息
        results_html = render_to_string('_includes/search-loader.html',
                                        {'query': query, 'page_obj': page, 'results': results})
        data['results_html'] = results_html
        # print("results_html:", results_html)

        return JsonResponse(data)

    # return redirect('/')  # 重定向到首页
    # 非 AJAX 请求处理逻辑（如果有需要返回完整的 HTML 页面，可以在这里处理）
    return JsonResponse({'error': 'Only AJAX requests are supported.'})
