import os
import pathlib  # 用于处理文件路径
import random
import sys
from datetime import timedelta  # 用于处理日期和时间

import django
import faker  # 用于生成假数据
from django.utils import timezone  # 用于处理时区相关的时间

# 将项目根目录添加到 Python 的模块搜索路径中
dir_name = os.path.dirname  # 赋值函数引用，用于获取指定路径的父目录路径
BASE_DIR = dir_name(dir_name(os.path.abspath(__file__)))  # 获取当前文件所在目录的上一级目录的上一级目录
sys.path.append(BASE_DIR)  # 将 BASE_DIR 添加到系统路径

# 主程序执行，配置 Django 环境
if __name__ == '__main__':
    # 设置 Django 的配置模块
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'backend.settings.development')
    django.setup()  # 启动 Django 应用

    # 导入需要操作的 Django 模型
    from blog.models import Post, Category, Tag
    from comment.models import Comment
    from django.contrib.auth.models import User

    # 清空数据库中的数据
    print('clean database...')
    Post.objects.all().delete()
    Category.objects.all().delete()
    Tag.objects.all().delete()
    Comment.objects.all().delete()
    User.objects.all().delete()

    # 创建一个超级用户
    print('create a blog user...')
    user = User.objects.create_superuser('admin', 'admin@admin.com', 'admin')

    # 定义一些类别和标签
    category_list = ['Python', 'Django', 'Flask', 'HTML', 'CSS', 'JavaScript']
    tag_list = ['Python', 'Django', 'Flask', 'HTML', 'CSS', 'JavaScript']

    # 设置一个时间标记，表示一年前的时间
    year_ago = timezone.now() - timedelta(days=365)

    # 创建类别和标签
    print('create categories and tags...')
    for cate in category_list:
        Category.objects.create(name=cate)

    for tag in tag_list:
        Tag.objects.create(name=tag)

    # 创建一个示例文章
    print('create posts...')
    sample_body = pathlib.Path(BASE_DIR).joinpath('scripts', 'sample.md').read_text(encoding='utf-8')
    Post.objects.create(
        title='Making a New World',
        body=sample_body,  # 从 sample.md 文件中读取内容
        category=Category.objects.create(name='Markdown Test'),  # 创建一个新的类别
        author=user,  # 文章作者设定为已创建的超级用户
    )

    # 创建一些在过去一年内发布的假文章
    print('create some faked posts published within the past year')
    fake = faker.Faker('zh_CN')  # 生成中文假数据
    for _ in range(200):
        tags = Tag.objects.order_by('?')  # 随机顺序标签
        tag1 = tags.first()  # 取第一个标签
        tag2 = tags.last()  # 取最后一个标签
        cate = Category.objects.order_by('?').first()  # 随机选择一个类别
        created_time = fake.date_time_between(
            start_date='-1y', end_date='now',
            tzinfo=timezone.get_current_timezone()
        )  # 生成一个在过去一年的随机时间

        post = Post.objects.create(
            title=fake.sentence().rstrip('.'),
            body='\n\n'.join(fake.paragraphs(10)),  # 生成文章内容，包含 10 个段落
            created_time=created_time,
            category=cate,
            author=user,
        )

        # 为每篇文章添加两个随机标签
        post.tags.add(tag1, tag2)
        post.save()

    # 为前 20 篇文章创建一些假评论
    print('create some faked comments...')
    for post in Post.objects.all()[:20]:
        post_created_time = post.created_time
        delta_in_days = '-' + str((timezone.now() - post_created_time).days) + 'd'  # 格式类似于 -10d，表示当前时间之前的 10 天
        for _ in range(random.randrange(3, 15)):  # 为每篇文章生成 3 到 15 条随机评论
            Comment.objects.create(
                name=fake.name(),
                email=fake.email(),
                url=fake.uri(),
                text=fake.paragraphs(),
                created_time=fake.date_time_between(
                    start_date=delta_in_days,
                    end_date='now',
                    tzinfo=timezone.get_current_timezone()
                ),  # 生成随机评论时间
                post=post,  # 评论所属文章
            )
    print('done')
