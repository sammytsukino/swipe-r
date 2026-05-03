from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse, resolve

from swiperecommenderapp.context_processors import app_shell
from swiperecommenderapp.clients.base_http import BaseAPIClient, ExternalAPIError
from swiperecommenderapp.clients.rpdb import RPDBClient
from swiperecommenderapp.clients.tmdb import TMDBClient
from swiperecommenderapp.clients.tvdb import TVDBClient
from swiperecommenderapp.models import MediaItem, UserSwipe
from swiperecommenderapp.services.catalog import CatalogService
from swiperecommenderapp.services.recommendations import RecommendationService


class MediaItemModelTest(TestCase):
    def test_mediaitem_generates_normalized_title(self):
        item = MediaItem.objects.create(
            title="El Viaje de Chihiro",
            media_type=MediaItem.TYPE_MOVIE,
            release_year=2001,
        )
        self.assertEqual(item.normalized_title, "el-viaje-de-chihiro")


class UserSwipeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ana", password="test123456")
        self.item = MediaItem.objects.create(
            title="Dune",
            media_type=MediaItem.TYPE_MOVIE,
            release_year=2021,
        )

    def test_unique_swipe_per_user_item(self):
        UserSwipe.objects.create(user=self.user, media_item=self.item, decision=UserSwipe.DECISION_LIKE)
        with self.assertRaises(IntegrityError):
            UserSwipe.objects.create(
                user=self.user,
                media_item=self.item,
                decision=UserSwipe.DECISION_DISLIKE,
            )


class BaseAPIClientTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = BaseAPIClient("https://example.com")

    @patch("swiperecommenderapp.clients.base_http.requests.request")
    def test_get_json_uses_cache_for_repeated_requests(self, mock_request):
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {"results": [1, 2, 3]}
        mock_request.return_value = mock_response

        first = self.client.get_json("/items", params={"q": "test"})
        second = self.client.get_json("/items", params={"q": "test"})
        self.assertEqual(first, second)
        self.assertEqual(mock_request.call_count, 1)

    @patch("swiperecommenderapp.clients.base_http.requests.request")
    def test_rate_limit_raises_error_after_retries(self, mock_request):
        mock_request.return_value = Mock(status_code=429)
        with self.assertRaises(ExternalAPIError):
            self.client.get_json("/items")


class NormalizeClientsTest(TestCase):
    def test_tmdb_normalize_item(self):
        item = TMDBClient.normalize_item(
            {
                "id": 101,
                "media_type": "movie",
                "title": "Interstellar",
                "release_date": "2014-01-01",
            }
        )
        self.assertEqual(item["tmdb_id"], 101)
        self.assertEqual(item["release_year"], 2014)
        self.assertEqual(item["media_type"], "movie")

    def test_tvdb_normalize_item(self):
        item = TVDBClient.normalize_item({"tvdb_id": 321, "name": "Breaking Bad", "type": "series", "year": 2008})
        self.assertEqual(item["tvdb_id"], "321")
        self.assertEqual(item["media_type"], "tv")

    def test_tvdb_normalize_item_remote_ids_list(self):
        item = TVDBClient.normalize_item(
            {
                "tvdb_id": 777,
                "name": "Dark",
                "type": "series",
                "year": 2017,
                "remote_ids": [
                    {"sourceName": "IMDB", "id": "tt5753856"},
                ],
            }
        )
        self.assertEqual(item["imdb_id"], "tt5753856")

    def test_tvdb_normalize_item_ignores_non_dict(self):
        item = TVDBClient.normalize_item(["unexpected-list"])
        self.assertIsNone(item)

    def test_tvdb_unwrap_search_item_series_wrapper(self):
        wrapped = {"series": {"id": 123, "name": "The Last of Us"}}
        unwrapped = TVDBClient._unwrap_search_item(wrapped)
        self.assertEqual(unwrapped["id"], 123)
        self.assertEqual(unwrapped["type"], "series")

    @override_settings(RPDB_API_KEY="rpdb-key", RPDB_BASE_URL="https://api.ratingposterdb.com")
    def test_rpdb_builds_poster_url(self):
        url = RPDBClient().poster_url(media_type="movie", imdb_id="tt0816692")
        self.assertIn("tt0816692.jpg?fallback=true", url)
        self.assertIn("rpdb-key", url)

    @override_settings(RPDB_API_KEY="rpdb-key", RPDB_BASE_URL="https://api.ratingposterdb.com")
    def test_rpdb_builds_tmdb_poster_url(self):
        url = RPDBClient().poster_url(media_type="movie", tmdb_id=155)
        self.assertIn("/tmdb/poster-default/movie-155.jpg?fallback=true", url)


