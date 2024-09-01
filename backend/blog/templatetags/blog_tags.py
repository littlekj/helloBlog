from django import template
from blog.models import Post, Category, Tag
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache

from django.db.models.aggregates import Count

# 创建一个模板库实例
register = template.Library()


# 装饰器将函数注册为模板标签，指定渲染的模板路径，并表示此标签接收模板上下文作为参数
@register.inclusion_tag('blog/inclusions/_recent_posts.html', takes_context=True)
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
            # 查询所有博客文章，按创建时间降序排列
            posts = Post.objects.all().order_by('-created_time')

            # 使用 Paginator 对象进行分页
            paginator = Paginator(posts, num)

            # 从上下文获取当前页码，如果没有则默认第一页
            page_number = context.get('page_number', 1)

            try:
                # 获取当前页的数据
                recent_posts = paginator.page(page_number)
            except PageNotAnInteger:
                # 如果页码不是整数，则返回第一页
                recent_posts = paginator.page(1)
            except EmptyPage:
                # 如果页码超出范围，则返回最后一一页
                recent_posts = paginator.page(paginator.num_pages)

            # 将查询结果存储到缓存中，设置有效时间为600秒
            cache.set(cache_key, recent_posts, timeout=600)
        except Exception as e:
            print(f'Error fecthing recent posts: {e}')
            recent_posts = []

        # 返回给模板的数据字典
        return {
            'recent_post_list': recent_posts,
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
    tag_list =Tag.objects.annotate(num_posts=Count('post')).filter(num_posts__gt=0).order_by('-num_posts')

    return {
        'tag_list': tag_list
    }
