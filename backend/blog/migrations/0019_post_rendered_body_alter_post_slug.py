# Generated by Django 4.2.16 on 2024-09-21 01:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0018_alter_category_slug_alter_post_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='rendered_body',
            field=models.TextField(blank=True, editable=False),
        ),
        migrations.AlterField(
            model_name='post',
            name='slug',
            field=models.SlugField(blank=True, max_length=100, null=True, unique=True, verbose_name='slug'),
        ),
    ]