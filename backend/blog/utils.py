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
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('ObsidianLinkConverter')


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


# 配置路径
internal_link_prefix = r'https://quillnk.com/posts/'
external_link_prefix = r'https://gitee.com/quillnk/linkres/raw/master/obsidian/'

# 定义所有支持的文件类型（扩展列表）
supported_extensions = {
    'image': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp', 'svg'],
    'document': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'md'],
    'audio': ['mp3', 'wav', 'ogg', 'flac', 'm4a'],
    'video': ['mp4', 'mov', 'avi', 'mkv', 'webm'],
    'archive': ['zip', 'rar', '7z', 'tar', 'gz']
}

# # 正则表达式匹配所有 Obsidian 链接
# # 格式：[[文件名]] 或 ![[文件名]]
# link_regex = re.compile(
#     r'(!?)\[\[([^\]\|\n#]*?)(?:#([^\]\|\n]*?))?(?:\|([^\]\|\n]*?))?(?:\|(\d+)(?:x(\d+))?)?\]\]',
#     re.MULTILINE
# )
#
# # 代码块匹配正则（同时匹配多行代码块和单行内联代码）
# code_pattern = re.compile(
#     r'(?s)(```.*?```|~~~.*?~~~|`[^`]+?`)',
#     re.DOTALL
# )

# 匹配 Obsidian 特有的 Wiki 链接格式
# 格式：[[文件]] 或 ![[文件]]
link_regex = re.compile(
    r'(!?)\[\[([^\]\|\n#]*?)(?:#([^\]\|\n]*?))?(?:\|([^\]\|\n]*?))?(?:\|(\d+)(?:x(\d+))?)?\]\]',
    re.MULTILINE
)

# 匹配标准的 Markdown 超链接语法（包括图片链接）
# 如 [描述](链接) 或 ![描述](链接)
link_pattern = r'''
    (!)?                    # 图片标识（可选）
    \[                      # 开始括号 [
    (                       # 捕获组：链接文本/图片描述
        (?:                 # 非捕获组（处理尺寸或别名部分）
            [^\]\|\n]*      # 除 ]、|、换行外的任意字符
            (?:\|           # 分隔符 |（可选）
                [^\]\n]*    # 除 ]、换行外的任意字符
            )?              # 分隔符部分结束
        )                   # 非捕获组结束
    )                       # 捕获组结束
    \]                      # 结束括号 ]
    \(                      # 开始括号 (
    (                       # 捕获组：URL/路径
        (?:                 # 允许括号出现在URL中
            [^()\n]         # 非括号字符
            |               # 或
            \([^()\n]*\)    # 成对的括号内容
        )*                  # 重复多次
        [^)\n]*             # 最后可以有一些非括号字符
    )                       # URL捕获组结束
    \)                      # 结束括号 )
'''

compiled_pattern = re.compile(link_pattern, re.VERBOSE)

# 代码块匹配正则（同时匹配多行代码块和单行内联代码）
code_pattern = re.compile(
    r'(```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`]*?`)'
)


def save_code_blocks(content):
    """
    保存代码块，并替换为占位符
    """
    code_blocks = code_pattern.findall(content)
    content = code_pattern.sub('__CODE_BLOCK__', content)
    return content, code_blocks


def restore_code_blocks(content, code_blocks):
    """恢复代码块"""
    for code_block in code_blocks:
        content = content.replace('__CODE_BLOCK__', code_block, 1)
    return content


def get_file_type(filename):
    """根据文件扩展名获取文件类型"""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    for file_type, extensions in supported_extensions.items():
        if ext in extensions:
            return file_type
    return 'other'


def encode_url_space_only(url):
    """
    仅对URL中的空格进行编码
    """
    return url.replace(" ", "%20")


def decode_url_space_only(url):
    """
    仅对URL中的空格进行解码
    """
    return url.replace("%20", " ")


