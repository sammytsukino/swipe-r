from django.conf import settings

from .base_http import ExternalAPIError


class RPDBClient:
    default_query = "?fallback=true"

    def poster_url(self, media_type, imdb_id=None, tmdb_id=None, tvdb_id=None):
        if not settings.RPDB_API_KEY:
            raise ExternalAPIError("RPDB_API_KEY no configurada.")
        normalized_media_type = "series" if media_type == "tv" else "movie"

        if imdb_id:
            return (
                f"{settings.RPDB_BASE_URL}/{settings.RPDB_API_KEY}/imdb/poster-default/"
                f"{imdb_id}.jpg{self.default_query}"
            )

        if tmdb_id:
            return (
                f"{settings.RPDB_BASE_URL}/{settings.RPDB_API_KEY}/tmdb/poster-default/"
                f"{normalized_media_type}-{tmdb_id}.jpg{self.default_query}"
            )

        if tvdb_id:
            return (
                f"{settings.RPDB_BASE_URL}/{settings.RPDB_API_KEY}/tvdb/poster-default/"
                f"{normalized_media_type}-{tvdb_id}.jpg{self.default_query}"
            )

        return ""
