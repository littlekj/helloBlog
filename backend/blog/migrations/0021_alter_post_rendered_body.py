# Generated by Django 4.2.16 on 2024-10-17 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0020_alter_post_rendered_body'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='rendered_body',
            field=models.TextField(blank=True, editable=False),
        ),
    ]
