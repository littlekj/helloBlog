from django.http import HttpResponse
from django.shortcuts import render, redirect
from blog.models import Post, Category, Tag
from django.shortcuts import get_object_or_404

import re
from markdown_it import MarkdownIt
from blog.utils import generate_toc, replace_markdown_symbols, slugify
from mdit_py_plugins.anchors import anchors_plugin

from django.views.generic import DetailView
from django.views.generic import ListView

from django.contrib import messages
from django.db.models import Q

from haystack.query import SearchQuerySet
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


# Create your views here.


# def index(request):
#     return HttpResponse("欢迎访问我的博客首页！")


# def index(request):
#     return render(request, 'blog/index.html', context={
#         'title': '博客首页',
#         'welcome': '欢迎访问我的博客'
#     })


# def index(request):
#     post_list = Post.objects.all().order_by('-created_time')
#     return render(request, 'blog/index.html', context={'post_list': post_list})


# 用于处理 Post 模型对象列表的视图逻辑
class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'

    # 指定 paginate_by 属性后开启分页功能，其值代表每页有多少个文章
    paginate_by = 10


# def detail(request, pk):
#     """
#     访问文章详情页
#     :param pk: 文章的 id
#     """
#     # 获取文章对象，如果不存在则返回 404 错误
#     post = get_object_or_404(Post, pk=pk)
#
#     md = markdown.Markdown(extensions=[
#         'markdown.extensions.extra',  # 包含很多有用的扩展，如表格、代码块、脚注等
#         'markdown.extensions.codehilite',  # 用于代码高亮
#         # 'markdown.extensions.toc',  # 生成目录
#         TocExtension(slugify=slugify),  # 更好地处理中文标题的锚点值
#     ])
#
#     # 渲染 Markdown 内容
#     post.body = md.convert(post.body)
#     print('post.body:', post.body)
#     print('md.toc:', md.toc)
#
#     # 提取目录（TOC）
#     # 使用 re.S（re.DOTALL）标志后，点号 . 将会匹配所有字符，包括换行符。
#     toc_match = re.search(r'<div class="toc">\s*<ul>(.*)</ul>\s*</div>', md.toc, re.S)
#     post.toc = toc_match.group(1) if toc_match else ''
#
#     # 渲染模板，并传递文章内容
#     return render(request, 'blog/detail.html', context={'post': post})


# def detail(request, pk):
#     """
#     访问文章详情页
#     :param pk: 文章的 id
#     """
#     # 获取文章对象，如果不存在则返回 404 错误
#     post = get_object_or_404(Post, pk=pk)
#
#     # 阅读量 +1
#     post.increase_views()
#
#     # 替换 Markdown 标题中的特殊符号
#     post.body = replace_markdown_symbols(post.body)
#
#     # 渲染 Markdown 内容
#     md = MarkdownIt('gfm-like')
#     md.use(anchors_plugin, min_level=2, max_level=4, slug_func=slugify,
#            permalink=True, permalinkSymbol='¶', permalinkBefore=False, permalinkSpace=True)
#
#     # 生成目录
#     post.toc = generate_toc(md, post.body)
#     # print("post.toc:", post.toc)
#     # toc_match = re.search(r'<div class="toc">\s*<ul>(.*)</ul>\s*</div>', post.toc, re.S)
#     # post.toc = toc_match.group(1) if toc_match else ''
#
#     post.body = md.render(post.body)
#
#     # Prism.js 添加类异常，为代码块添加行号类
#     post.body = post.body.replace('<pre><code', '<pre class="line-numbers"><code')
#     # print("post.body:", post.body)
#
#     return render(request, 'blog/detail.html', context={'post': post})


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
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
               permalink=True, permalinkSymbol='¶', permalinkBefore=False, permalinkSpace=True)

        # 生成目录
        post.toc = generate_toc(md, post.body)
        # print("post.toc:", post.toc)
        # toc_match = re.search(r'<div class="toc">\s*<ul>(.*)</ul>\s*</div>', post.toc, re.S)
        # post.toc = toc_match.group(1) if toc_match else ''

        post.body = md.render(post.body)

        # Prism.js 添加类异常，为代码块添加行号类
        post.body = post.body.replace('<pre><code', '<pre class="line-numbers"><code')

        # 将处理后的 post 对象传递给模板
        context['post'] = post
        return context


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

class ArchiveView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'

    def get_queryset(self):
        # 通过 URL 中的 year 和 month 参数获取文章列表，并按创建时间降序排列
        return super(ArchiveView, self).get_queryset().filter(
            created_time__year=self.kwargs.get('year'),
            created_time__month=self.kwargs.get('month')).order_by('-created_time')


# def category(request, pk):
#     """
#     访问文章分类页
#     :param pk: 分类 id
#     """
#     # 获取分类对象，如果找不到则返回 404 错误
#     cate = get_object_or_404(Category, pk=pk)
#     post_list = Post.objects.filter(category=cate).order_by('-created_time')
#
#     return render(request, 'blog/index.html', {'post_list': post_list})

class CategoryView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'

    # 重写 get_queryset 方法，用于自定义查询集
    def get_queryset(self):
        # 通过 URL 中的 pk 参数获取 Category 对象，如果找不到则返回 404 错误
        cate = get_object_or_404(Category, pk=self.kwargs.get('pk'))

        # 使用父类的 get_queryset 方法获取初始查询集，并过滤出属于指定分类的文章
        return super(CategoryView, self).get_queryset().filter(
            category=cate).order_by('-created_time')


# def tag(request, pk):
#     """
#     访问文章标签页
#     :param pk: 标签 id
#     """
#     # 获取标签对象，如果找不到则返回 404 错误
#     t = get_object_or_404(Tag, pk=pk)
#     post_list = Post.objects.filter(tags=t).order_by('-created_time')
#
#     return render(request, 'blog/index.html', {'post_list': post_list})

class TagView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'

    # 重写 get_queryset 方法，用于自定义查询集
    def get_queryset(self):
        t = get_object_or_404(Tag, pk=self.kwargs.get('pk'))
        return super(TagView, self).get_queryset().filter(tags=t).order_by('-created_time')


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

    # sqs = SearchQuerySet().filter(content=query)
    sqs = SearchQuerySet().filter(content__exact=query)  # content_exact 表示精确匹配

    # 使用 Django 的分页器对搜索结果进行分页，每页显示 10 条结果
    paginator = Paginator(sqs, 10)
    # 从请求中获取当前页码，如果没有提供页码，默认设置为 1
    page_number = request.GET.get('page', 1)

    try:
        page = paginator.page(page_number)  # 返回从给定页码的 Page 对象数据
        print("page :", page)
    except PageNotAnInteger:
        page = paginator.page(1)   # 如果页码不是整数，则返回第一页的数据
    except EmptyPage:
        page = paginator.page(paginator.num_pages)  # 如果页码超出范围，则返回最后一页的数据

    # 将查询参数和分页数据传递给模板上下文
    context = {
        'query': query,
        'page': page,
    }

    # 渲染模板，并将上下文传递给模板
    return render(request, 'search/search.html', context)
