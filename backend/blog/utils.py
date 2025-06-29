import re
from collections import defaultdict
from bs4 import BeautifulSoup
from django.utils.text import slugify
from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin
from django.utils.html import strip_tags
from haystack.utils import Highlighter
import random
import hashlib
import time
import requests


def generate_summary(html, max_length=200):
    """
    生成 HTML 摘要
    :param html: HTML 文本
    :param max_length: 最大长度
    """
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    summary_text = text[:max_length] + '...' if len(text) > max_length else text

    return summary_text


def replace_markdown_symbols(markdown_text):
    """
    替换 Markdown 标题中符号为空
    :param markdown_text: Markdown 文本
    """
    # 字符串列表，包括需要被替换为空的字符和标签
    str_list = ['*', '_', '~', '<sub>', '</sub>', '<sup>', '</sup>', '`']

    # 创建正则表达式模式
    # re.escape(char) 确保特殊字符在正则表达式中被正确转义
    # '|'.join(...) 将列表中的字符用 '|' 连接起来，形成一个匹配任意字符的模式
    pattern = '|'.join(re.escape(char) for char in str_list)

    # 处理每一行
    lines = markdown_text.split('\n')

    # 使用 re.sub() 方法将匹配到的字符替换为空
    # pattern 是正则表达式模式
    # '' 是替换的内容（即空字符串）
    # text 是原始文本
    processed_lines = [
        re.sub(pattern, '', line) if line.startswith(('#', '##', '###', '####', '#####', '######')) else line
        for line in lines
    ]
    # print("processed_lines", processed_lines)
    return '\n'.join(processed_lines)


def custom_slugify(text):
    """
    保留字母、数字和中文字符，其他字符替换为短横线
    """
    # \w: 匹配字母、数字和下划线。
    # \u4e00-\u9fff: 匹配中文字符的 Unicode 范围。
    return re.sub(r'[^\w\u4e00-\u9fff]+', '-', text.lower()).strip('-')


def dict_to_html(toc, active_title=None, collapsed=False):
    """
    将目录结构字典转换为 HTML
    :param toc: 嵌套目录结构
    :param active_title: 当前高亮标题（只高亮这个）
    :param collapsed: 是否折叠子目录
    :return: HTML 字符串
    """

    def render_toc_items(items):
        """内部函数，递归处理目录项"""

        # 设置 ul_class，根据折叠状态添加相应样式
        ul_class = "toc-list is-collapsible is-collapsed" if collapsed else "toc_list"
        html = f'<ul class="{ul_class}">'

        # 遍历当前层级的所有标题项
        for title, data in items.items():
            # 生成标题的 URL slug（用于锚点链接）
            slug = custom_slugify(title)
            # 获取标题的层级
            level = int(data['level'])
            # 检查当前标题是否为活动标题
            is_active = (title == active_title)

            # 设置 li 和 a 标签的类名
            li_class = "toc-list-item"
            link_class = f"toc-link node-name--H{level}"

            # 如果是活动标题，添加高亮样式
            if is_active:
                li_class += " is-active-li"
                link_class += " is-active-link"

            # 构建列表项：包含链接到标题的锚点
            html += f'<li class="{li_class}"><a href="#{slug}" class="{link_class}">{title}</a>'

            if data['children']:  # 递归处理子目录
                html += render_toc_items(data['children'])
            html += '</li>'

        html += '</ul>'
        return html

    return render_toc_items(toc) if toc else ''


def generate_toc(markdown_parser, markdown_text, active_title=None):
    """
    从 Markdown 文本生成嵌套的 HTML TOC（目录）
    :param markdown_parser: MarkdownIt 实例
    :param markdown_text: 原始 Markdown 字符串
    :param active_title: 当前文章标题（用于高亮）
    :return: HTML 字符串
    """

    # 使用 Markdown 解析器将文本解析为 token 流
    tokens = markdown_parser.parse(markdown_text)
    # print("tokens:", tokens)

    # 使用 defaultdict 创建嵌套字典结构
    toc = defaultdict(dict)

    # 初始化栈：用于跟踪当前标题层级和位置
    # 栈元素为元组 (children_dict, level)
    stack = []

    # 遍历解析得到的所有 token
    for i, token in enumerate(tokens):
        if token.type == 'heading_open' and token.tag in ['h2', 'h3', 'h4', 'h5']:
            level = int(token.tag[1])

            # 获取标题文本内容（下一个 token 是标题文本）
            title = tokens[i + 1].content.strip()

            # 弹出栈中所有高于或等于当前层级的元素
            while stack and stack[-1][1] >= level:
                stack.pop()

            # 确定当前标题的父容器（栈顶或根目录）
            current = stack[-1][0] if stack else toc

            # 添加新标题项（包含子容器和层级）
            current[title] = {'children': {}, 'level': level}

            # 将新标题的子容器压入栈
            stack.append((current[title]['children'], level))

    # 转换嵌套字典为HTML
    return dict_to_html(dict(toc), active_title)