def extract_resource_links(content):
    """
    提取笔记中资源的链接
    """
    matches = []
    for match in compiled_pattern.finditer(content):
        is_image = match.group(1) is not None
        link_text = match.group(2)
        url = match.group(3).strip()  # 去除首尾空格
        url = decode_url_space_only(url)
        size_info = None
        alt_text = link_text

        if is_image:
            if re.match(r'^\d+$', link_text):
                width = link_text.split('x')
                size_info = f"width={width}"

            elif re.match(r'^\d+x\d+$', link_text):
                width, height = link_text.split('x')
                size_info = f"width={width}, height={height}"

            elif '|' in link_text:
                parts = link_text.split('|', 1)
                alt_text = parts[0]
                size_part = parts[1]

                if re.match(r'^\d+x\d+$', size_part):
                    width, height = size_part.split('x')
                    size_info = f"width={width}, height={height}"
                elif re.match(r'^\d+$', size_part):
                    size_info = f"width={size_part}"

        match_info = {
            'type': 'image' if is_image else 'link',
            'full_match': match.group(0),
            'text': alt_text,
            'url': url,
            'size': size_info,
            'start': match.start(),
            'end': match.end()
        }
        matches.append(match_info)

    return matches


def is_web_link(link):
    """
    判断链接是否为网页链接
    """
    # 1. 如果以http://或https://开头
    if link.startswith(('http://', 'https://')):
        return True

    # 2. 常见网络协议
    if link.startswith(('ftp://', 'mailto:', 'tel:')):
        return True

    # 3. 标准URL格式（带域名）
    domain_pattern = re.compile(
        r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # 域名
        r'(?::\d+)?'  # 端口
        r'(?:/[^\s]*)?$'  # 路径
    )
    if domain_pattern.match(link):
        return True

    # 4. 协议相对URL（视为外部链接）
    if link.startswith('//'):
        return True

    # 5. 本地网络地址（视为本地链接）
    if 'localhost' in link.lower() or '127.0.0.1' in link.lower():
        return False

    # 6. 其他情况视为本地链接
    return False


def convert_obsidian_wiki_links(content, title=None):
    """
    将 Obsidian 的 wiki 链接转换为标准 Markdown 链接格式
    """

    def replacement(match):
        """内部函数，处理匹配到的链接"""
        # 获取匹配组
        full_match = match.group(0)
        type = match.group(1)
        resource_path = match.group(2) or ''
        anchor = match.group(3) or ''
        alias_or_param = match.group(4) or ''
        width = match.group(5) or ''
        height = match.group(6) or ''
        # print("resource_path：", resource_path)
        # print("alias_or_param：", alias_or_param)
        if not resource_path:
            resource_path = title

        resource_name = os.path.basename(resource_path)
        file_type = get_file_type(resource_name)

        if file_type == 'image':
            # 图片链接到外部资源
            extended_link = f'{external_link_prefix}{resource_name}'
            alt_text = alias_or_param or resource_name
            if width and height:
                return f'<img src="{extended_link}" width="{width}" height="{height}" alt="{alt_text}" />'
            elif width:
                return f'<img src="{extended_link}" width="{width}" alt="{alt_text}" />'
            elif height:
                return f'<img src="{extended_link}" height="{height}" alt="{alt_text}" />'
            else:
                return f'<img src="{extended_link}" alt="{alt_text}" />'
        else:
            # 其他链接到网站内部资源
            resource_name = os.path.splitext(resource_name)[0]
            resource_slug = slugify_translate(resource_name)
            extended_link = f'{internal_link_prefix}{resource_slug}'
            display_text = alias_or_param or anchor or resource_name
            return f'<a href="{extended_link}">{display_text}</a>'

    updated_content = link_regex.sub(replacement, content)

    return updated_content


