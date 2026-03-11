from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_alter_testexecution_comment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='testexecution',
            name='evidence',
            field=models.FileField(blank=True, null=True, upload_to='evidence/'),
        ),
    ]
