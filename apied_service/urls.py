from django.contrib import admin
from django.urls import path, include

# NEW: Import settings and static for serving media files in development
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Gloex Administration"
admin.site.site_title = "Gloex Administration Portal"
admin.site.index_title = "Welcome to the Gloex Administration"

urlpatterns = [
    # Django Admin path (optional, but good practice)
    path('admin/', admin.site.urls),

    # API endpoints for the 'apied' application
    path('api/', include('apied.urls')),
]

# NEW: Serving media files during development (IMPORTANT: Do NOT use in production!)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)