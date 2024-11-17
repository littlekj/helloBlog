from django.urls import path, include
from blog import views
from blog.feeds import LatestPostsFeed
from django.contrib.sitemaps.views import sitemap
from .sitemaps import PostSitemap, HomeSitemap, TagSitemap

app_name = 'blog'  # 定义 URL 命名空间

sitemaps = {
    'posts': PostSitemap,
    'home': HomeSitemap,
    'tags': TagSitemap,
}

urlpatterns = [
    # path('', views.index, name='index'),
    # path('posts/<int:pk>/', views.detail, name='detail'),
    # path('archive/<int:year>/<int:month>', views.archive, name='archive'),
    # path('category/<int:pk>', views.category, name='category'),
    # path('tag/<int:pk>', views.tag, name='tag'),

    path('', views.IndexView.as_view(), name='index'),
    # path('posts/<int:pk>/', views.PostDetailView.as_view(), name='detail'),
    path('posts/<slug:slug>/', views.PostDetailView.as_view(), name='detail'),
    # path('archive/<int:year>/<int:month>', views.ArchiveView.as_view(), name='archive'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    # 使用 path 转换器更宽松，能够处理几乎任何字符，包括中文
    path('categories/<path:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('tags/', views.TagListView.as_view(), name='tags'),
    path('tags/<path:slug>/', views.TagDetailView.as_view(), name='tag_detail'),
    path('archives/', views.ArchiveView.as_view(), name='archives'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('rss/', LatestPostsFeed(), name='rss_feed'),
    path('search/', views.search, name='search'),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]
