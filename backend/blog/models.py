from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from markdown_it import MarkdownIt
from blog.utils import generate_summary, custom_slugify
from django.db.models import F


# Create your models here.

class Category(models.Model):
    """创建文章分类模型类"""
    name = models.CharField(max_length=100, unique=True)
    # 用于生成 URL 中的分类名
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)

    # 表示当前分类的父级分类，自关联，暂时不用
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')

    # 缓存路径
    path = models.CharField(max_length=255, blank=True, editable=False)

    class Meta:
        verbose_name = '分类'  # 定义模型的单数形式名称
        verbose_name_plural = verbose_name  # 定义模型的复数形式名称

        # 定义模型中需要在数据库级别创建的索引。这有助于提高查询性能。
        indexes = [
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        生成当前对象的绝对路径
        """
        if self.parent:
            ancestors = [self.slug]
            parent = self.parent
            while parent:
                ancestors.insert(0, parent.slug)
                parent = parent.parent
            return reverse('blog:category_detail', args=['/'.join(ancestors)])
        return reverse('blog:category_detail', args=[self.slug])


class Tag(models.Model):
    """创建文章标签模型类"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        生成当前对象的绝对路径
        """
        return reverse('blog:tag_detail', args=[self.slug])


class Post(models.Model):
    """创建文章模型类"""

    # 文章标题
    title = models.CharField('标题', max_length=100)

    # slug 是一个 URL 友好的字符串，用于在 URL 中表示文章
    # blank=True：在 Django 的表单或后台中，slug 字段可以为空。
    # null=True：在数据库中，slug 字段可以存储 NULL 值。
    slug = models.SlugField('slug', max_length=100, unique=True, blank=True, null=True)

    # 文章正文，使用 TextField 模型字段
    body = models.TextField('正文')

    # 文章目录
    toc = models.TextField('侧边栏目录', blank=True)

    # 文章创建时间，存储时间的字段用 DateTimeField 类型
    # default=timezone.now 表示默认值为当前时间
    # auto_now=True 表示每次保存对象时，自动将该字段设置为当前时间
    created_time = models.DateTimeField('创建时间', default=timezone.now, db_index=True)

    # 文章最后一次修改时间
    modified_time = models.DateTimeField('修改时间', null=True, blank=True, db_index=True)

    # 文章摘要，可以没有文章摘要，但默认情况下 CharField 要求必须存入数据，否则就会报错
    # 指定 CharField 的 blank=True 参数值后就可以允许空值了
    excerpt = models.CharField('摘要', max_length=200, blank=True)

    # 文章分类，文章与类别可以是多对多的关系，使用 ManyToManyField 定义
    # on_delete 参数指定当管理数据被删除时，被关联数据的行为
    categories = models.ManyToManyField(Category, verbose_name='分类', blank=True)

    # 文章标签，标签与文章是多对多关系，使用 ManyToManyField 定义
    tags = models.ManyToManyField(Tag, verbose_name='标签', blank=True)

    # 文章作者，这里 User 是从 django.contrib.auth.models 导入的
    author = models.ForeignKey(User, verbose_name='作者', on_delete=models.CASCADE)

    # 新增 views 字段，用于存储文章浏览量
    views = models.PositiveIntegerField(default=0, editable=False)

    # 新增一个字段，用于存储文章是否置顶
    pin = models.BooleanField(default=False)

    # 新增一个字段，用于存储文章渲染后的正文内容
    rendered_body = models.TextField(editable=False, blank=True)

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = verbose_name
        ordering = ['-created_time', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # 如果主键 pk 不存在，则首先保存以生成 pk
        if not self.pk:
            super().save(*args, **kwargs)
            if not self.slug:
                self.slug = self.generate_slug()
                self.save(update_fields=['slug'])
            return

        # update_fields 不会直接影响模型，仅适用于数据库更新
        # 它仅限于控制在将更改写入数据库，而不影响模型实例本身的字段值
        update_fields = kwargs.get('update_fields', [])

        # 更新 modified_time 字段逻辑：若非文章本身的内容的修改不更新
        # if self.pk and (not {'views', 'pin'}.intersection(update_fields)):  # 使用集合的交集判断
        #     # 更新 modified_time，因为其他字段正在被更新
        #     self.modified_time = timezone.now()

        super().save(*args, **kwargs)
        self.refresh_from_db()  # 重新加载模型实例的状态

    # 默认的 slugify 函数会将字符串中的非字母数字字符替换为短横线（-），并且会将多个短横线合并为一个。
    # 指定参数 allow_unicode=True，允许使用 Unicode 字符。
    # 使用 unidecode 将中文转成拼音或自定义 slugify 处理中文。
    def generate_slug(self):
        # self.slug = slugify(unidecode(self.title), allow_unicode=True)
        # 自动生成 slug
        day = str(self.created_time.day).lstrip('0')
        month = str(self.created_time.month).lstrip('0')
        year = str(self.created_time.year)[-2:]  # 只取年份的最后两位
        return f"{day}{month}{year}{self.pk}"

    def get_absolute_url(self):
        """
        生成当前对象的绝对路径
        """
        # 根据视图名称和参数反向生成 URL
        # blog:detail 是在 urls.py 中定义的视图名称，self.pk 是当前对象的 id 值（主键）
        # return reverse('blog:detail', kwargs={'pk': self.pk})
        return reverse('blog:detail', kwargs={'slug': self.slug})

    def increase_views(self):
        """
        增加文章浏览量
        """
        # self.views += 1
        self.views = F('views') + 1  # 使用 F() 表达式避免读-写竞争问题
        self.save(update_fields=['views'])


from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=Post)
def set_excerpt(sender, instance, **kwargs):
    if not instance.excerpt:
        md = MarkdownIt()
        html = md.render(instance.body)
        instance.excerpt = generate_summary(html, 120)
