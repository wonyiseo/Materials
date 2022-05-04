import django.core.files.uploadedfile
import img_convert
import img_convert.models
from QueueServer import redisqueue
from django.shortcuts import render

from .forms import ImageForm

QUEUE_NAME = "queue1"
WORKER_NAME = "queue1"
QUEUE_PASS = "queue1234"
SERVER_IP = "13.209.88.71"
SERVER_PORT = 6379
DB = 0

Q_MAX_SIZE = 1000000

q = redisqueue.RedisQueuePutter(event_q_name=QUEUE_NAME , q_max_size=Q_MAX_SIZE , host=SERVER_IP , port=SERVER_PORT , db=DB)


def image_upload_view(request):
    """Process images uploaded by users"""
    if request.method == 'POST':
        form: img_convert.forms.ImageForm = ImageForm(request.POST , request.FILES)
        if form.is_valid():
            img: django.core.files.uploadedfile.InMemoryUploadedFile = request.FILES["image"]
            if img.readable():
                data = img.read()
                try:
                    form.save()
                except Exception as ex:
                    pass

                path = form.instance.image.url[1:]
                # q.enqueue(handle, img)
                q.put(element=data)

            # Get the current instance object to display in the template
            img_obj: img_convert.models.Image = form.instance
            return render(request , 'index.html' , {'form': form , 'img_obj': img_obj})
    else:
        form = ImageForm()
    return render(request , 'index.html' , {'form': form})
