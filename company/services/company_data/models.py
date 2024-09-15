from decimal import Decimal

from pydantic import BaseModel


class CompanyManager(BaseModel):
    name: str
    post: str


class CompanyState(BaseModel):
    status: str
    code: str = None
    actuality_date: int
    registration_date: int
    liquidation_date: int = None


class CompanyOpf(BaseModel):
    type: str
    code: str
    full: str
    short: str


class CompanyName(BaseModel):
    full_with_opf: str
    short_with_opf: str
    latin: str = None
    full: str
    short: str = None


class AddressDetail(BaseModel):
    postal_code: str = None
    country: str
    federal_district: str = None

    region: str = None
    region_type: str = None
    region_type_full: str = None

    area: str = None
    area_type: str = None
    area_type_full: str = None

    city: str = None
    city_type: str = None
    city_type_full: str = None
    city_area: str = None

    city_district: str = None
    city_district_type: str = None
    city_district_type_full: str = None

    settlement: str = None
    settlement_type: str = None
    settlement_type_full: str = None

    street: str = None
    street_type: str = None
    street_type_full: str = None

    house: str = None
    house_type: str = None
    house_type_full: str = None

    geo_lat: Decimal = None
    geo_lon: Decimal = None


class CompanyAddress(BaseModel):
    value: str
    unrestricted_value: str
    invalidity: str = None
    data: AddressDetail


class Person(BaseModel):
    surname: str
    name: str
    patronymic: str = None
    gender: str = None
    source: str = None
    qc: str = None


class CompanyData(BaseModel):
    kpp: str = None
    capital: str = None
    invalid: str = None
    fio: Person = None
    management: CompanyManager = None
    founders: str = None
    managers: str = None
    predecessors: str = None
    successors: str = None
    branch_type: str = None
    branch_count: int = None
    source: str = None
    qc: str = None
    hid: str = None
    type: str = None
    state: CompanyState
    opf: CompanyOpf
    name: CompanyName
    inn: str
    ogrn: str
    okpo: str = None
    okato: str = None
    oktmo: str = None
    okogu: str = None
    okfs: str = None
    okved: str
    okveds: str = None
    address: CompanyAddress
    phones: str = None
    emails: str = None
    ogrn_date: int
    okved_type: str = None
    employee_count: int = None
