from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import auth, messages


# Create your views here.


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            messages.success(request, 'Ви успішно зайшли до системи')
            return redirect('home')
        else:
            messages.error(request, 'Неправильні авторизаційні дані')
    return render(request, 'accounts/login.html')



def logout(request):
    auth.logout(request)
    messages.success(request, 'Ви вийшли з аккаунту')
    return redirect('login')



