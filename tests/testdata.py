#!/usr/bin/env python

users = [
    {
        "firstName": "Mickey",
        "lastName": "Mouse",
        "cpf": "609.350.354-27",
        "email": "mickey.mouse@disney.com",
        "birthDate": "1928-11-18",
    },
    {
        "firstName": "Minnie",
        "lastName": "Mouse",
        "cpf": "673.810.785-46",
        "email": "minnie.mouse@disney.com",
        "birthDate": "1928-11-18",
    },
]

duplicate_user = {
    "firstName": "Mickey",
    "lastName": "Mouse Python Test",
    "cpf": "609.350.354-27",
    "email": "mickey.mouse2@disney.com",
    "birthDate": "2021-07-10",
}

new_user = {
    "firstName": "Donald",
    "lastName": "Duck",
    "cpf": "324.453.314-04",
    "email": "donald.duck@disney.com",
    "birthDate": "1934-06-09",
}

# should be different from nonexistent user cpf
mismatched_nonexistent_user_cpf = "446.153.595-94"
nonexistent_user = {
    "firstName": "Nonexistent",
    "lastName": "User",
    "cpf": "857.545.040-98",
    "email": "nonexistent@test.com",
    "birthDate": "1980-04-04",
}
