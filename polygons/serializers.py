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
    DB_CRS = 'EPSG:4326'
    SUPPORTED_CRS = ['EPSG:4326', 'EPSG:32644']

    def to_internal_value(self, data):
        polygon = shapely.wkt.loads(data['polygon'])
        if 'crs' in data:
            from_crs = data['crs'].upper()
            if from_crs != GeometryField.DB_CRS:
                if from_crs in GeometryField.SUPPORTED_CRS:
                    from_crs = pyproj.CRS(from_crs)
                    to_crs = pyproj.CRS(GeometryField.DB_CRS)
                    project = pyproj.Transformer.from_crs(
                        from_crs, to_crs, always_xy=True).transform
                    polygon = transform(project, polygon)
                else:
                    msg = 'Incorrect CRS value %s'
                    raise serializers.ValidationError(msg % data['crs'])
        return from_shape(polygon)

    def to_representation(self, value):
        polygon = to_shape(value)
        to_crs = self.context['crs'].upper()
        if to_crs != GeometryField.DB_CRS:
            if to_crs in GeometryField.SUPPORTED_CRS:
                from_crs = pyproj.CRS(GeometryField.DB_CRS)
                project = pyproj.Transformer.from_crs(
                    from_crs, pyproj.CRS(to_crs), always_xy=True).transform
                polygon = transform(project, polygon)
            else:
                msg = 'Incorrect CRS value %s'
                raise serializers.ValidationError(msg % self.context['crs'])
        data = {'polygon': str(polygon), 'crs': 'EPSG:4326'}
        return data


class GisPolygonSerializer(serializers.Serializer):
    _created = serializers.DateTimeField(
        read_only=True, format='%Y-%m-%d %H:%M:%S.%f')
    _updated = serializers.DateTimeField(
        read_only=True, format='%Y-%m-%d %H:%M:%S.%f')
    id = serializers.IntegerField(read_only=True)
    class_id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=65535)
    props = serializers.JSONField(required=False)
    geom = GeometryField(required=False)

    def create(self, validated_data):
        now = datetime.datetime.utcnow()
        return GisPolygon(_created=now, _updated=now, **validated_data)

    def update(self, instance, validated_data):
        instance._updated = datetime.datetime.utcnow()
        instance.class_id = validated_data.get('class_id', instance.class_id)
        instance.name = validated_data.get('name', instance.name)
        instance.props = validated_data.get('props', instance.props)
        instance.geom = validated_data.get('geom', instance.geom)
        return instance