def render_markdown(body):
    """
    将 Markdown 文本转换为 HTML 并生成目录(TOC)
    :param body: 原始 Markdown 格式的文本内容
    :return tuple: (rendered_body, toc)
            rendered_body (str): 渲染后的 HTML 内容
            toc (str): 生成的 HTML 目录
    """
    # 替换 Markdown 标题中的特殊符号
    processed_body = replace_markdown_symbols(body)

    # 初始化 Markdown 解析器（使用类似 GitHub 的解析规则）
    # 'gfm-like' 模式支持表格、任务列表等扩展语法
    md = MarkdownIt('gfm-like').use(
        anchors_plugin,
        min_level=2,
        max_level=4,
        slug_func=custom_slugify,  # 自定义 slugify 函数
        permalink=True,
        permalinkSymbol='',
        permalinkBefore=False,
        permalinkSpace=True
    )

    # 渲染 Markdown 为 HTML
    rendered_body = md.render(processed_body)

    # 生成目录(TOC)
    toc = generate_toc(md, processed_body)

    return rendered_body, toc


class CustomHighlighter(Highlighter):
    """
    自定义关键词高亮器类，扩展 Haystack 的 Highlighter。
    这个高亮器不对过短的文本（如标题）进行截断。
    """

    def highlight(self, text_block):
        """
        高亮显示关键词，避免对过短的文本进行截断。

        参数:
        text_block (str): 要高亮显示的文本块。

        返回:
        str: 包含高亮标记的 HTML 文本。
        """
        # 去除 HTML 标签
        self.text_block = strip_tags(text_block)

        # 查找需要高亮的关键词位置
        highlight_locations = self.find_highlightable_words()

        # 查找高亮窗口的起始和结束位置
        start_offset, end_offset = self.find_window(highlight_locations)

        # 如果文本块长度小于最大长度，则不进行截断
        if len(text_block) < self.max_length:
            start_offset = 0

        # 渲染高亮显示的 HTML
        return self.render_html(highlight_locations, start_offset, end_offset)


def is_highlight_title_first(highlights, title):
    """
    判断高亮的第一部分是否是标题，如果是，标题使用高亮的第一部分，如果不是，直接返回标题。
    不使用搜索词是否在标题中的判断，因为搜索词可能在标题中，但返回的高亮部分可能在标题之外。
    :param highlights: 高亮文本
    :param title: 标题
    """
    # 获取高亮文本的第一部分
    first_line = highlights[0].split('\n')[0]

    # 去除高亮文本中的 HTML 标签 <em> 和 </em>
    cleaned = re.sub(r'</?em>', '', first_line)

    # 判断高亮文本的第一部分是否是标题
    return cleaned == title


def normalize_highlight(highlighted):
    """
    Elasticsearch 查询字段可能会返回不同的数据类型，如字符串或字符串列表。
    将这些数据类型标准化为字符串，以便后续处理。
    """
    if isinstance(highlighted, list):
        return '...'.join(highlighted)  # 如果是列表，则连接成一个字符串
    elif isinstance(highlighted, str):
        return highlighted  # 如果已经是字符串，直接返回
    return ''  # 如果既不是列表也不是字符串，返回空字符


# 百度翻译 API 凭证
APP_ID = '20250611002379582'
SECRET_KEY = 'QeVzbItxwBorSBcsLC5G'


def translate_baidu(text, from_lang='zh', to_lang='en'):
    """
    翻译文本
    :param text: 要翻译的文本
    :param from_lang: 原文语言
    :param to_lang: 目标语言
    :return: 翻译后的文本
    """
    salt = str(random.randint(32768, 65536))
    sign_str = APP_ID + text + salt + SECRET_KEY
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
    params = {
        'q': text,
        'from': from_lang,
        'to': to_lang,
        'appid': APP_ID,
        'salt': salt,
        'sign': sign
    }

    result = None

    try:
        time.sleep(1)  # 翻译API访问频率受限
        resp = requests.get(url, params=params, timeout=3)
        result = resp.json()
        return result['trans_result'][0]['dst']
    except Exception as e:
        print(f"翻译失败：{e}")
        print(f"失败结果：{result}")
        return text


def slugify_translate(text):
    """
    翻译并生成 URL 友好的字符串
    """
    translate_text = translate_baidu(text)
    return slugify(translate_text)
