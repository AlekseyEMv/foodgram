from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from foodgram_backend.settings import DEBUG, MEDIA_ROOT, MEDIA_URL


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
]

if DEBUG:
    import debug_toolbar
    urlpatterns += (path('__debug__/', include(debug_toolbar.urls)),)
    urlpatterns += static(
        MEDIA_URL, document_root=MEDIA_ROOT
    )
