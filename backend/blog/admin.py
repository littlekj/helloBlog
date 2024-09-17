# Register your models here.
from django.contrib import admin
from blog.models import Post, Category, Tag
from django.utils.text import slugify


class PostAdmin(admin.ModelAdmin):
    """
    配置 Post 模型在 Django 管理后台的显示和编辑行为
    """
    # 定义在后台文章列表页面中显示的字段
    list_display = ['title', 'created_time', 'modified_time', 'get_categories', 'author']

    # 定义在后台文章编辑页面中显示的字段
    fields = ['title', 'slug', 'body', 'excerpt', 'categories', 'tags']

    def get_categories(self, obj):
        """
        自定义方法，用于在后台页面列表显示文章的分类信息，逗号分隔
        """
        return ', '.join([category.name for category in obj.categories.all()])

    # 设置 get_categories 方法的显示名称，用于列表页面的标题栏
    get_categories.short_description = '分类'

    def save_model(self, request, obj, form, change):
        """
        重写 save_model 方法，在保存模型时，将 author 字段设置为当前登录的用户
        """
        obj.author = request.user

        super().save_model(request, obj, form, change)


# class TagAdmin(admin.ModelAdmin):
#     """
#     配置 Tag 模型在 Django 管理后台的显示和编辑行为
#     """
#     def save_model(self, request, obj, form, change):
#         if not obj.slug:
#             obj.slug = slugify(obj.name, allow_unicode=True)
#         super().save_model(request, obj, form, change)


# 注册模型及其对应的管理类
admin.site.register(Post, PostAdmin)
admin.site.register(Category)
admin.site.register(Tag)
