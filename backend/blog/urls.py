from django.urls import path, include
from blog import views
from blog.feeds import LatestPostsFeed

app_name = 'blog'  # 定义 URL 命名空间

urlpatterns = [
    # path('', views.index, name='index'),
    # path('posts/<int:pk>/', views.detail, name='detail'),
    # path('archive/<int:year>/<int:month>', views.archive, name='archive'),
    # path('category/<int:pk>', views.category, name='category'),
    # path('tag/<int:pk>', views.tag, name='tag'),

    path('', views.IndexView.as_view(), name='index'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='detail'),
    path('archive/<int:year>/<int:month>', views.ArchiveView.as_view(), name='archive'),
    path('category/<int:pk>', views.CategoryView.as_view(), name='category'),
    path('tag/<int:pk>', views.TagView.as_view(), name='tag'),

    path('rss/', LatestPostsFeed(), name='rss_feed'),

    path('search/', views.search, name='search')
    # path('search/', include('haystack.urls')),
]
