from django import forms
from comment.models import Comment


class CommentForm(forms.ModelForm):
    """
    用于处理 Comment 模型的表单数据
    """

    class Meta:
        """
        Meta 内部类用于指定表单所使用的模型和字段
        """
        # 指定使用的模型
        model = Comment

        # 指定表单中显示的模型字段
        fields = ['name', 'email', 'url', 'text']
