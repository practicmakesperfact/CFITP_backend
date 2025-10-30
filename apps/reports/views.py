from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import ReportSerializer
from .models import Report
from .services import ReportService
from rest_framework.permissions import IsAuthenticated
from apps.users.permissions import IsStaffOrManager

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsStaffOrManager]

    def perform_create(self, serializer):
        report_type = self.request.data.get('type')
        report = ReportService.request_report(self.request.user, report_type)
        serializer.instance = report

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)