# Generated by Django 4.2.14 on 2024-08-09 13:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_alter_category_options_alter_post_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-created_time', 'title'], 'verbose_name': '文章', 'verbose_name_plural': '文章'},
        ),
    ]