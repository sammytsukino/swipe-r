from django.contrib import admin

from .models import MediaItem, RecommendationSnapshot, UserSwipe


@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    list_display = ("title", "media_type", "release_year", "tmdb_id", "tvdb_id", "popularity")
    list_filter = ("media_type", "release_year")
    search_fields = ("title", "imdb_id", "tmdb_id", "tvdb_id")


@admin.register(UserSwipe)
class UserSwipeAdmin(admin.ModelAdmin):
    list_display = ("user", "media_item", "decision", "created_at")
    list_filter = ("decision", "created_at")
    search_fields = ("user__username", "media_item__title")


@admin.register(RecommendationSnapshot)
class RecommendationSnapshotAdmin(admin.ModelAdmin):
    list_display = ("user", "media_item", "score", "reason", "created_at")
    list_filter = ("reason", "created_at")
    search_fields = ("user__username", "media_item__title")
