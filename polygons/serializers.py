import datetime
from geoalchemy2.shape import from_shape, to_shape
from rest_framework import serializers
import shapely
from shapely.ops import transform
import pyproj
from .models import GisPolygon


class GeometryField(serializers.Field):
    """
    Geomerty objects are serialized from shapely notation with CRS.
    """
    db_crs = 'EPSG:4326'
    supported_crs_to_internal = ['EPSG:32644']    

    def to_internal_value(self, data):
        print('to_internal_value', data)
        polygon = shapely.wkt.loads(data['polygon'])
        if 'crs' in data and data['crs'] != GeometryField.db_crs:
            if data['crs'] in GeometryField.supported_crs_to_internal:
                from_crs = pyproj.CRS(data['crs'])
                to_crs = pyproj.CRS(GeometryField.db_crs)
                project = pyproj.Transformer.from_crs(from_crs, to_crs, always_xy=True).transform
                polygon = transform(project, polygon)
            else:
                msg = 'Incorrect CRS value %s'
                raise serializers.ValidationError(msg % data['crs']) 
        return from_shape(polygon)


class GeometryFieldEPSG_4326(GeometryField):
    def to_representation(self, value):
        polygon = to_shape(value)
        data = {'polygon': str(polygon), 'crs': 'EPSG:4326'}
        return data


class GeometryFieldEPSG_32644(GeometryField):
    def to_representation(self, value):
        polygon = to_shape(value)
        from_crs =  pyproj.CRS(GeometryField.db_crs)
        to_crs = 'EPSG:32644'
        project = pyproj.Transformer.from_crs(from_crs, pyproj.CRS(to_crs), always_xy=True).transform
        polygon = transform(project, polygon)
        data = {'polygon': str(polygon), 'crs': to_crs}
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


class GisPolygonSerializerEPSG_4326(GisPolygonSerializer):
    geom = GeometryFieldEPSG_4326(required=False)


class GisPolygonSerializerEPSG_32644(GisPolygonSerializer):
    geom = GeometryFieldEPSG_32644(required=False)
