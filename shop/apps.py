from django.apps import AppConfig


class ShopConfig(AppConfig):
    name = 'shop'

def ready(self):
    from jobs import updater
    updater.start()