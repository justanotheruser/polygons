from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from .models import Session, GisPolygon


class IndexView(APIView):
    def get(self, request):
        with Session() as session:
            polygon_list = session.query(GisPolygon).all()
            context = {'polygon_list': polygon_list}
            return render(request, 'polygons/index.html', context)


class DetailView(APIView):
    def get(self, request, polygon_id):
        return HttpResponse(f'Info about polygon {polygon_id}')
        