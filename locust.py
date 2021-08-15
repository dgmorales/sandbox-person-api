#!/usr/bin/env python

from locust import HttpUser, task


class ApiUser(HttpUser):
    @task
    def get_users(self):
        self.client.get("/users")

    @task
    def get_user(self):
        cpf = "857.545.040-98"
        self.client.get("/users/" + cpf)
