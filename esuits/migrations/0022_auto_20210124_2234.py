# Generated by Django 3.1.1 on 2021-01-24 13:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('esuits', '0021_auto_20201217_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionmodel',
            name='selected_version',
            field=models.IntegerField(default=1, verbose_name='表示するバージョン'),
        ),
        migrations.CreateModel(
            name='AnswerModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.IntegerField(blank=True, default=1, verbose_name='バージョン')),
                ('answer', models.TextField(blank=True, null=True, verbose_name='回答')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='esuits.questionmodel', verbose_name='質問')),
            ],
            options={
                'db_table': 'answers',
            },
        ),
    ]
