from rest_framework.serializers import BaseSerializer


class CopyESSerializer(BaseSerializer):
    def to_internal_value(self, data):
        return data

    def to_representation(self, instance):
        return instance

    def create(self, validated_data):
        document_class = self.context["view"].document
        # TODO: nested are not supported
        doc = document_class(**validated_data)
        doc.save()
        return doc

    def update(self, instance, validated_data):
        if self.partial:
            for k, v in validated_data.items():
                setattr(instance, k, v)
        else:
            # clear the instance
            doctype = type(instance)
            if doctype.DOCUMENT_ID_FIELD not in validated_data:
                validated_data[doctype.DOCUMENT_ID_FIELD] = instance.meta.id
            instance = doctype(meta={"id": instance.meta.id}, **validated_data)
        instance.save()
        return instance
