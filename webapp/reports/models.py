from django.db import models


class Reports(models.Model):
    class Meta:
        permissions = [
            ("view_sales_report", "Может просматривать отчет по продажам"),
            ("view_events_report", "Может просматривать отчет по сеансам"),
            ("view_tickets_report", "Может просматривать отчет реестр билетов"),
        ]
