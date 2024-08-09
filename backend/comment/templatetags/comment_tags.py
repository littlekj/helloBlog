from django import template
from comment.forms import CommentForm

register = template.Library()


@register.inclusion_tag('comment/inclusions/_form.html', takes_context=True)
def show_comment_form(context, post, form=None):
    """
    显示评论表单
    """
    if form is None:
        form = CommentForm()
    return {
        'form': form,
        'post': post,
    }


@register.inclusion_tag('comment/inclusions/_list.html', takes_context=True)
def show_comments(context, post):
    """
    显示评论列表
    :param context: 上下文
    :param post: 文章
    :return: 包含评论计数和评论列表的字典
    """
    # 获取当前文章的评论列表，按照创建时间倒序排列
    # comment_set 是为外键自动生成的关系管理器
    comment_list = post.comment_set.all().order_by('-created_time')

    comment_count = comment_list.count()

    return {
        'comment_count': comment_count,
        'comment_list': comment_list,
    }
