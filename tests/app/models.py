from django.db import models
from rest_framework import serializers

from django_es_drf import registry, DjangoDocument
import elasticsearch_dsl as e


class School(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(null=True, blank=True)


class SchoolWithNameAsText(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()


class City(models.Model):
    name = models.CharField(max_length=100)


class SchoolWithForeign(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, related_name="+", on_delete=models.CASCADE)


class Person(models.Model):
    name = models.CharField(max_length=100)


class SchoolWithM2M(models.Model):
    name = models.CharField(max_length=100)
    people = models.ManyToManyField(Person, related_name="+")


class SchoolForSerializerGenerator(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    int_fld = models.IntegerField(null=True, blank=True)
    float_fld = models.FloatField(null=True, blank=True)
    bool_fld = models.BooleanField(null=True, blank=True)


@registry.register(School)
class SchoolDocument(DjangoDocument):
    class Index:
        name = "tests-schools"


@registry.register(SchoolWithNameAsText, mapping={"name": e.Text})
class SchoolWithNameAsTextDocument(DjangoDocument):
    class Index:
        name = "tests-schools-name-as-text"


@registry.register(SchoolWithForeign, serializer_meta={"depth": 1})
class SchoolWithForeignDocument(DjangoDocument):
    class Index:
        name = "tests-schools-with-foreign"


@registry.register(SchoolWithM2M, serializer_meta={"depth": 1})
class SchoolWithM2MDocument(DjangoDocument):
    class Index:
        name = "tests-schools-with-m2m"


class SchoolWithSerializer(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()


class SchoolSerializer(serializers.ModelSerializer):
    name_with_address = serializers.SerializerMethodField()

    def get_name_with_address(self, instance):
        return f"{instance.name}, {instance.address}"

    class Meta:
        model = SchoolWithSerializer
        exclude = ()


@registry.register(
    SchoolWithSerializer,
    serializer=SchoolSerializer,
    mapping={"name_with_address": e.Text},
)
class SchoolWithSerializerDocument(DjangoDocument):
    class Index:
        name = "tests-schools-serializer"


# do not use model serializer here as we want to generate fields from the document
class EmptySerializer(serializers.Serializer):
    def create(self, validated_data):
        return SchoolForSerializerGenerator.objects.create(**validated_data)


@registry.register(SchoolForSerializerGenerator, serializer=EmptySerializer)
class SchoolForSerializerGeneratorDocument(DjangoDocument):
    name = e.Keyword()
    int_fld = e.Integer()
    float_fld = e.Float()
    bool_fld = e.Boolean()

    class Index:
        name = "tests-schools-serializer-generator"
