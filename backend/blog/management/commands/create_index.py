# blog/management/commands/create_index.py
from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch
from django.conf import settings
from dotenv import load_dotenv
import os

# 加载 .env 文件中的环境变量
load_dotenv()

HOST = os.getenv('HOST')


class Command(BaseCommand):
    help = 'Create Elasticsearch index with optimized settings and mappings.'

    def handle(self, *args, **kwargs):
        # Initialize Elasticsearch client

        es = Elasticsearch(f'http://elastic:elastic@{HOST}:9200')

        index_name = settings.HAYSTACK_CONNECTIONS['default']['INDEX_NAME']

        # Delete old index if it exists
        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)
            self.stdout.write(self.style.WARNING(f'Index "{index_name}" deleted.'))

        # Define the index settings and mappings
        index_body = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "ik_max_word_analyzer": {
                            "type": "custom",
                            "tokenizer": "ik_max_word"
                        },
                        "english_analyzer": {
                            "type": "standard"
                        },
                        "mixed_language_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "asciifolding"
                            ]
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "title": {
                        "type": "text",
                        "analyzer": "mixed_language_analyzer"
                    },
                    "body": {
                        "type": "text",
                        "analyzer": "mixed_language_analyzer",
                        "copy_to": ["body_ik_max", "body_english"]
                    },
                    "body_ik_max": {
                        "type": "text",
                        "analyzer": "ik_max_word_analyzer"
                    },
                    "body_english": {
                        "type": "text",
                        "analyzer": "english_analyzer"
                    }
                }
            }
        }

        # Create the new index with the defined settings and mappings
        es.indices.create(index=index_name, body=index_body)
        self.stdout.write(self.style.SUCCESS(f'Successfully created index "{index_name}".'))
