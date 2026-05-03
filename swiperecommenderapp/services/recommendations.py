from collections import Counter

from swiperecommenderapp.models import MediaItem, RecommendationSnapshot, UserSwipe
from swiperecommenderapp.services.catalog import CatalogService


class RecommendationService:
    def __init__(self):
        self.catalog_service = CatalogService()

    def record_swipe(self, user, media_item, decision):
        swipe, _ = UserSwipe.objects.update_or_create(
            user=user,
            media_item=media_item,
            defaults={"decision": decision},
        )
        return swipe

    def get_next_candidate(self, user, media_type=None):
        voted_ids = list(UserSwipe.objects.filter(user=user).values_list("media_item_id", flat=True))
        queryset = MediaItem.objects.exclude(id__in=voted_ids)
        if media_type in {MediaItem.TYPE_MOVIE, MediaItem.TYPE_TV}:
            queryset = queryset.filter(media_type=media_type)

        candidate = queryset.exclude(poster_url="").order_by("-popularity", "title").first()
        if not candidate:
            candidate = queryset.order_by("-popularity", "title").first()
        if candidate:
            return candidate

        fetched_items = self.catalog_service.fetch_and_store_candidates(limit=40)
        for item in fetched_items:
            if item.id not in voted_ids:
                if media_type in {MediaItem.TYPE_MOVIE, MediaItem.TYPE_TV}:
                    if item.media_type != media_type:
                        continue
                return item
        return None

    def build_recommendations(self, user, limit=10, media_type=None):
        likes = UserSwipe.objects.filter(user=user, decision=UserSwipe.DECISION_LIKE)
        dislikes = UserSwipe.objects.filter(user=user, decision=UserSwipe.DECISION_DISLIKE)
        if media_type in {MediaItem.TYPE_MOVIE, MediaItem.TYPE_TV}:
            likes = likes.filter(media_item__media_type=media_type)
            dislikes = dislikes.filter(media_item__media_type=media_type)
        disliked_ids = list(dislikes.values_list("media_item_id", flat=True))

        if not likes.exists():
            fallback = MediaItem.objects.exclude(id__in=disliked_ids)
            if media_type in {MediaItem.TYPE_MOVIE, MediaItem.TYPE_TV}:
                fallback = fallback.filter(media_type=media_type)
            fallback = fallback.order_by("-popularity", "title")[:limit]
            return self._snapshot(user, fallback, "Títulos populares", media_type=media_type)

        liked_ids = list(likes.values_list("media_item_id", flat=True))
        liked_items = MediaItem.objects.filter(id__in=liked_ids)

        genre_weights = Counter()
        type_weights = Counter()
        for item in liked_items:
            for genre in item.genres:
                genre_weights[str(genre)] += 1
            type_weights[item.media_type] += 1

        candidates = MediaItem.objects.exclude(id__in=liked_ids + disliked_ids)
        if media_type in {MediaItem.TYPE_MOVIE, MediaItem.TYPE_TV}:
            candidates = candidates.filter(media_type=media_type)
        scored = []
        for candidate in candidates:
            score = 0.0
            for genre in candidate.genres:
                score += genre_weights[str(genre)] * 1.8
            score += type_weights[candidate.media_type] * 1.2
            score += candidate.popularity * 0.03
            if score > 0:
                scored.append((candidate, score))

        scored.sort(key=lambda row: row[1], reverse=True)
        top_items = [row[0] for row in scored[:limit]]
        if not top_items:
            fallback = MediaItem.objects.exclude(id__in=liked_ids + disliked_ids)
            if media_type in {MediaItem.TYPE_MOVIE, MediaItem.TYPE_TV}:
                fallback = fallback.filter(media_type=media_type)
            fallback = fallback.order_by("-popularity", "title")[:limit]
            return self._snapshot(
                user,
                fallback,
                "Títulos populares (vota más para afinar sugerencias)",
                media_type=media_type,
            )
        return self._snapshot(user, top_items, "Según tus gustos", media_type=media_type)

    def _snapshot(self, user, items, reason, media_type=None):
        snapshots_queryset = RecommendationSnapshot.objects.filter(user=user)
        if media_type in {MediaItem.TYPE_MOVIE, MediaItem.TYPE_TV}:
            snapshots_queryset = snapshots_queryset.filter(media_item__media_type=media_type)
        snapshots_queryset.delete()
        snapshots = []
        score = len(items)
        for item in items:
            snapshots.append(
                RecommendationSnapshot(
                    user=user,
                    media_item=item,
                    score=float(score),
                    reason=reason,
                )
            )
            score -= 1
        if snapshots:
            RecommendationSnapshot.objects.bulk_create(snapshots)
        return [snapshot.media_item for snapshot in snapshots]
