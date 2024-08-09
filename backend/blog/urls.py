from django.urls import path

from blog import views

app_name = 'blog'  # 定义 URL 命名空间

urlpatterns = [
    path('', views.index, name='home'),
    path('posts/<int:pk>/', views.detail, name='detail'),
    path('archive/<int:year>/<int:month>', views.archive, name='archive'),
    path('category/<int:pk>', views.category, name='category'),
    path('tag/<int:pk>', views.tag, name='tag'),
]
