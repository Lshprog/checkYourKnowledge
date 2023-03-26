from django.shortcuts import render
from django.utils.safestring import mark_safe
import json
from django.contrib.auth.decorators import login_required

def home(request):
    return render(request, 'home.html', {})


@login_required
def room(request, room_name):
    return render(request, 'chatroom.html', {
        'room_name': room_name,
        'username': mark_safe(json.dumps(request.user.username)),

    })