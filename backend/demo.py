import os
import django

# 设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')

# 设置 Django
django.setup()

from blog.models import Category, Tag, Post
from django.contrib.auth.models import User
from django.utils import timezone
#
# # 获取或创建必要的对象
# Category(name='Python').save()
# category = Category.objects.get(name='Python')
#
# tags = ['Django', 'Python']
# for tag_name in tags:
#     Tag.objects.get_or_create(name=tag_name)
#
# # 获取现有的标签
# # name 是 Tag 模型中的字段，__in 是一个查找表达式
# curr_tags = Tag.objects.filter(name__in=['Django', 'Python'])
#
# # 创建新用户
# # user = User.objects.create_user(username='Zhangsan', password='password123')
#
# user = User.objects.get(username='Zhangsan')
#
# post = Post(title='first article', body='This is my first article.', created_time=timezone.now(),
#             modified_time=timezone.now(), category=category,
#             author=user)
# post.save()
#
# post.tags.set(curr_tags)
from django.db.models import Count
# # 自定义解析器
#
# import re
# from markdown_it import MarkdownIt
#
# # 正则表达式，用于匹配 Vimeo 视频 URL
# vimeoRE = re.compile(r'^https?:\/\/(www\.)?vimeo.com\/(\d+)($|\/)')
#
#
# # 自定义的渲染函数，用于处理 Vimeo 视频
# def render_vimeo(self, tokens, idx, options, env):
#     print('idx:', idx)
#     print('tokens:', tokens)
#     token = tokens[idx]
#     print('token:', token)
#     # 检查 URL 是否匹配 Vimeo 视频模式
#     if vimeoRE.match(token.attrs["src"]):
#         # [2]：访问正则表达式中的第3个捕获组（索引从0开始）。
#         ident = vimeoRE.match(token.attrs["src"])[2]
#
#         # 返回嵌入 Vimeo 视频的 HTML
#         return (
#                 '<div class="embed-responsive embed-responsive-16by9">\n'
#                 '  <iframe class="embed-responsive-item" src="//player.vimeo.com/video/' +
#                 ident + '" frameborder="0" allow="autoplay; fullscreen" allowfullscreen></iframe>\n'
#                         '</div>\n'
#         )
#
#     # 如果不是 Vimeo 视频，使用默认的图像渲染器
#     return self.image(tokens, idx, options, env)
#
#
# # 初始化 MarkdownIt 实例
# md = MarkdownIt("commonmark")
#
# # 添加自定义的渲染规则
# md.add_render_rule("image", render_vimeo)
#
# # 渲染 Markdown 内容
# markdown_content = "![](https://www.vimeo.com/123)"
# html_output = md.render(markdown_content)
#
# # 打印 HTML 输出
# print(html_output)


