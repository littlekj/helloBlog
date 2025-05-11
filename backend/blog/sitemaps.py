from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Post, Tag
from django.db.models import Count


class PostSitemap(Sitemap):
    """
    博客文章的站点地图
    """
    changefreq = "daily"  # 更新频率
    priority = 0.8  # 优先级

    def items(self):
        # 返回需要展示的文章
        return Post.objects.all().order_by('-modified_time')

    def lastmod(self, obj):
        # 返回文章的最后修改时间
        return obj.modified_time if obj.modified_time else obj.created_time

    # def location(self, obj):
    #     """
    #     Django Sitemap 框架会默认调用 get_absolute_url() 自动生成每条记录的 URL
    #    ，可以不需要再重写 location 方法。
    #     """
    #     return obj.get_absolute_url()


class HomeSitemap(Sitemap):
    """
    首页的站点地图
    """
    changefreq = "daily"
    priority = 1.0  # 优先级

    def items(self):
        return ['blog:index']  # index 是首页的 URL 名称

    def location(self, item):
        return reverse(item)


class TagSitemap(Sitemap):
    """
    标签的站点地图
    """
    priority = 0.5

    def items(self):
        """返回需要展示的标签"""
        # return Tag.objects.all().order_by('name')
        # 'post' 指的是 Tag 模型和 Post 模型之间的反向关系名称，它通常来源于 Post 模型中定义的 ManyToManyField 字段。
        return Tag.objects.annotate(num_posts=Count('post')).filter(num_posts__gt=5).order_by('-num_posts')

    def location(self, obj):
        return reverse('blog:tag_detail', args=[obj.slug])  # tag_detail 是标签详情页的 URL 名称