class CatalogServiceTest(TestCase):
    def test_deduplicate_prefers_more_popular_item(self):
        service = CatalogService()
        deduped = service._deduplicate_items(
            [
                {"title": "Dune", "media_type": "movie", "release_year": 2021, "tmdb_id": 1, "popularity": 10.0},
                {"title": "Dune", "media_type": "movie", "release_year": 2021, "tmdb_id": 1, "popularity": 90.0},
            ]
        )
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]["popularity"], 90.0)


class RecommendationServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="marta", password="test123456")
        self.item_like = MediaItem.objects.create(
            title="Arrival",
            media_type=MediaItem.TYPE_MOVIE,
            release_year=2016,
            genres=["Sci-Fi"],
            popularity=50,
        )
        self.item_candidate = MediaItem.objects.create(
            title="Blade Runner 2049",
            media_type=MediaItem.TYPE_MOVIE,
            release_year=2017,
            genres=["Sci-Fi"],
            popularity=70,
        )
        self.item_disliked = MediaItem.objects.create(
            title="Random Show",
            media_type=MediaItem.TYPE_TV,
            release_year=2020,
            genres=["Reality"],
            popularity=30,
        )
        self.service = RecommendationService()

    def test_build_recommendations_prioritizes_genre_affinity(self):
        UserSwipe.objects.create(user=self.user, media_item=self.item_like, decision=UserSwipe.DECISION_LIKE)
        UserSwipe.objects.create(user=self.user, media_item=self.item_disliked, decision=UserSwipe.DECISION_DISLIKE)
        results = self.service.build_recommendations(self.user, limit=5)
        self.assertIn(self.item_candidate, results)
        self.assertNotIn(self.item_disliked, results)

    def test_get_next_candidate_respects_media_type_filter(self):
        tv_item = MediaItem.objects.create(
            title="The Office",
            media_type=MediaItem.TYPE_TV,
            release_year=2005,
            popularity=95,
        )
        candidate_movie = self.service.get_next_candidate(self.user, media_type=MediaItem.TYPE_MOVIE)
        candidate_tv = self.service.get_next_candidate(self.user, media_type=MediaItem.TYPE_TV)
        self.assertEqual(candidate_movie.media_type, MediaItem.TYPE_MOVIE)
        self.assertEqual(candidate_tv, tv_item)


class SwipeFlowViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pepe", password="test123456")
        self.item = MediaItem.objects.create(
            title="The Matrix",
            media_type=MediaItem.TYPE_MOVIE,
            release_year=1999,
            popularity=90,
        )

    def test_swipe_requires_login(self):
        response = self.client.get(reverse("swipe"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_user_can_like_item(self):
        self.client.login(username="pepe", password="test123456")
        swipe_url = f"{reverse('swipe')}?type=movie"
        self.assertEqual(self.client.get(swipe_url).status_code, 200)
        response = self.client.post(
            swipe_url,
            {
                "media_item_id": self.item.id,
                "decision": UserSwipe.DECISION_LIKE,
                "selected_type": MediaItem.TYPE_MOVIE,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserSwipe.objects.filter(user=self.user, media_item=self.item).exists())

    def test_swipe_redirects_to_index_without_type_when_logged_in(self):
        self.client.login(username="pepe", password="test123456")
        response = self.client.get(reverse("swipe"))
        self.assertRedirects(response, reverse("index"))


class AppShellContextProcessorTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="ctxuser", password="ctx12345678")

    def test_shell_route_matches_resolver_url_name_across_sections(self):
        for url_name in ("swipe", "history", "recommendations"):
            with self.subTest(url_name=url_name):
                bare = reverse(url_name)
                request = self.factory.get(f"{bare}?type=movie")
                SessionMiddleware(lambda _req: HttpResponse()).process_request(request)
                request.session.save()
                request.user = self.user
                request.resolver_match = resolve(bare)
                ctx = app_shell(request)
                self.assertEqual(ctx["app_shell_route"], url_name)
