from django.apps import AppConfig

class PaymentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Payment'

    # Yeh function Django ko batayega ki models 'model' folder ke andar hain
    def ready(self):
        import Payment.model