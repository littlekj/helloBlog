# Generated by Django 4.2.16 on 2024-09-21 04:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0019_post_rendered_body_alter_post_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='rendered_body',
            field=models.TextField(blank=True),
        ),
    ]
