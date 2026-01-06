
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('upload/', include('upload.urls')),
    path("", include("core.urls")),
    path("blog/", include("blog.urls")),
    path("game/", include("game.urls")),
    path('tools/', include('tools.urls')),

    # path('test-404/', TemplateView.as_view(template_name="404.html")),
    # path('test-500/', TemplateView.as_view(template_name="500.html")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]