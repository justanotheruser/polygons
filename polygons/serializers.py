import datetime
from geoalchemy2.shape import from_shape, to_shape
from rest_framework import serializers
import shapely
from .models import GisPolygon


class GeometryField(serializers.Field):
    """
    Geomerty objects are serialized into shapely notation with CRS.
    """

    def to_internal_value(self, data):
        print('to_internal_value', data)
        polygon = shapely.wkt.loads(data['polygon'])
        # if 'crs' in data and data['crs']
        return from_shape(polygon)


class GeometryFieldEPSG4326(GeometryField):
    """
    Geomerty objects are serialized into shapely notation with CRS.
    """

    def to_representation(self, value):
        polygon = to_shape(value)
        data = {'polygon': str(polygon), 'crs': 'EPSG:4326'}
        return data


class GisPolygonSerializer(serializers.Serializer):
    _created = serializers.DateTimeField(read_only=True)
    _updated = serializers.DateTimeField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    class_id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=200)
    props = serializers.JSONField(required=False)

    def create(self, validated_data):
        now = datetime.datetime.utcnow()
        return GisPolygon(_created=now, _updated=now, **validated_data)

    def update(self, instance, validated_data):
        instance._updated = datetime.datetime.utcnow()
        instance.class_id = validated_data.get('class_id', instance.class_id)
        instance.name = validated_data.get('name', instance.name)
        instance.props = validated_data.get('props', instance.props)
        return instance


class GisPolygonSerializerEPSG4326(GisPolygonSerializer):
    geom = GeometryFieldEPSG4326(required=False)
