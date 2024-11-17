from django import template
from blog.models import Post, Category, Tag
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache
from django.db.models.functions import Coalesce

from django.db.models.aggregates import Count

import re
from django.utils.html import strip_tags

from django.shortcuts import get_object_or_404
from urllib.parse import quote

# 创建一个模板库实例
register = template.Library()


# 装饰器将函数注册为模板标签，指定渲染的模板路径，将视图逻辑嵌入到模板中
# @register.inclusion_tag('blog/inclusions/_recent_posts.html', takes_context=True)
@register.inclusion_tag('_includes/update-list.html', takes_context=True)
def show_recent_posts(context, num=5):
    """
    显示最近发布的文章
    param context(dict): 模板上下文
    param num(int): 显示的文章数量
    return: (dict): 包含最近发布的文章的模板上下文
    """

    # 生成的缓存键，用于存储和检索缓存数据
    cache_key = f'recent_posts_{num}'

    # 尝试从缓存中检索数据
    recent_posts = cache.get(cache_key)

    # 查询数据并实现分页和缓存
    if not recent_posts:
        try:
            # 查询所有博客文章，按修改时间降序或创建时间降序排序，限制为前num个
            recent_posts = Post.objects.order_by(Coalesce('modified_time', 'created_time').desc()).only('pk', 'title')[
                           :num]
            # 将查询结果存储到缓存中，设置有效时间为600秒
            cache.set(cache_key, recent_posts, timeout=600)
        except Exception as e:
            print(f'Error fecthing recent posts: {e}')
            recent_posts = []

    # 返回给模板的数据字典
    return {
        'recent_posts': recent_posts
    }


@register.inclusion_tag('_includes/trending-tags.html', takes_context=True)
def show_trending_tags(context, num=10):
    """
    显示文章的热门标签
    :param context(dict): 模板上下文
    """

    # 获取所有标签并按管理文章数排序，限制为前10个
    tags = Tag.objects.annotate(num_posts=Count('post')).filter(num_posts__gt=0).order_by('-num_posts')[:num]
    return {
        'trending_tags': tags
    }


@register.inclusion_tag('_includes/trending-content.html', takes_context=True)
def show_trending_content(context, num=10):
    """
    显示文章的热门标签
    :param context(dict): 模板上下文
    """

    # 获取所有标签并按管理文章数排序，限制为前10个
    tags = Tag.objects.annotate(num_posts=Count('post')).filter(num_posts__gt=0).order_by('-num_posts')[:num]
    return {
        'trending_tags': tags
    }


@register.inclusion_tag('blog/inclusions/_archives.html', takes_context=True)
def show_archives(context):
    """
    显示文章的归档列表
    :param context(dict): 模板上下文
    """

    # 查询所有文章的创建时间，并按月份分组，降序排列
    date_list = Post.objects.dates('created_time', 'month', order='DESC')

    return {
        'date_list': date_list,
    }


@register.inclusion_tag('blog/inclusions/_categories.html', takes_context=True)
def show_categories(context):
    """
    显示文章的分类列表
    :param context(dict): 模板上下文
    """

    # 查询所有分类信息，按名称排序
    # category_list = Category.objects.all().order_by('name')
    category_list = Category.objects.annotate(num_posts=Count('post')).filter(num_posts__gt=0).order_by('-num_posts')

    return {
        'category_list': category_list
    }


@register.inclusion_tag('blog/inclusions/_tags.html', takes_context=True)
def show_tags(context):
    """
    显示文章的标签列表
    :param context(dict): 模板上下文
    """

    # 查询所有标签信息，按名称排序
    # tag_list = Tag.objects.all().order_by('name')
    tag_list = Tag.objects.annotate(num_posts=Count('post')).filter(num_posts__gt=0).order_by('-num_posts')

    return {
        'tag_list': tag_list
    }


@register.simple_tag(takes_context=True)
def calculate_read_time(context, content, wpm=260, min_time=1):
    """
    计算阅读时间
    :param context(dict): 模板上下文
    :param content(str): 文章内容
    :param wpm(int): 每分钟阅读的单词数，默认为260
    :param min_time(int): 最小阅读时间，默认为1分钟
    """
    # 去掉 HTML 标签
    text_content = strip_tags(content)

    # 旨匹配文本中的英文单词和中文字符
    # [\w\u4e00-\u9fff]+ 匹配一个或多个字母、数字或下划线的序列（即单词字符）以及常见的中文字符
    words = len(re.findall(r'[\w+|\u4e00-\u9fff]', text_content))
    # print("words:", words)
    # 计算阅读时间，以分钟为单位
    read_time = max(words // wpm, min_time)

    # 添加阅读时间和单词数
    context.update({
        'words': words,
        'read_time': read_time
    })
    return ''


@register.simple_tag(takes_context=True)
def share_detail(context, post_pk):
    """
    文章详情页的分享数据
    """

    request = context['request']

    # 获取文章对象
    post = get_object_or_404(Post.objects.only('pk', 'title'), pk=post_pk)

    # 定义分享平台
    share_platforms = [
        {
            'type': 'Telegram',
            'icon': 'fab fa-telegram',
            'link': 'https://t.me/share/url?url=URL&text=TITLE',

        },
        # {
        #     'type': 'Mastodon',
        #     'icon': 'fa-mastodon',
        #     'link': 'mastodon',
        #     'instances': ['mastodon.social', 'mastodon.xyz'],
        # },
    ]

    # 构造 URL 和标题，方便模板渲染
    post_title = post.title
    post_url = request.build_absolute_uri()

    # 对标题进行编码，以便在分享链接中使用
    post_title_encoded = quote(post_title)
    # 对 URL 进行编码，以便在分享链接中使用
    post_url_encoded = quote(post_url)

    for share in share_platforms:
        share_link = share['link'].replace('TITLE', post_title_encoded).replace('URL', post_url_encoded)
        share['link'] = share_link

    # 更新上下文
    context.update({
        'share_platforms': share_platforms,
        # 'post_title_encoded': post_title_encoded,
        # 'post_url_encoded': post_url_encoded,
        'copy_link_tooltip': '复制链接',
        'copy_link_success': '链接复制成功！',
    })

    # 不需要返回任何内容，因为这是一个上下文标签
    return ''
