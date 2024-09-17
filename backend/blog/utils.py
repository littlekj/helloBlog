from collections import defaultdict
import re

from bs4 import BeautifulSoup


def dict_to_html(toc, isactive, collapsed):
    """
    将目录结构的字典转换为 HTML
    :param toc: 目录结构的字典
    :param isactive: 是否激活当前目录项
    :param collapsed: 是否折叠目录
    """
    if toc:
        def dict_to_html_recursive(toc, isactive, collapsed):
            """
            递归地将目录结构的字典转换为 HTML
            """
            if not collapsed:
                html = '<ul class="toc-list">'
                collapsed = True
            else:
                html = '<ul class="toc-list is-collapsible is-collapsed">'

            for title, sub_toc in toc.items():
                slug = slugify(title)
                # print('slug:', slug)
                level = int(sub_toc['level'])

                if isactive:
                    html += f'<li class="toc-list-item is-active-li"><a href="#{slug}" class="toc-link node-name--H{level} is-active-link">' \
                            f'<font style="vertical-align: inherit;"><font style="vertical-align: inherit;">{title}</font></font></a>'
                    isactive = False
                else:
                    html += f'<li class="toc-list-item"><a href="#{slug}" class="toc-link node-name--H{level}">' \
                            f'<font style="vertical-align: inherit;"><font style="vertical-align: inherit;">{title}</font></font></a>'

                if sub_toc['children']:
                    html += dict_to_html(sub_toc['children'], isactive, collapsed)
                html += '</li>'
            html += '</ul>'
            return html

        return dict_to_html_recursive(toc, isactive, collapsed)

    else:
        return ''


def generate_toc(markdown_parser, markdown_text):
    """
    生成 HTML 目录
    :param markdown_parser: MarkdownIt 实例
    :param markdown_text: Markdown 文本
    """

    tokens = markdown_parser.parse(markdown_text)

    # 定义要识别的标题标签
    tag = ['h1', 'h2', 'h3', 'h4']

    # 使用 defaultdict 初始化目录结构
    toc = defaultdict(dict)
    stack = []  # 用于跟踪目录的层级结构

    # 遍历 tokens 并生成目录项
    for i, token in enumerate(tokens):
        # 处理标题
        if token.type == 'heading_open':
            if token.tag in tag:
                # 获取当前标题的级别
                level = str(token.tag)[1]
                # 获取当前标题的内容
                title = tokens[i + 1].content

                # 弹出堆栈中的元素，直到找到正确的层级
                while stack and stack[-1][1] >= level:
                    stack.pop()

                # 设置当前目录项的位置
                current_toc = stack[-1][0] if stack else toc

                # 添加新的目录节点
                current_toc[title] = {'children': {}, 'level': level}

                # 将当前节点和层级压入堆栈
                stack.append((current_toc[title]['children'], level))
    # print("dict(toc):", dict(toc))

    # return dict(toc)  # 转化为普通 dict

    # # 转换的HTML结构简陋，注释掉
    # def dict_to_html(toc):
    #     """
    #     将目录结构的字典转换为 HTML
    #     :param toc: 目录结构的字典
    #     """
    #
    #     def dict_to_html_recursive(node):
    #         """
    #         递归地将目录结构的字典转换为 HTML
    #         """
    #         html = '<ul>'
    #         for title, sub_node in node.items():
    #             slug = slugify(title)
    #             # print('slug:', slug)
    #             html += f'<li id="{slug}"><a href="#{slug}">{title}</a>'
    #             if sub_node['children']:
    #                 html += dict_to_html(sub_node['children'])
    #             html += '</li>'
    #         html += '</ul>'
    #         return html
    #
    #     return dict_to_html_recursive(toc)

    return dict_to_html(dict(toc), True, False)


def replace_markdown_symbols(markdown_text):
    """
    替换 Markdown 标题中符号为空
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

    return '\n'.join(processed_lines)


def slugify(text):
    # 保留字母、数字和中文字符，其他字符替换为短横线
    # \w: 匹配字母、数字和下划线。
    # \u4e00-\u9fff: 匹配中文字符的 Unicode 范围。
    return re.sub(r'[^\w\u4e00-\u9fff]+', '-', text.lower()).strip('-')


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


from django.utils.html import strip_tags
from haystack.utils import Highlighter


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


def standardize_highlight(highlighted):
    """
    Elasticsearch 查询字段可能会返回不同的数据类型，如字符串或字符串列表。
    将这些数据类型标准化为字符串，以便后续处理。
    """
    if isinstance(highlighted, list):
        return '...'.join(highlighted)  # 如果是列表，则连接成一个字符串
    elif isinstance(highlighted, str):
        return highlighted  # 如果已经是字符串，直接返回
    return ''  # 如果既不是列表也不是字符串，返回空字符
