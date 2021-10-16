import datetime
from rest_framework import serializers
from .models import GisPolygon


class GisPolygonSerializer(serializers.Serializer):
    #geom = Column(Geometry('POLYGON', srid=4326))
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
