from django import template
from django.utils.translation import gettext as _

register = template.Library()


@register.simple_tag(takes_context=True)
def breadcrumb_navigation(context):
    # 获取当前页面的 URL
    request = context['request']
    current_url = request.path
    print("current_url:", current_url)
    paths = current_url.strip('/').split('/')
    print("paths:", paths)

    # 处理面包屑数据
    breadcrumb = []

    # 根据 URL 设置面包屑数据
    if 'posts' not in paths:
        if not paths or current_url == '/':
            breadcrumb = [{'url': '/', 'title': _('首页')}]
            print('breadcrumb:', breadcrumb)
        else:
            breadcrumb = [{'url': '/', 'title': _('首页')}]
            for i, item in enumerate(paths):
                url = '/' + '/'.join(paths[:i + 1])
                title = _(item.capitalize())  # 假设每个路径部分都需要翻译并首字母大写
                print("url:", url)
                print("title:", title)
                breadcrumb.append({'url': url, 'title': title})

    return breadcrumb
