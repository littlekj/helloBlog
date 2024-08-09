from django.db import models
from django.utils import timezone
# Create your models here.

class Comment(models.Model):
    """
    评论模型类，用于存储文章评论信息
    """
    name = models.CharField('名字', max_length=255)
    email = models.EmailField('邮箱')
    url = models.URLField('网站', blank=True)  # 评论者的网站链接，可选字段
    text = models.TextField('内容')
    created_time = models.DateTimeField('创建时间', default=timezone.now)  # 评论的创建时间，默认当前时间
    post = models.ForeignKey('blog.Post', verbose_name='文章', on_delete=models.CASCADE)  # 外键，关联到blog应用中的Post模型类

    class Meta:
        """
        模型的元数据，定义模型在 Django 管理后台的显示名称
        """
        verbose_name = '评论'
        verbose_name_plural = verbose_name
        ordering = ['-created_time', 'name']

    def __str__(self):
        # format方法用于格式化字符串，替换占位符为实际的值
        return '{}: {}'.format(self.name, self.text[:20])
