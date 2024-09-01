from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from markdown_it import MarkdownIt
from blog.utils import generate_summary


# Create your models here.

class Category(models.Model):
    """创建文章分类模型类"""
    name = models.CharField(max_length=100, unique=True)

    # slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Tag(models.Model):
    """创建文章标签模型类"""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Post(models.Model):
    """创建文章模型类"""

    # 文章标题
    title = models.CharField('标题', max_length=100)

    # 文章正文，使用 TextField 模型字段
    body = models.TextField('正文')

    # 文章目录
    toc = models.TextField('侧边栏目录', blank=True)

    # 文章创建时间，默认使用当前时间
    # 文章最后一次修改时间
    # 存储时间的字段用 DateTimeField 类型
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    modified_time = models.DateTimeField('修改时间')

    # 文章摘要，可以没有文章摘要，但默认情况下 CharField 要求必须存入数据，否则就会报错
    # 指定 CharField 的 blank=True 参数值后就可以允许空值了
    excerpt = models.CharField('摘要', max_length=200, blank=True)

    # 文章分类，分类与文章是一对多关系，使用 ForeignKey 定义
    # on_delete 参数指定当管理数据被删除时，被关联数据的行为
    category = models.ForeignKey(Category, verbose_name='分类', on_delete=models.CASCADE)
    # 文章标签，标签与文章是多对多关系，使用 ManyToManyField 定义
    tags = models.ManyToManyField(Tag, verbose_name='标签', blank=True)

    # 文章作者，这里 User 是从 django.contrib.auth.models 导入的
    author = models.ForeignKey(User, verbose_name='作者', on_delete=models.CASCADE)

    # 新增 views 字段，用于存储文章浏览量
    views = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = verbose_name
        ordering = ['-created_time', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.modified_time = timezone.now()

        # md = markdown.Markdown(extensions=[
        #     'markdown.extensions.extra',
        #     'markdown.extensions.codehilite'
        # ])
        #
        # # strip_tags 去掉 HTML 文本中全部的 HTML 标签，然后截取字符
        # self.excerpt = strip_tags(md.convert(self.body))[:120]

        # 生成摘要
        md = MarkdownIt()
        html = md.render(self.body)
        self.excerpt = generate_summary(html, 120)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        生成当前对象的绝对路径
        """
        # 根据视图名称和参数反向生成 URL
        # blog:detail 是在 urls.py 中定义的视图名称，self.pk 是当前对象的 id 值（主键）
        return reverse('blog:detail', kwargs={'pk': self.pk})

    # 增加 views 字段的自增方法
    def increase_views(self):
        self.views += 1
        self.save(update_fields=['views'])
