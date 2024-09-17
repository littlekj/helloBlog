import os
import pathlib
import random
import sys
from datetime import timedelta

import django
import faker
from django.utils import timezone
from django.utils.text import slugify

# 将项目根目录添加到 Python 的模块搜索路径中
dir_name = os.path.dirname
BASE_DIR = dir_name(dir_name(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# 主程序执行，配置 Django 环境
if __name__ == '__main__':
    # 设置 Django 的配置模块
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'backend.settings.development')
    django.setup()

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
    user = User.objects.create_superuser('Quill', 'quill@mail.com', 'quill')

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
    post = Post.objects.create(
        title='Making a New World',
        body=sample_body,
        author=user,
    )

    # 创建一个新的类别
    category = Category.objects.create(name='Markdown Test')

    # 为 Post 对象添加类别
    post.categories.set([category])

    # 创建一些在过去一年内发布的假文章
    print('create some faked posts published within the past year')
    fake = faker.Faker('zh_CN')

    def create_unique_slug(title):
        slug = slugify(title)
        unique_slug = slug
        while Post.objects.filter(slug=unique_slug).exists():
            unique_slug = f'{slug}-{random.randint(1, 1000)}'
        return unique_slug

    for _ in range(50):
        tags = Tag.objects.order_by('?')[:2]  # 取两个随机标签
        categories = Category.objects.order_by('?')[:2]  # 取两个随机类别
        created_time = fake.date_time_between(
            start_date='-1y', end_date='now',
            tzinfo=timezone.get_current_timezone()
        )

        try:
            post = Post.objects.create(
                title=fake.sentence().rstrip('.'),
                slug=create_unique_slug(fake.sentence().rstrip('.')),
                body='\n\n'.join(fake.paragraphs(10)),
                created_time=created_time,
                author=user,
            )
            post.tags.set(tags)
            post.categories.set(categories)
        except Exception as e:
            print(f'Error creating post: {e}')

    # 为前 20 篇文章创建一些假评论
    print('create some faked comments...')
    for post in Post.objects.all()[:20]:
        post_created_time = post.created_time
        delta_in_days = '-' + str((timezone.now() - post_created_time).days) + 'd'
        for _ in range(random.randrange(3, 15)):
            try:
                Comment.objects.create(
                    name=fake.name(),
                    email=fake.email(),
                    url=fake.uri(),
                    text=' '.join(fake.paragraphs()),
                    created_time=fake.date_time_between(
                        start_date=delta_in_days,
                        end_date='now',
                        tzinfo=timezone.get_current_timezone()
                    ),
                    post=post,
                )
            except Exception as e:
                print(f'Error creating comment: {e}')

    print('done')
