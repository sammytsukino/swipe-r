from django.conf import settings
from django.core.cache import cache

from .base_http import BaseAPIClient, ExternalAPIError


class TVDBClient(BaseAPIClient):
    cache_prefix = "tvdb"
    token_cache_key = "tvdb:token"

    def __init__(self):
        super().__init__(settings.TVDB_BASE_URL)

    def _auth_headers(self):
        token = cache.get(self.token_cache_key)
        if not token:
            token = self._login()
            cache.set(self.token_cache_key, token, timeout=60 * 60 * 12)
        return {"Authorization": f"Bearer {token}"}

    def _login(self):
        if not settings.TVDB_API_KEY:
            raise ExternalAPIError("TVDB_API_KEY no configurada.")
        payload = {"apikey": settings.TVDB_API_KEY}
        if settings.TVDB_PIN:
            payload["pin"] = settings.TVDB_PIN
        data = self.post_json(
            "/login",
            json_data=payload,
            cache_key=f"{self.cache_prefix}:login:{settings.TVDB_API_KEY}:{settings.TVDB_PIN}",
        )
        token = data.get("data", {}).get("token")
        if not token:
            raise ExternalAPIError("TVDB no devolvió token.")
        return token

    def search(self, query, media_type="series", page=0):
        headers = self._auth_headers()
        params = {"query": query, "type": media_type, "page": page}
        data = self.get_json("/search", params=params, headers=headers)
        results = data.get("data", [])
        if not isinstance(results, list):
            return []
        return [self._unwrap_search_item(item) for item in results]

    @staticmethod
    def normalize_item(item):
        if not isinstance(item, dict):
            return None

        raw_type = (item.get("type") or "").lower()
        media_type = "tv" if "series" in raw_type else "movie"
        year = item.get("year") if isinstance(item.get("year"), int) else None
        tvdb_id = item.get("tvdb_id") or item.get("id")
        if not tvdb_id:
            return None

        return {
            "source": "tvdb",
            "source_id": tvdb_id,
            "tmdb_id": None,
            "tvdb_id": str(tvdb_id),
            "title": (item.get("name") or "").strip(),
            "media_type": media_type,
            "release_year": year,
            "overview": item.get("overview") or "",
            "genres": item.get("genres") or [],
            "poster_url": item.get("image_url") or "",
            "popularity": 0.0,
            "imdb_id": TVDBClient._extract_imdb_id(item.get("remote_ids")),
            "external_payload": item,
        }

    @staticmethod
    def _unwrap_search_item(item):
        if not isinstance(item, dict):
            return {}

        if isinstance(item.get("series"), dict):
            series = item["series"]
            series["type"] = series.get("type") or "series"
            return series

        if isinstance(item.get("movie"), dict):
            movie = item["movie"]
            movie["type"] = movie.get("type") or "movie"
            return movie

        return item

    @staticmethod
    def _extract_imdb_id(remote_ids):
        if isinstance(remote_ids, dict):
            value = remote_ids.get("imdb_id", "")
            return value if isinstance(value, str) else ""

        if isinstance(remote_ids, list):
            for entry in remote_ids:
                if not isinstance(entry, dict):
                    continue
                source_name = str(entry.get("sourceName", "")).lower()
                if source_name == "imdb":
                    remote_id = entry.get("id", "")
                    return str(remote_id) if remote_id else ""
                remote_id = entry.get("imdb_id")
                if isinstance(remote_id, str) and remote_id:
                    return remote_id

        return ""
