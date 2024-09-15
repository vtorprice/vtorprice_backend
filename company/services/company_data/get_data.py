import logging
from typing import Union

from django.conf import settings
from dadata import Dadata

from company.models import Company, City
from company.services.company_data.models import CompanyData

log = logging.getLogger(__name__)


def get_companies_data(query: str) -> Union[list[CompanyData], None]:
    """
    Get data about the companies by IIN or name from the DaData service

    :param query: string containing INN or company name
    :return: list objects of CompanyData model
    """
    dadata = Dadata(settings.DADATA_API_KEY)
    result = dadata.suggest("party", query)

    companies = []

    for item in result:
        data = item.get("data", None)

        if data is None:
            log.exception("DaData -- Incorrect data format")
            return None

        companies.append(CompanyData(**data))

    return companies


def get_companies(query: str) -> Union[list[Company], None]:
    """
    Gets a list of company objects by name or TIN number

    :param query: string containing INN or company name
    :return: list objects of Company model
    """

    companies_data = get_companies_data(query)

    companies = []

    cities_to_update = []  # for bulk update or create
    cities_names = []  # for getting list of cities from db
    city_company_map = (
        {}
    )  # for the subsequent connection of the company with the city

    # prepare data
    for company_data in companies_data:
        city_name = (
            company_data.address.data.city
            or company_data.address.data.settlement
        )
        cities_names.append(city_name)
        cities_to_update.append(City(name=city_name))

        company = Company(
            name=company_data.name.short_with_opf,
            inn=company_data.inn,
            address=company_data.address.unrestricted_value,
            latitude=company_data.address.data.geo_lat,
            longitude=company_data.address.data.geo_lon,
        )

        if city_name in city_company_map:
            city_company_map[city_name].append(company)
        else:
            city_company_map[city_name] = [company]

    # to avoid multiple queries to the database, we carry out bulk update or create cities
    City.objects.bulk_update_or_create(
        cities_to_update, ["name"], match_field="name"
    )

    cities = City.objects.filter(name__in=cities_names)

    # rel cities with companies
    for city in cities:
        city_companies = city_company_map[city.name]
        for company in city_companies:
            company.city = city
            companies.append(company)

    return companies
