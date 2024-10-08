# Generated by Django 4.1.7 on 2023-08-03 14:11

from django.db import migrations
from django.db.models import Q


def update_city_coordinates(apps, schema_editor):
    from services.yandex_geo import YandexGeocoderClient
    from config.settings import YANDEX_GEOCODER_API_KEY

    geocoder_client = YandexGeocoderClient(YANDEX_GEOCODER_API_KEY)
    City = apps.get_model("company", "City")
    cities = City.objects.filter(Q(latitude=None) | Q(longitude=None))
    for city in cities:
        address_data = geocoder_client.get_coordinates_from_city(city)
        city.latitude, city.longitude = (
            address_data.latitude,
            address_data.longitude,
        )
        city.save()


class Migration(migrations.Migration):

    dependencies = [
        ("company", "0012_city_latitude_city_longitude"),
    ]

    operations = [
        migrations.RunPython(update_city_coordinates),
    ]
