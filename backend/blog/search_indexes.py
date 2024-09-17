from haystack import indexes
from .models import Post


# 定义一个索引类 PostIndex，用于 Haystack 和 Elasticsearch 的交互
class PostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)  # 默认搜索字段
    title = indexes.CharField(model_attr='title')  # 定义 title 字段，索引模型的 title 属性
    body = indexes.CharField(model_attr='body')  # 定义 body 字段，索引模型的 body 属性

    def get_model(self):
        """返回与当前索引相关联的模型类"""
        return Post

    def index_queryset(self, using=None):
        """定义要被索引的数据集"""
        return self.get_model().objects.all()  # 这里返回 Post 模型的所有对象