def convert_standard_markdown_links(content, title=None):
    """
    将标准 Markdown 链接转换为 Web 可访问的外部链接格式
    """
    # 提取所有资源链接和图片匹配项
    matches = extract_resource_links(content)

    # 按起始位置正向排序
    matches.sort(key=lambda m: m['start'])

    # 使用列表拼接构建新内容
    parts = []
    last_end = 0  # 记录上次处理结束位置

    for match in matches:
        full_match = match['full_match']  # 完整匹配
        type = match['type']  # 链接类型（link 或 image）
        text = match['text']  # 链接文本
        url = match['url']  # 链接地址
        size = match['size']  # 尺寸信息
        start = match['start']  # 起始位置
        end = match['end']  # 结束位置

        # 添加匹配前的文本
        parts.append(content[last_end:start])

        # 默认保留原始链接
        replacement_str = full_match

        # 处理本地资源链接
        if not is_web_link(url):
            anchor = None

            # 本地可能存在非图片格式：![alt text](file://path/to/file#anchor)
            # 处理内部锚点链接
            if url.startswith('#'):
                anchor = url[1:]
                resource_path = title
                resource_name = os.path.basename(resource_path)
            else:
                # 处理带锚点的文件链接
                if '#' in url:
                    url_parts = url.split('#', 1)
                    resource_path = url_parts[0]
                    anchor = url_parts[1]
                # 处理普通文件链接
                else:
                    resource_path = url

                resource_name = os.path.basename(resource_path)

            if resource_name:
                resource_name = decode_url_space_only(resource_name)
                resource_name = encode_url_space_only(resource_name)
                if type == 'image':
                    # 生成外部链接格式，链接到外部图床资源
                    extended_link = f'{external_link_prefix}{resource_name}'
                    # 添加锚点（如果存在）
                    if anchor:
                        encoded_anchor = encode_url_space_only(anchor)
                        extended_link += f'#{encoded_anchor}'

                    alt_text = text or resource_name
                    if size:
                        replacement_str = f'<img src="{extended_link}" {size} alt="{alt_text}" />'
                    else:
                        replacement_str = f'![{alt_text}]({extended_link})'
                elif type == 'link':
                    # 生成外部链接格式，链接到网站内部资源
                    display_text = text or anchor or resource_name
                    resource_name = os.path.splitext(resource_name)[0]
                    resource_slug = slugify_translate(resource_name)
                    extended_link = f'{internal_link_prefix}{resource_slug}'
                    replacement_str = f'<a href="{extended_link}">{display_text}</a>'

            else:
                logger.warning(f"⚠️ 警告: 资源未找到： {resource_path}")

        # 添加替换后的内容
        parts.append(replacement_str)
        last_end = end  # 更新上次处理结束位置

    # 添加最后一段文本
    parts.append(content[last_end:])

    # 拼接所有部分
    updated_content = ''.join(parts)

    return updated_content


def resolve_img_src_to_url(content):
    """
    将图片链接中的 src 属性转换为 URL
    :param content: 包含 HTML 内容的字符串
    :return: 修改后的 HTML 内容
    """
    # 解析 HTML
    soup = BeautifulSoup(content, 'html.parser')

    # 遍历所有 img 标签
    for img in soup.find_all('img'):
        src = img.get('src')
        alt = img.get('alt', '')  # 默认为空字符串

        if src is None:
            continue

        # 判断是否为相对路径
        if not (src.startswith('http://') or src.startswith('https://')):
            img_name = os.path.basename(src)
            img_name = decode_url_space_only(img_name)
            if alt is None:
                img['alt'] = img_name
            img_name = encode_url_space_only(img_name)
            # 图片链接到外部图床资源
            new_src = f'{external_link_prefix}{img_name}'
            img['src'] = new_src

    modified_content = str(soup)

    return modified_content


def update_obsidian_links(content, title=None):
    """
    更新 Obsidian 链接形式
    """
    # 提取代码内容并用占位符替换
    updated_content, code_blocks = save_code_blocks(content)

    # 转换为标准 Markdown 链接格式
    updated_content = convert_obsidian_wiki_links(updated_content, title)

    # 转换为 Web 可访问的外部链接格式
    updated_content = convert_standard_markdown_links(updated_content, title)

    # 更新图片链接相对路径为 URL
    updated_content = resolve_img_src_to_url(updated_content)

    # 恢复代码内容
    updated_content = restore_code_blocks(updated_content, code_blocks)

    return updated_content


def render_markdown(body, title=None):
    """
    将 Markdown 文本转换为 HTML 并生成目录(TOC)
    :param body: 原始 Markdown 格式的文本内容
    :param title: 文章标题，用于处理链接
    :return tuple: (rendered_body, toc)
            rendered_body (str): 渲染后的 HTML 内容
            toc (str): 生成的 HTML 目录
    """
    body = update_obsidian_links(body, title=title)

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
