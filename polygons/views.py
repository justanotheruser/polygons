import io
from rest_framework.parsers import JSONParser
import json
from django.http import HttpResponse, Http404
from django.shortcuts import render
from rest_framework import status, serializers
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Session, GisPolygon
from .serializers import GisPolygonSerializer


class IndexView(APIView):
    def get(self, request):
        with Session() as session:
            polygon_list = session.query(GisPolygon).all()
            context = {'polygon_list': polygon_list}
            return render(request, 'polygons/index.html', context)

    def post(self, request):
        stream = io.BytesIO(request.body)
        data = JSONParser().parse(stream)
        serializer = GisPolygonSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        polygon = serializer.save()
        with Session() as session:
            with session.begin():
                session.add(polygon)
            return Response({'id': polygon.id}, status=status.HTTP_201_CREATED)


DEFAULT_CRS = 'epsg:4326'


class DetailView(APIView):
    def get(self, request, polygon_id):
        with Session() as session:
            polygon = session.query(GisPolygon).filter_by(
                id=polygon_id).first()
            if polygon is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
            crs = request.query_params.get('crs', DEFAULT_CRS)
            try:
                serializer = GisPolygonSerializer(polygon, context={'crs': crs})
                polygon_json = JSONRenderer().render(serializer.data)
            except serializers.ValidationError as e:
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            return HttpResponse(polygon_json, status=status.HTTP_200_OK)

    def patch(self, request, polygon_id):
        with Session() as session:
            with session.begin():
                existing_polygon = session.query(GisPolygon).filter_by(
                    id=polygon_id).first()
                if existing_polygon is None:
                    return Response(status=status.HTTP_404_NOT_FOUND)
                stream = io.BytesIO(request.body)
                data = JSONParser().parse(stream)
                serializer = GisPolygonSerializer(
                    existing_polygon, data=data, partial=True)
                if not serializer.is_valid():
                    return Response(serializer.errors,
                                    status=status.HTTP_400_BAD_REQUEST)
                polygon = serializer.save()
                session.add(polygon)
            return Response(status=status.HTTP_200_OK)

    def delete(self, request, polygon_id):
        with Session() as session:
            with session.begin():
                polygon = session.get(GisPolygon, polygon_id)
                if not polygon:
                    return Response(status=status.HTTP_404_NOT_FOUND)
                session.delete(polygon)
            return Response(status=status.HTTP_200_OK)
