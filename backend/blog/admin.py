# Register your models here.
from django.contrib import admin
from blog.models import Post, Category, Tag
from blog.utils import render_markdown
from blog.forms import PostForm


class PostAdmin(admin.ModelAdmin):
    """
    配置 Post 模型在 Django 管理后台的显示和编辑行为
    """
    # 定义在后台文章列表页面中显示的字段
    list_display = ['title', 'id', 'created_time', 'modified_time', 'get_categories', 'author']

    # 定义在后台文章编辑页面中显示的字段
    fields = ['title', 'slug', 'body', 'excerpt', 'categories', 'tags']

    # 不可编辑字段设置为只读以便显示
    readonly_fields = ('rendered_body',)

    # prepopulated_fields = {}  # 已禁用，由翻译器自动生成 slug

    # 指定自定义表单类
    form = PostForm

    @admin.display(description='分类')
    def get_categories(self, obj):
        """
        自定义方法，用于在后台页面显示文章的分类信息，逗号分隔
        """
        return ', '.join([category.name for category in obj.categories.all()])

    def save_model(self, request, obj, form, change):
        """
        重写 save_model 方法，生成 toc 和 rendered_body
        change 参数表示模型是否是更新操作（而非创建新对象）
        """
        # 设置当前用户为作者
        obj.author = request.user

        # 仅在 body 字段被修改或首次创建时渲染 Markdown
        if (change and 'body' in form.changed_data) or not change:
            # 渲染正文并生成目录
            rendered_body, toc = render_markdown(obj.body)
            obj.rendered_body = rendered_body
            obj.toc = toc
            # 不需要显式调用 obj.save()，super().save_model() 会处理保存逻辑

        # 保存文章模型实例
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
