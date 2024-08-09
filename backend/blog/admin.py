from django.contrib import admin

# Register your models here.

from blog.models import Post, Category, Tag


class PostAdmin(admin.ModelAdmin):
    """
    配置 Post 模型在 Django 管理后台的显示和编辑行为
    """
    # 定义在后台页面列表显示的字段
    list_display = ['title', 'created_time', 'modified_time', 'category', 'author']

    # 定义在编辑页面上的显示的字段
    fields = ['title', 'body', 'excerpt', 'category', 'tags']

    def save_model(self, request, obj, form, change):
        """
        重写 save_model 方法，在保存模型时，将 author 字段设置为当前登录的用户
        """
        obj.author = request.user
        super().save_model(request, obj, form, change)


# 注册模型及其对应的管理类
admin.site.register(Post, PostAdmin)
admin.site.register(Category)
admin.site.register(Tag)
