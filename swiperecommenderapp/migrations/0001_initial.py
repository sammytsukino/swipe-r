import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MediaItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('normalized_title', models.SlugField(max_length=255)),
                ('media_type', models.CharField(choices=[('movie', 'Movie'), ('tv', 'Series')], max_length=10)),
                ('release_year', models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1888), django.core.validators.MaxValueValidator(2100)])),
                ('overview', models.TextField(blank=True)),
                ('genres', models.JSONField(blank=True, default=list)),
                ('poster_url', models.URLField(blank=True)),
                ('imdb_id', models.CharField(blank=True, max_length=20)),
                ('tmdb_id', models.PositiveIntegerField(blank=True, null=True, unique=True)),
                ('tvdb_id', models.CharField(blank=True, max_length=32, null=True, unique=True)),
                ('external_payload', models.JSONField(blank=True, default=dict)),
                ('popularity', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-popularity', 'title'],
                'indexes': [models.Index(fields=['media_type', 'release_year'], name='swiperecomm_media_t_49bbe9_idx')],
                'constraints': [models.UniqueConstraint(fields=('normalized_title', 'release_year', 'media_type'), name='uniq_mediaitem_title_year_type')],
            },
        ),
        migrations.CreateModel(
            name='RecommendationSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField(default=0.0)),
                ('reason', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('media_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendation_snapshots', to='swiperecommenderapp.mediaitem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendation_snapshots', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-score', '-created_at'],
                'indexes': [models.Index(fields=['user', '-score'], name='swiperecomm_user_id_5bb4f7_idx')],
            },
        ),
        migrations.CreateModel(
            name='UserSwipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('decision', models.CharField(choices=[('like', 'Like'), ('dislike', 'Dislike')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('media_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='swipes', to='swiperecommenderapp.mediaitem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='swipes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['user', 'decision'], name='swiperecomm_user_id_0e65f3_idx')],
                'constraints': [models.UniqueConstraint(fields=('user', 'media_item'), name='uniq_userswipe_user_media')],
            },
        ),
    ]
