from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("swiperecommenderapp", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="mediaitem",
            name="youtube_trailer_url",
            field=models.URLField(blank=True),
        ),
    ]
