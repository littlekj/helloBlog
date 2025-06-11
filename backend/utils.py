import secrets
import os
import django

# 设置 Django 配置文件的路径
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')
# 初始化 Django 环境
django.setup()


def generate_secret_key(length=50):
    return secrets.token_urlsafe(length)


print(generate_secret_key())

# 导入 Post 模型
from blog.models import Post

# 获取所有文章
posts = Post.objects.all()

# 站点的基本 URL
site_url = "https://quillnk.com"

# 打开并写入 urls.txt
with open('urls.txt', 'w') as f:
    f.write(site_url + "\n")
    for post in posts:
        url = f"{site_url}/posts/{post.slug}/"
        f.write(url + "\n")

print("成功保存所有文章的 URL 到 urls.txt 文件")
