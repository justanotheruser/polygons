from django.test import TestCase
from django.urls import reverse
from .models import Session, GisPolygon


class PolygonIndexViewTest(TestCase):
    def setUp(self):
        with Session() as session:
            with session.begin():
                session.query(GisPolygon).delete()

    def test_no_polygons(self):
        response = self.client.get(reverse('polygons:index'))
        self.assertContains(
            response, 'No polygons are available', status_code=200)

    def test_some_polygons(self):
        lake = GisPolygon(name='Lake')
        field = GisPolygon(name='Field')
        with Session() as session:
            with session.begin():
                session.add_all([lake, field])
        response = self.client.get(reverse('polygons:index'))
        self.assertContains(response, 'Lake')
        self.assertContains(response, 'Field')
