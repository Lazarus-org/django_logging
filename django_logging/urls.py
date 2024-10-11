from django.urls import path

from django_logging.utils.get_conf import include_log_iboard
from django_logging.views.log_iboard import LogiBoardView

urlpatterns = []

if include_log_iboard():
    urlpatterns.append(path("log-iboard/", LogiBoardView.as_view(), name="log-iboard"))
