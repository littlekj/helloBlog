from django import forms
from blog.models import Post


class PostForm(forms.ModelForm):
    class Meta:
        """Meta 类定义了表单的模型和字段，以及字段的显示方式"""
        model = Post
        fields = '__all__'  # Django 的 ModelForm 会自动忽略某些字段类型，比如只读字段
        widgets = {
            'excerpt': forms.Textarea(attrs={'rows': 5, 'cols': 80}),
        }
