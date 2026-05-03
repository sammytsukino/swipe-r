import hashlib
import json
import time

import requests
from django.conf import settings
from django.core.cache import cache


class ExternalAPIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class BaseAPIClient:
    cache_prefix = "external_api"

    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def _build_cache_key(self, path, method="GET", params=None, headers=None, json_data=None):
        payload = json.dumps(
            {
                "base_url": self.base_url,
                "method": method,
                "path": path,
                "params": params or {},
                "headers": headers or {},
                "json_data": json_data or {},
            },
            sort_keys=True,
            default=str,
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"{self.cache_prefix}:{digest}"

    def _request_json(
        self,
        method,
        path,
        params=None,
        headers=None,
        json_data=None,
        cache_key=None,
    ):
        key = cache_key or self._build_cache_key(
            path,
            method=method,
            params=params,
            headers=headers,
            json_data=json_data,
        )
        cached_data = cache.get(key)
        if cached_data is not None:
            return cached_data

        url = f"{self.base_url}{path}"
        timeout = settings.API_TIMEOUT_SECONDS
        retries = settings.API_RETRY_ATTEMPTS
        backoff = settings.API_RETRY_BACKOFF_SECONDS
        rate_limit_sleep = settings.API_RATE_LIMIT_SLEEP_SECONDS
        last_exception = None

        for attempt in range(retries + 1):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers,
                    json=json_data,
                    timeout=timeout,
                )
            except requests.RequestException as exc:
                last_exception = exc
                if attempt < retries:
                    time.sleep(backoff * (attempt + 1))
                    continue
                raise ExternalAPIError("No se pudo conectar con la API externa.") from exc

            if response.status_code == 429:
                if attempt < retries:
                    time.sleep(rate_limit_sleep * (attempt + 1))
                    continue
                raise ExternalAPIError("Rate limit excedido por la API externa.", status_code=429)

            if response.status_code >= 500 and attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue

            if response.status_code >= 400:
                raise ExternalAPIError(
                    f"Error de API externa ({response.status_code}).",
                    status_code=response.status_code,
                )

            try:
                data = response.json()
            except ValueError as exc:
                raise ExternalAPIError("Respuesta inválida (no JSON) de API externa.") from exc

            cache.set(key, data, timeout=settings.API_CACHE_TTL_SECONDS)
            return data

        raise ExternalAPIError("Error inesperado consumiendo API externa.") from last_exception

    def get_json(self, path, params=None, headers=None, cache_key=None):
        return self._request_json(
            "GET",
            path,
            params=params,
            headers=headers,
            cache_key=cache_key,
        )

    def post_json(self, path, json_data=None, headers=None, cache_key=None):
        return self._request_json(
            "POST",
            path,
            headers=headers,
            json_data=json_data,
            cache_key=cache_key,
        )
