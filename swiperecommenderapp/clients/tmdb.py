from django.conf import settings

from .base_http import BaseAPIClient, ExternalAPIError


class TMDBClient(BaseAPIClient):
    cache_prefix = "tmdb"

    def __init__(self):
        super().__init__(settings.TMDB_BASE_URL)

    def _auth(self):
        if settings.TMDB_READ_ACCESS_TOKEN:
            return (
                {"language": "es-ES"},
                {
                    "Authorization": f"Bearer {settings.TMDB_READ_ACCESS_TOKEN}",
                    "Accept": "application/json",
                },
            )
        if settings.TMDB_API_KEY:
            return ({"api_key": settings.TMDB_API_KEY, "language": "es-ES"}, None)
        raise ExternalAPIError(
            "TMDB no configurada. Define TMDB_READ_ACCESS_TOKEN o TMDB_API_KEY."
        )

    def fetch_trending(self, media_type="all", page=1):
        params, headers = self._auth()
        params.update({"page": page})
        data = self.get_json(
            f"/trending/{media_type}/day",
            params=params,
            headers=headers,
        )
        return data.get("results", [])

    @staticmethod
    def normalize_item(item):
        raw_type = item.get("media_type") or ("tv" if item.get("name") else "movie")
        media_type = "tv" if raw_type in {"tv", "series"} else "movie"
        title = item.get("title") or item.get("name") or ""
        release = item.get("release_date") or item.get("first_air_date") or ""
        year = int(release[:4]) if release[:4].isdigit() else None
        return {
            "source": "tmdb",
            "source_id": item.get("id"),
            "tmdb_id": item.get("id"),
            "tvdb_id": None,
            "title": title.strip(),
            "media_type": media_type,
            "release_year": year,
            "overview": item.get("overview", ""),
            "genres": item.get("genre_ids", []),
            "poster_url": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get("poster_path") else "",
            "popularity": float(item.get("popularity") or 0.0),
            "imdb_id": "",
            "external_payload": item,
        }
