from django.urls import path
from services.api import views

urlpatterns = [
    path("geocode/", views.yandex_geocoder, name="geocode"),
    path("approximate_price", views.approx_price, name="approximate_price"),
    path(
        "approximate_price_using_cities",
        views.approximate_price_using_cities,
        name="approximate_price_using_cities",
    ),
]
