from urllib.parse import urlencode

from django.conf import settings

from .base_http import BaseAPIClient, ExternalAPIError


class YouTubeClient(BaseAPIClient):
    cache_prefix = "youtube"

    def __init__(self):
        super().__init__(settings.YOUTUBE_BASE_URL)

    def find_trailer_url(self, *, title, media_type, release_year=None):
        if not settings.YOUTUBE_API_KEY:
            raise ExternalAPIError("YOUTUBE_API_KEY no configurada.")
        if not title:
            return ""

        query = self._build_query(title=title, media_type=media_type, release_year=release_year)
        params = {
            "part": "snippet",
            "type": "video",
            "maxResults": 8,
            "order": "relevance",
            "q": query,
            "key": settings.YOUTUBE_API_KEY,
        }
        data = self.get_json("/search", params=params)
        items = data.get("items", [])
        if not items:
            return ""
        selected = self._choose_best_video(items=items, title=title, release_year=release_year)
        if not selected:
            return ""
        video_id = (selected.get("id") or {}).get("videoId")
        if not video_id:
            return ""
        return f"https://www.youtube.com/watch?{urlencode({'v': video_id})}"

    @staticmethod
    def _build_query(*, title, media_type, release_year=None):
        kind = "trailer pelicula" if media_type == "movie" else "trailer serie"
        parts = [title.strip(), kind, "oficial", "espanol"]
        if release_year:
            parts.append(str(release_year))
        return " ".join(part for part in parts if part)

    @classmethod
    def _choose_best_video(cls, *, items, title, release_year=None):
        valid_items = [item for item in items if isinstance(item, dict) and (item.get("id") or {}).get("videoId")]
        if not valid_items:
            return None
        scored = []
        for item in valid_items:
            score = cls._score_video(item=item, title=title, release_year=release_year)
            scored.append((score, item))
        scored.sort(key=lambda row: row[0], reverse=True)
        best_score, best_item = scored[0]
        if best_score <= 0:
            return None
        return best_item

    @staticmethod
    def _score_video(*, item, title, release_year=None):
        snippet = item.get("snippet") or {}
        raw_text = " ".join(
            str(part or "")
            for part in (
                snippet.get("title"),
                snippet.get("description"),
                snippet.get("channelTitle"),
            )
        ).lower()
        title_tokens = [token for token in str(title or "").lower().replace(":", " ").split() if len(token) > 2]

        score = 0
        if "trailer" in raw_text:
            score += 8
        if "teaser" in raw_text:
            score += 3
        if "official" in raw_text or "oficial" in raw_text:
            score += 5
        if release_year and str(release_year) in raw_text:
            score += 2
        for token in title_tokens:
            if token in raw_text:
                score += 2

        blocked_terms = (
            "opening",
            "op ",
            " ending",
            "ed ",
            "capitulo",
            "episodio",
            "episode",
            "full movie",
            "pelicula completa",
            "full hd",
            "resumen",
            "review",
            "reaccion",
            "reaction",
            "clip",
            "scene",
            "escena",
        )
        for term in blocked_terms:
            if term in raw_text:
                score -= 8
        return score
