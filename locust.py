#!/usr/bin/env python

from locust import HttpUser, task


class ApiUser(HttpUser):
    @task
    def get_users(self):
        self.client.get("/users")

    @task
    def get_user(self):
        cpf = "218.254.539-50"
        self.client.get("/users/" + cpf)
