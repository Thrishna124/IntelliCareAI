from faker import Faker
import random

fake = Faker("en_IN")

random.seed(42)
Faker.seed(42)


def first_name(gender):

    if gender == "Male":
        return fake.first_name_male()

    return fake.first_name_female()


def middle_name():

    if random.random() < 0.30:
        return fake.first_name()

    return ""


def last_name():
    return fake.last_name()


def phone():
    return str(random.randint(6000000000, 9999999999))


def address():

    return {
        "address": fake.street_address(),
        "city": fake.city(),
        "state": fake.state(),
        "pincode": fake.postcode(),
    }


def dob(age):

    today = fake.date_this_year()

    return fake.date_of_birth(
        minimum_age=age,
        maximum_age=age
    )