from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class MediaItem(models.Model):
    TYPE_MOVIE = "movie"
    TYPE_TV = "tv"
    MEDIA_TYPE_CHOICES = [
        (TYPE_MOVIE, "Película"),
        (TYPE_TV, "Serie"),
    ]

    title = models.CharField(max_length=255)
    normalized_title = models.SlugField(max_length=255)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    release_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1888), MaxValueValidator(2100)],
    )
    overview = models.TextField(blank=True)
    genres = models.JSONField(default=list, blank=True)
    poster_url = models.URLField(blank=True)
    imdb_id = models.CharField(max_length=20, blank=True)
    tmdb_id = models.PositiveIntegerField(null=True, blank=True, unique=True)
    tvdb_id = models.CharField(max_length=32, null=True, blank=True, unique=True)
    external_payload = models.JSONField(default=dict, blank=True)
    popularity = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["normalized_title", "release_year", "media_type"],
                name="uniq_mediaitem_title_year_type",
            ),
        ]
        indexes = [models.Index(fields=["media_type", "release_year"])]
        ordering = ["-popularity", "title"]

    def save(self, *args, **kwargs):
        self.normalized_title = slugify(self.title or "")[:255]
        super().save(*args, **kwargs)

    @property
    def tmdb_page_url(self):
        if not self.tmdb_id:
            return ""
        if self.media_type == self.TYPE_MOVIE:
            segment = "movie"
        elif self.media_type == self.TYPE_TV:
            segment = "tv"
        else:
            return ""
        return f"https://www.themoviedb.org/{segment}/{self.tmdb_id}"

    def __str__(self):
        return f"{self.title} ({self.media_type})"


class UserSwipe(models.Model):
    DECISION_LIKE = "like"
    DECISION_DISLIKE = "dislike"
    DECISION_CHOICES = [
        (DECISION_LIKE, "Like"),
        (DECISION_DISLIKE, "Dislike"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="swipes",
    )
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="swipes",
    )
    decision = models.CharField(max_length=10, choices=DECISION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "media_item"],
                name="uniq_userswipe_user_media",
            ),
        ]
        indexes = [models.Index(fields=["user", "decision"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} -> {self.media_item} [{self.decision}]"


class RecommendationSnapshot(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommendation_snapshots",
    )
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="recommendation_snapshots",
    )
    score = models.FloatField(default=0.0)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "-score"])]
        ordering = ["-score", "-created_at"]

    def __str__(self):
        return f"{self.user} => {self.media_item} ({self.score:.2f})"
