import io
from rest_framework.parsers import JSONParser
import json
from django.http import HttpResponse, Http404
from django.shortcuts import render
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Session, GisPolygon, loads_polygon
from .serializers import GisPolygonSerializer


class IndexView(APIView):
    def get(self, request):
        with Session() as session:
            polygon_list = session.query(GisPolygon).all()
            context = {'polygon_list': polygon_list}
            return render(request, 'polygons/index.html', context)

    def post(self, request):
        print(request.body)
        stream = io.BytesIO(request.body)
        data = JSONParser().parse(stream)
        print(data)
        serializer = GisPolygonSerializer(data=data)
        if not serializer.is_valid():
            return HttpResponse("Bad request", status_code=400)
        polygon = serializer.save()
        with Session() as session:
            with session.begin():
                session.add(polygon)
            return Response({'id': polygon.id}, status=status.HTTP_201_CREATED)


class DetailView(APIView):
    def get(self, request, polygon_id):
        with Session() as session:
            polygon = session.query(GisPolygon).filter_by(
                id=polygon_id).first()
            if polygon is None:
                raise Http404("Polygon does not exist")
            serializer = GisPolygonSerializer(polygon)
            print(serializer.data)
            polygon_json = JSONRenderer().render(serializer.data)
            return HttpResponse(polygon_json)
