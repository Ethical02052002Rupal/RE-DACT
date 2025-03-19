from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.upload_file, name='upload_file'),
    path('image/', views.handle_image, name='handle_image'),
    path('video/', views.handle_video, name='handle_video'),
    path('pdf/', views.handle_pdf, name='handle_pdf'),
    path('download_p/', views.download_p, name='download_p'),
    path('download_v/', views.download_v, name='download_v'),
    path('download_i/', views.download_i, name='download_i'),
    path("update_nlp_words/", views.update_nlp_words, name="update_nlp_words"),
    path('add_redacted_term/', views.add_redacted_term, name='add_redacted_term'),
    path('remove_redacted_term/', views.remove_redacted_term, name='remove_redacted_term'),
    path('redact_pdf/', views.redact_pdf, name='redact_pdf'),
    path('download_pdf/', views.download_pdf, name='download_pdf'),
    path('download_video/', views.download_video, name='download_video'),
    path('download_image/', views.download_image, name='download_image'),
    path('detect_faces/', views.detect_faces, name='detect_faces'),
    path('redact_video/', views.redact_video, name='redact_video'),
    path('redact_image/', views.redact_image, name='redact_image'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
