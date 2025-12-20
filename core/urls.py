"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from main.views import *
from main import views
from main.weather_app import weather_project_view
from main.stock_predictor import stock_predictor_view
from main.cheap_flight_finder import cheap_flight_finder_view

from django.contrib.sitemaps.views import sitemap
from main.sitemap import StaticViewSitemap 





sitemaps = {
    "static": StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("main.urls")),  # <-- ana səhifə BURA GƏLİR
    path('django/',get_django, name="django"),
    path('flask/',get_flask,name="flask"),
    path('pandas/',get_pandas,name="pandas"),
    path('git/',get_git,name="git"),
    path('crud/',get_crud,name="crud"),
    path('weather-app/', weather_project_view, name="weather_app"),
    path('python-basics/',get_python_basics,name="python-basics"),
    path('about/', views.about, name="about"),
    path('4o4-page/',get4o4, name='4o4-page'),
    path('stock-predictor/',stock_predictor_view, name="stock-predictor"),
    path('cheap-flight-finder/', cheap_flight_finder_view, name="cheap_flight_finder"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path('numpy/',get_numpy, name='numpy'),
    path('numpy/',get_matplotlib, name='matplotlib'),
]

