import datetime
import json
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
import shapely
from .models import Session, GisPolygon


class PolygonIndexViewTest(TestCase):
    def setUp(self):
        with Session() as session:
            with session.begin():
                session.query(GisPolygon).delete()

    def test_no_polygons(self):
        response = self.client.get(reverse('polygons:index'))
        self.assertContains(
            response, 'No polygons are available',
            status_code=status.HTTP_200_OK)

    def test_some_polygons(self):
        lake = GisPolygon(name='Lake')
        field = GisPolygon(name='Field')
        with Session() as session:
            with session.begin():
                session.add_all([lake, field])
        response = self.client.get(reverse('polygons:index'))
        self.assertContains(response, 'Lake')
        self.assertContains(response, 'Field')


class PolygonDetailViewTest(TestCase):
    def setUp(self):
        with Session() as session:
            with session.begin():
                session.query(GisPolygon).delete()

    def test_create_polygon(self):
        polygon = {'name': 'Lake', 'class_id': 1, 'props': {'prop1': 'value1'},
                   'geom': {'polygon': 'POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))',
                            'crs': 'EPSG:4326'}}
        response = self.client.post(reverse('polygons:index'),
                                    content_type='application/json',
                                    data=polygon)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_content = json.loads(response.content)
        url = reverse('polygons:detail', kwargs={
                      'polygon_id': post_content['id']})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        assert content['_created'] is not None
        assert content['_updated'] is not None
        self.assertEqual(content['id'],  post_content['id'])
        self.assertEqual(content['name'], polygon['name'])
        self.assertEqual(content['class_id'], polygon['class_id'])
        self.assertEqual(content['props'], polygon['props'])
        self.assertEqual(content['geom'], polygon['geom'])

    def test_trying_to_set_id(self):
        # Just in case real generated id will be the same
        # we will use 2 non-consecutive ids
        polygon_one = {'name': 'Lake', 'id': 42}
        response_one = self.client.post(reverse('polygons:index'),
                                        content_type='application/json',
                                        data=polygon_one)
        self.assertEqual(response_one.status_code, status.HTTP_201_CREATED)
        polygon_two = {'name': 'Field', 'id': 41}
        response_two = self.client.post(reverse('polygons:index'),
                                        content_type='application/json',
                                        data=polygon_two)
        self.assertEqual(response_two.status_code, status.HTTP_201_CREATED)
        content_one = json.loads(response_one.content)
        content_two = json.loads(response_two.content)
        assert content_one['id'] != polygon_one['id'] or \
            content_two['id'] != polygon_two['id']

    def test_trying_to_set_created_and_updated(self):
        future_time = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        polygon = {'name': 'Lake', '_created': str(
            future_time), '_updated': str(future_time)}
        response = self.client.post(reverse('polygons:index'),
                                    content_type='application/json',
                                    data=polygon)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_content = json.loads(response.content)
        url = reverse('polygons:detail', kwargs={
                      'polygon_id': post_content['id']})
        response = self.client.get(url)
        content = json.loads(response.content)
        self.assertNotEqual(content['_created'], str(future_time))
        self.assertNotEqual(content['_updated'], str(future_time))

    def test_class_id_geom_and_props_are_optional(self):
        polygon = {'name': 'Field'}
        response = self.client.post(reverse('polygons:index'),
                                    content_type='application/json',
                                    data=polygon)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_content = json.loads(response.content)
        url = reverse('polygons:detail', kwargs={
                      'polygon_id': post_content['id']})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_name_is_required(self):
        polygon = {'geom': {'polygon': 'POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))'}}
        response = self.client.post(reverse('polygons:index'),
                                    content_type='application/json',
                                    data=polygon)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        post_content = json.loads(response.content)
        self.assertEqual(post_content, {'name': ['This field is required.']})

    def test_polygon_not_found(self):
        url = reverse('polygons:detail', kwargs={'polygon_id': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_default_crs_is_epsg_4326(self):
        polygon = {'name': 'Lake',
                   'geom': {'polygon': 'POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))'}}
        response = self.client.post(reverse('polygons:index'),
                                    content_type='application/json',
                                    data=polygon)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_content = json.loads(response.content)
        url = reverse('polygons:detail', kwargs={
                      'polygon_id': post_content['id']})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['geom']['polygon'],
                         polygon['geom']['polygon'])
        self.assertEqual(content['geom']['crs'], 'EPSG:4326')

    def test_post_and_get_polygon_with_crs_epsg_32644(self):
        post_polygon_str = 'POLYGON ((0.5 0.5, 1 0.5, 1 1, 0.5 1, 0.5 0.5))'
        polygon_data = {'name': 'Lake',
                        'geom': {'polygon': post_polygon_str,
                                 'crs': 'EPSG:32644'}}
        response = self.client.post(reverse('polygons:index'),
                                    content_type='application/json',
                                    data=polygon_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_content = json.loads(response.content)
        url = reverse('polygons:detail', kwargs={
                      'polygon_id': post_content['id']})
        response = self.client.get(url, {'crs': 'epsg32644'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that shape didn't change in any signigicant way after
        # transformation to and from CRS used by DB
        post_polygon = shapely.wkt.loads(post_polygon_str)
        content = json.loads(response.content)
        get_polygon = shapely.wkt.loads(content['geom']['polygon'])
        assert post_polygon.almost_equals(get_polygon)

    def test_post_polygon_with_unknown_crs(self):
        polygon_data = {'name': 'Lake',
                        'geom': {'polygon': 'POLYGON ((0.5 0.5, 1 0.5, 1 1, 0.5 1, 0.5 0.5))',
                                 'crs': 'EPSG:1111'}}
        response = self.client.post(reverse('polygons:index'),
                                    content_type='application/json',
                                    data=polygon_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        post_content = json.loads(response.content)
        self.assertEqual(
            post_content, {'geom': ['Incorrect CRS value EPSG:1111']})

    def test_get_polygon_with_unknown_crs(self):
        polygon_data = {'name': 'Lake'}
        response = self.client.post(reverse('polygons:index'),
                                    content_type='application/json',
                                    data=polygon_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post_content = json.loads(response.content)
        url = reverse('polygons:detail', kwargs={
                      'polygon_id': post_content['id']})
        response = self.client.get(url, {'crs': 'epsg1111'})
        content = json.loads(response.content)
        self.assertEqual(content, 'Incorrect CRS value epsg1111')

    def test_update_polygon(self):
        polygon = {'name': 'Lake', 'class_id': 1, 'props': {'prop1': 'value1'},
                   'geom': {'polygon': 'POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0))'}}
        response = self.client.post(reverse('polygons:index'),
                                    content_type='application/json',
                                    data=polygon)
        post_content = json.loads(response.content)
        url = reverse('polygons:detail', kwargs={
                      'polygon_id': post_content['id']})
        response = self.client.get(url)
        original_content = json.loads(response.content)

        patch = {'name': 'Baikal', 'class_id': 2, 'props': {'prop2': 'value2'},
                 'geom': {'polygon': 'POLYGON ((0 0, 2 0, 2 2, 0 2, 0 0))'}}
        response = self.client.patch(
            url, content_type='application/json', data=patch)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(url)
        patched_content = json.loads(response.content)

        self.assertEqual(
            original_content['_created'], patched_content['_created'])
        self.assertNotEqual(
            original_content['_updated'], patched_content['_updated'])
        self.assertEqual(patched_content['name'], patch['name'])
        self.assertEqual(patched_content['class_id'], patch['class_id'])
        self.assertEqual(patched_content['props'], patch['props'])
        self.assertEqual(patched_content['geom']
                         ['polygon'], patch['geom']['polygon'])

    def test_delete_polygon(self):
        polygon = {'name': 'Lake'}
        response = self.client.post(reverse('polygons:index'),
                                    content_type='application/json',
                                    data=polygon)
        post_content = json.loads(response.content)
        url = reverse('polygons:detail', kwargs={
                      'polygon_id': post_content['id']})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
