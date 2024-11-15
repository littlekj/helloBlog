from django import template
from django.utils import translation
from django.utils.translation import gettext
from django.urls import resolve
from blog.models import Post, Category, Tag
import os
from django.conf import settings

register = template.Library()


@register.simple_tag(takes_context=True)
def global_nav(context):
    """
    添加自定义的上下文数据
    """

    tabs = [
        {'url': '/', 'title': gettext('首页'), 'icon': 'fas fa-home'},
        {'url': '/categories/', 'title': gettext('分类'), 'icon': 'fas fa-stream'},
        {'url': '/tags/', 'title': gettext('标签'), 'icon': 'fas fa-tags'},
        {'url': '/archives/', 'title': gettext('归档'), 'icon': 'fas fa-archive'},
        {'url': '/about/', 'title': gettext('关于'), 'icon': 'fas fa-info-circle'},
    ]

    context.update({
        'tabs': tabs,
    })

    return ''


@register.simple_tag(takes_context=True)
def global_data(context):
    page_lang = translation.get_language()  # 获取当前语言
    global_data = {
        'page_lang': page_lang,
        'site': {
            'alt_lang': 'fr',
            'lang': 'en'
        }
    }

    return global_data


@register.simple_tag(takes_context=True)
def meta_data(context):
    """
    添加页面元数据
    """
    request = context['request']
    current_url_name = resolve(request.path_info).url_name  # 获取当前URL模式的名称
    full_url = request.build_absolute_uri()
    # print("full_url:", full_url)

    # 获取用户设备信息
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    is_mobile = 'mobile' in user_agent.lower()

    if current_url_name == 'index':
        meta = {
            'title': '羽毛笔轻轻划过',
            'description': '这是羽毛笔的个人博客，记录关于 Python、Web 编程等相关技术的内容(•̀ᴗ-)✧',
            'type': 'website',
            'keywords': 'Python, Web编程, 技术博客, 后端开发',
        }
    elif current_url_name == 'detail':
        slug = resolve(request.path_info).kwargs.get('slug')
        try:
            current_post = Post.objects.get(slug=slug)
            if current_post.tags.exists():
                tags = ', '.join(tag.name for tag in current_post.tags.all())
            else:
                tags = ''
            meta = {
                'title': current_post.title,
                'description': current_post.excerpt,
                'type': 'article',
                'keywords': tags,
                'author': current_post.author,
                'published_time': current_post.modified_time,
                'created_time': current_post.created_time,
            }
        except Post.DoesNotExist:
            meta = {
                'title': '文章未找到',
                'description': '您访问的文章不存在。',
            }
    elif current_url_name == 'categories':
        meta = {
            'title': '分类',
            'description': '分类列表',
        }
    elif current_url_name == 'category_detail':
        meta = {
            'title': '分类',
            'description': '分类详情页',
        }
    elif current_url_name == 'tags':
        meta = {
            'title': '标签',
            'description': '标签列表',
        }
    elif current_url_name == 'tag_detail':
        meta = {
            'title': '标签',
            'description': '标签详情页',
        }
    elif current_url_name == 'archives':
        meta = {
            'title': '归档',
            'description': '文章归档列表',
        }
    elif current_url_name == 'about':
        meta = {
            'title': '关于',
            'description': '关于详情',
        }
    elif current_url_name == 'rss_feed':
        meta = {
            'title': '订阅RSS',
            'description': '订阅RSS',
        }
    elif current_url_name == 'search':
        meta = {
            'title': '搜索',
            'description': '搜索文章列表',
        }
    else:
        meta = {
            'title': '羽毛笔轻轻划过',
            'description': '这是羽毛笔的个人博客，记录关于 Python、Web 编程等相关技术的内容。',
        }

    # 添加当前URL到meta数据
    meta['full_url'] = full_url

    context.update({
        'meta': meta,
        'is_mobile': is_mobile,
    })

    return ''


@register.simple_tag(takes_context=True)
def static_jsfile(context):
    js_files = []
    javascript_files = []
    for static_dir in settings.STATICFILES_DIRS:
        js_dir = os.path.join(static_dir, 'assets/js')
        javascript_dir = os.path.join(static_dir, 'assets/_javascript')

        if os.path.exists(js_dir):
            for root, dir, files in os.walk(js_dir):
                for file in files:
                    if file.endswith('.js'):
                        relative_path = os.path.relpath(os.path.join(root, file), js_dir)
                        js_files.append(os.path.join('assets/js', relative_path))

        if os.path.exists(javascript_dir):
            for root, _, files in os.walk(javascript_dir):
                for file in files:
                    if file.endswith('.js'):
                        relative_path = os.path.relpath(os.path.join(root, file), javascript_dir)
                        javascript_files.append(os.path.join('assets/_javascript', relative_path))

    # print('js_files: ', js_files)
    # print('javascript_files: ', javascript_files)

    context.update({
        'js_files': js_files,
        'javascript_files': javascript_files
    })

    return ''
