from django import template
from blog.models import Post, Category, Tag
from django.core.cache import cache
from django.db.models.functions import Coalesce
from django.db.models.aggregates import Count
import re, math
from django.utils.html import strip_tags

from django.shortcuts import get_object_or_404
from urllib.parse import quote

# 创建一个模板库实例
register = template.Library()


# 装饰器将函数注册为模板标签，指定渲染的模板路径，将视图逻辑嵌入到模板中
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
            recent_posts = Post.objects.order_by(
                Coalesce('modified_time', 'created_time').desc()
            ).only('pk', 'title')[:num]

            # 将查询结果存储到缓存中，设置有效时间为600秒
            cache.set(cache_key, recent_posts, timeout=600)
        except Exception as e:
            print(f'Error fetching recent posts: {e}')
            recent_posts = []

    # 返回给模板的数据字典
    return {
        'recent_posts': recent_posts
    }


@register.inclusion_tag('_includes/trending-tags.html', takes_context=True)
def show_trending_tags(context, num=10):
    """
    显示文章的热门标签
    :param context: 模板上下文，当前未使用，预留扩展
    :param num: 显示的文章数量
    :return: 包含热门标签列表
    """

    # 获取所有标签并按管理文章数排序，限制为前10个
    tags = Tag.objects.annotate(num_posts=Count('post')).filter(num_posts__gt=0).order_by('-num_posts')[:num]
    return {
        'trending_tags': tags
    }


@register.simple_tag(takes_context=True)
def calculate_read_time(context, content=None, wpm=300):
    """
    计算文章的预期阅读时间
    :param context: 模板上下文
    :param content: 文章内容
    :param wpm: 每分钟阅读的单词数，默认为 300
    """
    # 移除 HTML 标签，获取纯文本内容
    text_content = strip_tags(content)

    # 正确匹配英文单词 + 单个中文字符
    # \w+ 匹配英文单词或数字（连贯字符），[\u4e00 -\u9fff] 匹配单个中文汉字。
    # Python 的 re 默认是 ASCII 模式，[a-zA-Z0-9_]+：比 \w+ 更明确，只匹配字母、数字和下划线。
    # words = len(re.findall(r'\w+|[\u4e00-\u9fff]', text_content))
    words = len(re.findall(r'[a-zA-Z0-9_]+|[\u4e00-\u9fff]', text_content))

    # 计算阅读时间（分钟），向上取整，确保短文章至少 1 分钟
    read_time = math.ceil(words / wpm) if words > 0 else 0

    # 更新模板上下文
    context.update({
        'words': words,
        'read_time': read_time
    })

    # 返回空字符串，simple_tag 的要求，主要依赖 context 中注入的数据
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
        # {
        #     'type': '微信',
        #     'icon': 'fa-brands fa-weixin',
        #     'link': 'https://t.me/share/url?url=URL&text=TITLE',
        # },
        {
            'type': 'Telegram',
            'icon': 'fab fa-telegram',
            'link': 'https://t.me/share/url?url=URL&text=TITLE',

        },
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
