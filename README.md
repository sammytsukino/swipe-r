# Swipe Recommender (Django Mashup)

Aplicación web estilo swipe para descubrir y votar películas/series, y recibir recomendaciones personalizadas.

- Proyecto Django: `swiperecommenderproject`
- App principal: `swiperecommenderapp`
- Interfaz HTML con vistas de inicio, votar, recomendaciones e historial

---

## APIs externas utilizadas y rutas concretas

### 1) TMDB (The Movie Database)

- Base URL: `TMDB_BASE_URL` (por defecto `https://api.themoviedb.org/3`)
- Cliente: `swiperecommenderapp/clients/tmdb.py`
- Rutas usadas:
  - `GET /trending/{media_type}/day`
  - En este proyecto se usa principalmente `media_type=all`, con `language=es-ES` y paginación.
- Uso funcional:
  - Obtener títulos en tendencia (películas y series).
  - Base principal de descubrimiento para el modo swipe.
  - Fuente del `tmdb_id` para enlazar al detalle público de TMDB.

### 2) YouTube Data API v3

- Base URL: `YOUTUBE_BASE_URL` (por defecto `https://www.googleapis.com/youtube/v3`)
- Cliente: `swiperecommenderapp/clients/youtube.py`
- Rutas usadas:
  - `GET /search` (con `part=snippet`, `type=video`, `q=<titulo+trailer>`, `maxResults=1`)
- Uso funcional:
  - Buscar un tráiler relevante para cada candidato del modo swipe.
  - Guardar el enlace de YouTube en `MediaItem.youtube_trailer_url` para mostrar botón "Ver tráiler".

### 3) RPDB (RatingPosterDB)

- Base URL: `RPDB_BASE_URL` (por defecto `https://api.ratingposterdb.com`)
- Cliente: `swiperecommenderapp/clients/rpdb.py`
- Construcción de rutas para póster:
  - `/{RPDB_API_KEY}/imdb/poster-default/{imdb_id}.jpg?fallback=true`
  - `/{RPDB_API_KEY}/tmdb/poster-default/{movie|series}-{tmdb_id}.jpg?fallback=true`
  - `/{RPDB_API_KEY}/tvdb/poster-default/{movie|series}-{tvdb_id}.jpg?fallback=true`
- Uso funcional:
  - Mejorar/normalizar imágenes de portada en la interfaz.
  - Aplicar fallback visual consistente para tarjetas.

---

## Relación entre APIs (sentido del mashup)

El mashup combina tres servicios complementarios:

- `TMDB` aporta tendencias y metadata popular en español.
- `YouTube Data API` aporta un tráiler para cada título (película o serie).
- `RPDB` genera URLs de póster homogéneas para mostrar mejor catálogo.

Flujo resumido:

1. `CatalogService` consulta TMDB.
2. Normaliza estructuras a un esquema común (`MediaItem`).
3. Deduplica por IDs (`tmdb_id`) o título/año/tipo.
4. Pide a RPDB una portada óptima cuando hay identificadores.
5. Busca en YouTube el tráiler oficial y guarda la URL.
6. Guarda/actualiza el catálogo para consumo en páginas HTML.

Archivo clave de orquestación: `swiperecommenderapp/services/catalog.py`.

---

## Caché (requisito técnico)

El proyecto implementa caché en dos niveles:

- **Cache backend de Django:** `LocMemCache` en `swiperecommenderproject/settings.py`.
- **Cache de llamadas a APIs externas:** en `BaseAPIClient` (`swiperecommenderapp/clients/base_http.py`), con clave hash de método/path/params/headers/body.
- **TTL configurable:** `API_CACHE_TTL_SECONDS` (por defecto 600 segundos).

Evidencia en tests:

- `BaseAPIClientTest.test_get_json_uses_cache_for_repeated_requests` comprueba que dos llamadas iguales solo hacen una petición HTTP real.

---

## Interfaz HTML e interacción del usuario

Rutas internas de la app (`swiperecommenderapp/urls.py`):

- `GET /swiperecommenderapp/` -> Inicio
- `GET|POST /swiperecommenderapp/swipe?type=movie|tv` -> Votar (like/dislike)
- `GET /swiperecommenderapp/recommendations?type=movie|tv` -> Recomendaciones
- `GET /swiperecommenderapp/history?type=movie|tv` -> Historial
- `GET /swiperecommenderapp/login` y `POST /swiperecommenderapp/logout`

Dónde se visualizan datos de APIs:

- En **Votar**: título, año, sinopsis, póster del candidato y botón a tráiler en YouTube.
- En **Recomendaciones**: lista de títulos sugeridos con póster y motivo.
- En **Historial**: títulos votados con miniatura de póster.

---

## Configuración de API keys y variables

Las variables se leen desde `.env` en la raíz (plantilla en `.env.example`).

Variables obligatorias/recomendadas:

- `TMDB_READ_ACCESS_TOKEN` o `TMDB_API_KEY`
- `YOUTUBE_API_KEY`
- `RPDB_API_KEY`

Variables de soporte:

- `TMDB_BASE_URL`, `YOUTUBE_BASE_URL`, `RPDB_BASE_URL`
- `API_TIMEOUT_SECONDS`, `API_RETRY_ATTEMPTS`, `API_RETRY_BACKOFF_SECONDS`
- `API_RATE_LIMIT_SLEEP_SECONDS`, `API_CACHE_TTL_SECONDS`, `CACHE_LOCATION`

---

## Capturas

- Vista Login.
![Login](https://res.cloudinary.com/dsy30p7gf/image/upload/v1777815436/Captura_de_pantalla_2026-05-03_153557_jx59a8.png)
- Vista Inicio con selector Películas/Series.
![Inicio](https://res.cloudinary.com/dsy30p7gf/image/upload/v1777815436/Captura_de_pantalla_2026-05-03_153621_lkhtin.png)
- Vista Votar con datos del título y póster.
![Votar](https://res.cloudinary.com/dsy30p7gf/image/upload/v1777817438/Captura_de_pantalla_2026-05-03_161035_tjhprd.png)
- Vista Historial con votos previos.
![Historial](https://res.cloudinary.com/dsy30p7gf/image/upload/v1777815436/Captura_de_pantalla_2026-05-03_153701_amf5g7.png)
- Vista Recomendaciones con resultados y razones.
![Recomendaciones](https://res.cloudinary.com/dsy30p7gf/image/upload/v1777815436/Captura_de_pantalla_2026-05-03_153652_igqowg.png)

---

## Puesta en marcha local

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py manage.py migrate
py manage.py runserver
```

App en local:

- `http://127.0.0.1:8000/swiperecommenderapp/`

---

## Tests

```bash
py manage.py test swiperecommenderapp
```
