from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from .models import MediaItem, RecommendationSnapshot, UserSwipe
from .services import RecommendationService


def index(request):
    return render(request, "swiperecommenderapp/index.html")


def _selected_media_type(request):
    media_type = request.GET.get("type")
    if media_type in {MediaItem.TYPE_MOVIE, MediaItem.TYPE_TV}:
        return media_type
    return None


def _selected_media_type_from_post(request):
    media_type = request.POST.get("selected_type") or ""
    if media_type in {MediaItem.TYPE_MOVIE, MediaItem.TYPE_TV}:
        return media_type
    return None


def _remember_rating_mode(request, media_type):
    if media_type in {MediaItem.TYPE_MOVIE, MediaItem.TYPE_TV}:
        request.session["rating_mode"] = media_type


def _swipe_redirect(media_type):
    return redirect(f"{reverse('swipe')}?type={media_type}")


class SwipeCandidate(LoginRequiredMixin, View):
    template_name = "swiperecommenderapp/swipe.html"
    recommendation_service = RecommendationService()

    def get(self, request):
        media_type = _selected_media_type(request)
        if not media_type:
            return redirect("index")
        _remember_rating_mode(request, media_type)
        candidate = self.recommendation_service.get_next_candidate(
            request.user,
            media_type=media_type,
        )
        return render(
            request,
            self.template_name,
            {
                "candidate": candidate,
                "selected_type": media_type,
            },
        )

    def post(self, request):
        decision = request.POST.get("decision")
        selected_type = _selected_media_type_from_post(request)
        if not selected_type:
            messages.error(
                request,
                "Elige en la página principal si quieres películas o series.",
            )
            return redirect("index")

        if decision not in {UserSwipe.DECISION_LIKE, UserSwipe.DECISION_DISLIKE}:
            messages.error(request, "Decisión no válida.")
            return _swipe_redirect(selected_type)

        media_item = get_object_or_404(MediaItem, id=request.POST.get("media_item_id"))
        if media_item.media_type != selected_type:
            messages.error(
                request,
                "Este título no coincide con el modo seleccionado.",
            )
            return _swipe_redirect(selected_type)
        self.recommendation_service.record_swipe(request.user, media_item, decision)
        return _swipe_redirect(selected_type)


class RecommendationList(LoginRequiredMixin, ListView):
    template_name = "swiperecommenderapp/recommendations.html"
    context_object_name = "recommendation_list"
    paginate_by = 12
    recommendation_service = RecommendationService()

    def get(self, request, *args, **kwargs):
        mt = _selected_media_type(request)
        if not mt:
            return redirect("index")
        _remember_rating_mode(request, mt)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        media_type = _selected_media_type(self.request)
        self.recommendation_service.build_recommendations(
            self.request.user,
            limit=30,
            media_type=media_type,
        )
        queryset = RecommendationSnapshot.objects.filter(user=self.request.user)
        if media_type:
            queryset = queryset.filter(media_item__media_type=media_type)
        return queryset.select_related("media_item")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_type"] = _selected_media_type(self.request)
        return context


class SwipeHistory(LoginRequiredMixin, View):
    template_name = "swiperecommenderapp/history.html"

    def get(self, request):
        media_type = _selected_media_type(request)
        if not media_type:
            return redirect("index")
        _remember_rating_mode(request, media_type)
        swipe_list = UserSwipe.objects.filter(user=request.user).select_related("media_item")
        if media_type:
            swipe_list = swipe_list.filter(media_item__media_type=media_type)
        paginator = Paginator(swipe_list, 12)
        page_obj = paginator.get_page(request.GET.get("page", 1))
        return render(
            request,
            self.template_name,
            {
                "page_obj": page_obj,
                "selected_type": media_type,
            },
        )
