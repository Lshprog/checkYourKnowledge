from django.contrib.auth import get_user_model
from django.db import models
User = get_user_model()


class Message(models.Model):
    author = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    def last_10_messages(self):
        return Message.objects.order_by('-timestamp').all()[:10]

class Task_model(models.Model):
    author = models.ForeignKey(User,  on_delete=models.CASCADE)
    content_problem = models.TextField()
    content_answear = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    # Id = models.TextField()


class Classroom(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    join_code = models.TextField()
    token = models.TextField()


class ClassroomUserList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    classroom_id = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    role = models.TextField()

