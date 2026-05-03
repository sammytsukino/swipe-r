from django.db import transaction
from django.utils.text import slugify

from swiperecommenderapp.clients import ExternalAPIError, RPDBClient, TMDBClient, YouTubeClient
from swiperecommenderapp.models import MediaItem


class CatalogService:
    def __init__(self):
        self.tmdb_client = TMDBClient()
        self.rpdb_client = RPDBClient()
        self.youtube_client = YouTubeClient()

    def fetch_and_store_candidates(self, query=None, limit=40):
        normalized_items = []

        normalized_items.extend(
            [TMDBClient.normalize_item(item) for item in self._safe_fetch_tmdb(limit=limit)]
        )

        deduplicated = self._deduplicate_items(normalized_items)[:limit]
        return self._upsert_items(deduplicated)

    def _safe_fetch_tmdb(self, limit):
        try:
            return self.tmdb_client.fetch_trending(media_type="all", page=1)[:limit]
        except ExternalAPIError:
            return []

    def _deduplicate_items(self, items):
        dedup_map = {}
        for item in items:
            if not item.get("title"):
                continue
            key = self._item_dedup_key(item)
            if key not in dedup_map:
                dedup_map[key] = item
            elif item.get("popularity", 0) > dedup_map[key].get("popularity", 0):
                dedup_map[key] = item
        return list(dedup_map.values())

    @staticmethod
    def _item_dedup_key(item):
        if item.get("tmdb_id"):
            return f"tmdb:{item['tmdb_id']}"
        if item.get("tvdb_id"):
            return f"tvdb:{item['tvdb_id']}"
        return (
            f"name:{slugify(item.get('title', ''))}:"
            f"{item.get('release_year')}:{item.get('media_type')}"
        )

    @transaction.atomic
    def _upsert_items(self, items):
        persisted = []
        for item in items:
            imdb_id = item.get("imdb_id") or ""
            poster_url = item.get("poster_url", "")
            trailer_url = ""
            try:
                rpdb_poster = self.rpdb_client.poster_url(
                    media_type=item.get("media_type", MediaItem.TYPE_MOVIE),
                    imdb_id=imdb_id,
                    tmdb_id=item.get("tmdb_id"),
                    tvdb_id=item.get("tvdb_id"),
                )
                poster_url = rpdb_poster or poster_url
            except ExternalAPIError:
                pass
            try:
                trailer_url = self.youtube_client.find_trailer_url(
                    title=item.get("title", ""),
                    media_type=item.get("media_type", MediaItem.TYPE_MOVIE),
                    release_year=item.get("release_year"),
                )
            except ExternalAPIError:
                trailer_url = ""

            defaults = {
                "title": item.get("title"),
                "media_type": item.get("media_type", MediaItem.TYPE_MOVIE),
                "release_year": item.get("release_year"),
                "overview": item.get("overview", ""),
                "genres": item.get("genres") or [],
                "poster_url": poster_url,
                "imdb_id": imdb_id,
                "tvdb_id": item.get("tvdb_id") or None,
                "youtube_trailer_url": trailer_url,
                "external_payload": item.get("external_payload", {}),
                "popularity": item.get("popularity") or 0.0,
            }

            if item.get("tmdb_id"):
                media_item, _ = MediaItem.objects.update_or_create(
                    tmdb_id=item["tmdb_id"], defaults=defaults
                )
            elif item.get("tvdb_id"):
                media_item, _ = MediaItem.objects.update_or_create(
                    tvdb_id=item["tvdb_id"], defaults=defaults
                )
            else:
                media_item, _ = MediaItem.objects.update_or_create(
                    normalized_title=slugify(item.get("title", "")),
                    release_year=item.get("release_year"),
                    media_type=item.get("media_type", MediaItem.TYPE_MOVIE),
                    defaults=defaults,
                )
            persisted.append(media_item)
        return persisted
