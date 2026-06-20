from django.urls import path
from Payment.view.payment_easebuzz import easebuzz_payment_callback, generate_easebuzz_link
from Payment.view.payment_payu import generate_payment_link, payu_payment_callback
from Payment.view.test_data import loan_details_test

urlpatterns = [
    path('payu_payment/', generate_payment_link, name='initiate-payment'),
    path('payment/success/', payu_payment_callback, name='payment-success'),
    path('payment/failure/', payu_payment_callback, name='payment-failure'),
    path('easebuzz_payment/', generate_easebuzz_link, name='easebuzz-initiate'),
    path('easebuzz_callback/', easebuzz_payment_callback, name='easebuzz-callback'),
    path('loan_details/', loan_details_test, name='loan-details-test'),
]
