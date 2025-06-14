# Register your models here.
from django.contrib import admin
from blog.models import Post, Category, Tag
from django.utils.text import slugify
from blog.utils import render_markdown
from django import forms


class PostModelForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'excerpt': forms.Textarea(attrs={'rows': 5, 'cols': 80}),
        }


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

    prepopulated_fields = {}  # 不自动生成 slug，翻译处理

    form = PostModelForm

    def get_categories(self, obj):
        """
        自定义方法，用于在后台页面显示文章的分类信息，逗号分隔
        """
        return ', '.join([category.name for category in obj.categories.all()])

    # 设置 get_categories 方法的显示名称，用于列表页面的标题栏
    get_categories.short_description = '分类'

    def save_model(self, request, obj, form, change):
        """
        重写 save_model 方法，change 参数表示模型是否是更新操作（而非创建新对象）
        """
        obj.author = request.user  # 在保存模型时，将 author 字段设置为当前登录的用户

        # update_fields 仅影响数据库操作，不会影响 obj 模型实例本身在内存中的数据状态。
        if change:
            if 'body' in form.changed_data or (not obj.rendered_body):
                # 若 body 字段被修改，则重新渲染 Markdown 内容
                obj.rendered_body = render_markdown(obj.body)
                obj.save(update_fields=['body', 'rendered_body'])
        obj.save()

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
