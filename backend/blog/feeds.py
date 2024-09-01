from django.contrib.syndication.views import Feed
from django.urls import reverse
from blog.models import Post


class LatestPostsFeed(Feed):
    # RSS feed 的标题，通常是博客的名称
    title = "Quill's Blog"

    # RSS feed 的链接，指向订阅源的内容的 URL 地址
    link = "/rss/"

    # RSS feed 的描述，用于简要说明该订阅源的内容
    description = "Updates on new blog posts."

    # 返回最新的博客文章，按照创建时间倒序排列
    def items(self):
        return Post.objects.order_by('-created_time')[:5]

    # 定义每个 RSS 条目的标题，通常是博客文章的标题
    def item_title(self, item):
        return item.title

    # 定义每个 RSS 条目的描述，通常是博客文章的摘要
    def item_description(self, item):
        return item.excerpt

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item):
        # 使用 Django 的 reverse 函数根据 URL 名称生成文章的详细页面链接
        return reverse("blog:detail", args=[item.pk])

    # 根据需求，扩展返回文章的发布时间、作者等额外信息
    def item_pubdate(self, item):
        return item.created_time

    def item_author(self, item):
        return item.author
