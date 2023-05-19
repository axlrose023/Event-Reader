"""
URL configuration for Event_Viewer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.urls import path, include
from event_viewer.views import eventlog_reader, home, filter_events_success \
    , filter_events_failure, filtering_events, download_csv

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('simple_events/', eventlog_reader, name='eventlog_reader'),
    path('success_events/', filter_events_success, name='filter_events_success'),
    path('failure_events/', filter_events_failure, name='filter_events_failure'),
    path('filtering_events/', filtering_events, name='filtering_events'),
    path('download-csv/', download_csv, name='download_csv'),
    path('accounts/', include('accounts.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


handler400 = 'event_viewer.views.bad_request'
handler404 = 'event_viewer.views.page_not_found'
handler403 = 'event_viewer.views.permission_denied'
handler500 = 'event_viewer.views.server_error'
