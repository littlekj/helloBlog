from django.test import TestCase

# Create your tests here.
import os
import sys
import django

# 获取当前脚本所在的目录（即 backend/blog/）
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录（backend/）
project_root = os.path.dirname(current_dir)

# 将项目根目录加入 Python 模块搜索路径
sys.path.append(project_root)

# 设置 DJANGO_SETTINGS_MODULE 环境变量
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.development")

# 初始化 Django 环境
django.setup()

# 此时再导入依赖 Django 的模块就不会出错了
from blog.utils import update_obsidian_links

# 测试内容
content = r'[[MapReduce 框架基础#ResourceManager 访问查询|ResourceManager 节点访问]] \
            和 [单元测试](/02_技术框架/Django/单元测试.md) \
            和 ![Pasted image 20240519150908.png](/02_技术框架/Django/res/Pasted%20image%2020240519150908.png) \
            和 <img src="https://raw.githubusercontent.com/littlekj/linkres/refs/heads/master/obsidian/1709340840209db.jpg" width="60%" height="50%"> \
            和 <img src="/res/Pasted%20image%2020240109205907.png" width=700, height=400 alt="别名" /> '

print('\n', update_obsidian_links(content))
