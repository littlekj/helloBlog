from django.urls import path

from comment import views

app_name = 'comment'  # 定义 URL 命名空间

urlpatterns = [
    path('comment/<int:post_pk>/', views.comment, name='comment'),
]
