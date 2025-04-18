from django.shortcuts import render,redirect





def homepage(request):
    return render(request, 'homepage.html')