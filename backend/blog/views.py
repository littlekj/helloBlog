from django.http import HttpResponse
from django.shortcuts import render
from blog.models import Post, Category, Tag
from django.shortcuts import get_object_or_404
import markdown
import re
from markdown.extensions.toc import TocExtension
# from django.utils.text import slugify

from markdown_it import MarkdownIt
from blog.utils import generate_toc, replace_markdown_symbols, slugify
from mdit_py_plugins.anchors import anchors_plugin


# Create your views here.


# def index(request):
#     return HttpResponse("欢迎访问我的博客首页！")


# def index(request):
#     return render(request, 'blog/index.html', context={
#         'title': '博客首页',
#         'welcome': '欢迎访问我的博客'
#     })


def index(request):
    post_list = Post.objects.all().order_by('-created_time')
    return render(request, 'blog/index.html', context={'post_list': post_list})


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


def detail(request, pk):
    """
    访问文章详情页
    :param pk: 文章的 id
    """
    # 获取文章对象，如果不存在则返回 404 错误
    post = get_object_or_404(Post, pk=pk)

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
    # print("post.body:", post.body)

    return render(request, 'blog/detail.html', context={'post': post})


def archive(request, year, month):
    """
    访问文章归档页
    :param year: 年份
    :param month: 月份
    """
    post_list = Post.objects.filter(
        created_time__year=year,  # created_time 是 date 对象，__year 是 date 对象的属性
        created_time__month=month
    ).order_by('-created_time')

    return render(request, 'blog/index.html', context={'post_list': post_list})


def category(request, pk):
    """
    访问文章分类页
    :param pk: 分类 id
    """
    # 获取分类对象，如果找不到则返回 404 错误
    cate = get_object_or_404(Category, pk=pk)
    post_list = Post.objects.filter(category=cate).order_by('-created_time')

    return render(request, 'blog/index.html', {'post_list': post_list})


def tag(request, pk):
    """
    访问文章标签页
    :param pk: 标签 id
    """
    # 获取标签对象，如果找不到则返回 404 错误
    t = get_object_or_404(Tag, pk=pk)
    post_list = Post.objects.filter(tags=t).order_by('-created_time')

    return render(request, 'blog/index.html', {'post_list': post_list})
