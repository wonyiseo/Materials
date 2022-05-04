import img_convert.views
from django.conf.urls import url

urlpatterns = [
    url("image/" , view=img_convert.views.image_upload_view)
]