# from bs4 import BeautifulSoup  # 导入 BeautifulSoup 类，用于解析 HTML 内容
#
# # 定义一个包含多个标题的 HTML 字符串
# html = '''
# <h1>章节 1</h1>
# <h2>副标题 1.1</h2>
# <h3>子标题 1.1.1</h3>
# <h1>章节 2</h1>
# <h2>副标题 2.1</h2>
# <h3>子标题 2.1.1</h3>
# <h2>副标题 2.2</h2>
# <h3>子标题 2.2.1</h3>
# '''
#
# # 使用 BeautifulSoup 解析 HTML 字符串，生成一个解析树对象
# soup = BeautifulSoup(html, 'html.parser')
# # 提取所有标题标签，标签范围从 h1 到 h6
# headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
#
#
# def build_toc(headings):
#     """
#     根据 HTML 标题生成目录结构。
#     :param headings: BeautifulSoup 提取的标题标签列表。
#     :return: 生成的目录结构字典。
#     """
#     toc = {}  # 初始化一个空字典，用于存储根目录
#     stack = []  # 初始化一个空列表，用于跟踪当前目录的层级
#
#     # 遍历所有标题标签
#     for heading in headings:
#         level = int(heading.name[1])  # 提取当前标题的级别（例如 'h1' 的级别为 1）
#         title = heading.get_text()  # 获取当前标题的文本内容
#
#         # 处理新的顶级目录项（即新的 <h1>）
#         if level == 1:
#             current_toc = toc  # 将 current_toc 设置为根目录 toc
#         else:
#             # 弹出 stack 中的元素，直到找到正确的层级
#             while stack and stack[-1][1] >= level:
#                 stack.pop()  # 移除 stack 中的最后一个元素
#             # 设置当前目录项的位置，如果 stack 非空，则是 stack 中最后一个元素的子节点
#             current_toc = stack[-1][0]['children'] if stack else toc
#
#         # 创建新的目录节点，包含标题和子节点
#         node = {'title': title, 'children': {}}
#
#         # 将当前节点添加到 current_toc 中
#         current_toc[title] = node
#
#         # 将当前节点和层级压入 stack 中，以便后续作为子节点处理
#         stack.append((node, level))
#
#     return toc  # 返回生成的目录结构
#
#
# # 调用 build_toc 函数，传入标题列表 headings，获取生成的目录结构
# toc = build_toc(headings)
#
#
# # 打印生成的目录结构
# # print(toc)
#
#
# def dict_to_html(toc):
#     """
#     将目录结构字典转换为 HTML 格式的目录结构。
#     :param toc: 目录结构字典。
#     :return: 生成的 HTML 字符串。
#     """
#
#     def dict_to_html_recursive(node):
#         """
#         递归地将目录节点转换为 HTML。
#         :param node: 当前目录节点字典。
#         :return: 生成的 HTML 字符串。
#         """
#         html = '<ul>'  # 开始一个新的无序列表
#         for title, sub_node in node.items():
#             html += f'<li><a href="#{title}">{title}</a>'  # 添加目录项的链接
#             if sub_node['children']:  # 如果当前目录项有子节点
#                 html += dict_to_html_recursive(sub_node['children'])  # 递归生成子节点的 HTML
#             html += '</li>'  # 关闭目录项的列表项
#         html += '</ul>'  # 关闭无序列表
#         return html
#
#     return dict_to_html_recursive(toc)  # 返回整个目录的 HTML 字符串
#
#
# # 调用 dict_to_html 函数，将目录结构转换为 HTML 格式
# html_toc = dict_to_html(toc)
# # 打印生成的 HTML 目录结构
# print(html_toc)


# Markdown 目录生成器
from markdown_it import MarkdownIt
from collections import defaultdict


# def generate_toc(markdown_text):
#     # 解析 Markdown 文本
#     tokens = MarkdownIt().parse(markdown_text)
#
#     tag = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
#     toc = defaultdict(dict)
#     stack = []
#
#     # 遍历 tokens 并生成目录项
#     for i, token in enumerate(tokens):
#         if token.type == 'heading_open':
#             if token.tag in tag:
#                 level = str(token.tag)[1]
#                 title = tokens[i + 1].content
#                 print('content', title)
#                 while stack and stack[-1][1] >= level:
#                     stack.pop()
#
#                 current_toc = stack[-1][0] if stack else toc
#
#                 current_toc[title] = {'children': {}}
#                 stack.append((current_toc[title]['children'], level))
#
#     return dict(toc)
#
#
# def dict_to_html(toc):
#     def dict_to_html_recursive(node):
#         html = '<div class="toc"><ul>'
#         for title, sub_node in node.items():
#             html += f'<li><a href="#{title}">{title}</a>'
#             if sub_node['children']:
#                 html += dict_to_html(sub_node['children'])
#             html += '</li>'
#         html += '</ul></div>'
#         return html
#
#     return dict_to_html_recursive(toc)
#
#
# # Markdown 文本示例
# markdown_content = """
# # Title 1
# Some content here.
#
# ## Subtitle 1.1
# More content here.
#
# ### Sub-subtitle 1.1.1
# Even more content here.
#
# ## Subtitle 1.2
# Additional content here.
#
# # Title 2
# Other content here.
# """
#
# # 初始化 MarkdownIt 实例
# md = MarkdownIt()
#
# # 生成目录
# toc = generate_toc(markdown_content)
# toc_html = dict_to_html(toc)
#
# # 打印目录 HTML
# print(toc_html)
#
# from markdown_it import MarkdownIt
# from mdit_py_plugins.anchors import anchors_plugin
#
# # 创建 MarkdownIt 实例
# md = MarkdownIt()
#
# # 添加 anchors_plugin 插件
# md.use(anchors_plugin, min_level=1, max_level=2, permalink=True, permalinkSymbol='¶ ', permalinkBefore=False,
#        permalinkSpace=True)
#
# # 示例 Markdown 文本
# markdown_text = """
# # Title String
# ## Subheading
#
# Some text here.
# """
#
# # 解析 Markdown 文本
# html = md.render(markdown_text)
#
# # 输出 HTML
# print(html)


from blog.models import Category
categories = Category.objects.values('slug').annotate(count=Count('slug')).filter(count__gt=1)
print("categories:", categories)
