from django.http import HttpResponse
from .models import Session, GisPolygon


def index(request):
    with Session() as session:
        result = session.query(GisPolygon).all()
        for row in result:
            print(row)
    return HttpResponse("List of all polygons")
