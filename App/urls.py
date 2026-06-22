from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib import admin
from django.urls import path, include

class TestAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "status": "success",
            "message": "Payment Project is working ✅"
        })
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/test/', TestAPIView.as_view(), name='test-api'),
    path('api/', include('Payment.urls')), 
]