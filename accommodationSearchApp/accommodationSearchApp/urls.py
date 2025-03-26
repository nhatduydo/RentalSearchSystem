from django.contrib import admin
from django.urls import path, include, re_path

urlpatterns = [
    path ('', include('accommodationSearch.urls')),
    path('admin/', admin.site.urls),
    re_path(r'^ckeditor/', include('ckeditor_uploader.urls')),
]
