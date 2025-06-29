from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from markdown_it import MarkdownIt
from blog.utils import generate_summary, slugify_translate
from django.db.models import F
from django.utils.crypto import get_random_string
from django.db.models.signals import pre_save
from django.dispatch import receiver


class Category(models.Model):
    """创建文章分类模型类"""
    name = models.CharField(max_length=100, unique=True)
    # 用于生成 URL 中的分类名
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)

    # 表示当前分类的父级分类，自关联，暂时不用
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')

    # 缓存路径
    path = models.CharField(max_length=255, blank=True, editable=False)

    # 显示声明管理器，用于管理模型实例
    objects = models.Manager()

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

    # 显示声明管理器，用于管理模型实例
    objects = models.Manager()

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

    # 显示声明管理器，用于管理模型实例
    objects = models.Manager()

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = verbose_name
        ordering = ['-created_time', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # 是否首次创建

        # 获取 update_fields，指定更新的字段
        update_fields = kwargs.get("update_fields")

        # 如果 slug 为空，不论是否创建，均根据标题生成
        if not self.slug:
            self.slug = slugify_translate(self.title)
            # 确保 slug 唯一（追加随机后缀）
            while Post.objects.filter(slug=self.slug).exists():
                self.slug = f"{self.slug}-{get_random_string(4)}"

        # 如果传入了 update_fields，则确保 slug 被加入进去
        if update_fields:
            update_fields = set(update_fields)
            update_fields.add("slug")  # 添加 slug 到更新字段
            kwargs["update_fields"] = list(update_fields)  # 更新回 kwargs
        else:
            # 如果没有指定 update_fields，则更新所有字段
            kwargs["update_fields"] = None

        # 可选：修改时间更新控制（如果启用 modified_time 字段）
        # update_fields = kwargs.get("update_fields")
        # if not is_new and update_fields:
        #     if not {"views", "pin"}.intersection(update_fields):
        #         self.modified_time = timezone.now()

        # 保存操作
        super().save(*args, **kwargs)

        # 保存后刷新字段（如 auto_now 相关字段）
        self.refresh_from_db()

    def generate_slug(self):
        """生成 slug 字段"""
        day = str(self.created_time.day).lstrip('0')
        month = str(self.created_time.month).lstrip('0')
        year = str(self.created_time.year)[-2:]  # 只取年份的最后两位
        return f"{year}{month}{day}{self.pk}"

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


@receiver(pre_save, sender=Post)  # 注册信号接收器
def set_excerpt(instance, **kwargs):
    """
    在 Post 保存前自动生成摘要
    :param instance: Post 实例
    :param kwargs: 其他参数
    """
    # 检查是否已存在摘要（避免覆盖用户手动设置的摘要）
    if not instance.excerpt:
        # 获取渲染后的正文内容
        if not instance.rendered_body:
            md = MarkdownIt()
            instance.rendered_body = md.render(instance.body)

        html = instance.rendered_body

        # 生成摘要（120个字符）
        instance.excerpt = generate_summary(html, 120)
