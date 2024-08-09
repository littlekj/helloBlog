from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from blog.models import Post
from comment.forms import CommentForm
from django.contrib import messages

# Create your views here.

@require_POST
def comment(request, post_pk):
    """
    发表评论
    :param request:
    :param post_pk: 指定博客文章的 id
    """
    # 获取指定 id 的博客文章
    post = get_object_or_404(Post, pk=post_pk)

    # 从请求的 POST 数据创建一个表单实例
    # request.POST 是一个类字典对象，包含了用户提交的表单数据
    form = CommentForm(request.POST)

    # 检查表单是否有效
    if form.is_valid():
        # 如果表单数据有效，使用表单数据创建一个新的 Comment 对象
        # commit=False 意味着尚未将对象保存到数据库中
        comment = form.save(commit=False)

        # 将评论与当前文章关联
        comment.post = post

        # 保存评论到数据库
        comment.save()

        messages.add_message(request, messages.SUCCESS, '评论发表成功！', extra_tags='success')

        # 使用 redirect 重定向到 post 的详情视图
        # 当 redirect 函数参数是一个模型对象时，会自动调用该对象的 get_absolute_url 方法
        # 并将请求重定向到该方法返回的 URL
        return redirect(post)
    print("testtest")
    # 如果表单数据无效，渲染一个预览页面显示表单错误信息
    # 传递当前文章对象和表单实例到模板中，以便在模板中显示错误信息和生成表单的提交地址
    context = {
        'post': post,
        'form': form,
    }
    messages.add_message(request, messages.ERROR, '评论发表失败！请检查表单内容后重新提交。', extra_tags='danger')
    return render(request, 'comment/inclusions/_preview.html', context=context)
