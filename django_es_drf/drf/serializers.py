from rest_framework.serializers import BaseSerializer


class CopyESSerializer(BaseSerializer):
    def to_internal_value(self, data):
        return data

    def to_representation(self, instance):
        return instance
