from django.contrib import admin

# Register your models here.

from django.contrib import admin
from comment.models import Comment


class CommentAdmin(admin.ModelAdmin):
    """
    配置 Comment 模型在 Django 管理后台的显示和编辑行为。
    """

    # 定义在 Django 管理后台的列表视图中显示的字段
    list_display = ['name', 'email', 'url', 'post', 'created_time']

    # 定义在 Django 管理后台的编辑页面中显示的字段
    fields = ['name', 'email', 'url', 'text', 'post']


# 注册 Comment 模型及其对应的管理类 CommentAdmin
admin.site.register(Comment, CommentAdmin)
