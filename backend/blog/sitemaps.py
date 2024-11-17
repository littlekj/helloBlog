from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Post, Tag


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
        return obj.modified_time


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
        return Tag.objects.all().order_by('name')

    def location(self, obj):
        return reverse('blog:tag_detail', args=[obj.slug])  # tag_detail 是标签详情页的 URL 名称
