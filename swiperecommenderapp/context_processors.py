from swiperecommenderapp.models import MediaItem


def app_shell(request):
    movie, tv = MediaItem.TYPE_MOVIE, MediaItem.TYPE_TV
    valid = {movie, tv}
    persisted = None
    active = None
    shell_route = ""

    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        persisted_raw = request.session.get("rating_mode")
        persisted = persisted_raw if persisted_raw in valid else None

        qt = request.GET.get("type")
        if qt in valid:
            active = qt
        else:
            active = persisted

        match = getattr(request, "resolver_match", None)
        url_name = getattr(match, "url_name", None) if match else None
        if url_name in {"swipe", "history", "recommendations"}:
            shell_route = url_name

    return {
        "rating_mode": persisted,
        "active_media_type": active,
        "app_shell_route": shell_route,
    }
