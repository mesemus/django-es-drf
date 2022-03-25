# Django ES DRF

**Work in progress**

A simple integration layer between Django, Elasticsearch and Django rest framework

- [Django ES DRF](#django-es-drf)
    - [Model and ES Document example](#model-and-es-document-example)
    - [DRF example](#drf-example)
        - [Returned fields from listing](#returned-fields-from-listing)
        - [Search, facets](#search-facets)
            - [Search via "q" GET parameters](#search-via-q-get-parameters)
                - [Simple search](#simple-search)
                - [Luqum search](#luqum-search)
            - [Facets and faceted filtering](#facets-and-faceted-filtering)
    - [Django Document and mapping](#django-document-and-mapping)
        - [Custom declaration for fields](#custom-declaration-for-fields)
        - [Excluding fields](#excluding-fields)
        - [Custom mapping between serializer fields and ES fields](#custom-mapping-between-serializer-fields-and-es-fields)
        - [Disabling the mapping](#disabling-the-mapping)
        - [Relations](#relations)
    - [Serializer](#serializer)
    - [Objects and nested](#objects-and-nested)

## Model and ES Document example

To declare a document, create a model and register it with a subclass of DjangoDocument. You do not need to declare any
fields on the document - they are generated automatically.

```python
from django.db import models
from django_es_drf import registry, DjangoDocument


class School(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()


@registry.register(School)
class SchoolDocument(DjangoDocument):
    class Index:
        name = "schools"
```

If you want to split the file into models and documents, be free to do so but ensure that the file including documents
is loaded at the startup - in app's ready function, imported at the bottom of the model etc.

Later on, use `SchoolDocument` (which is a subclass of elasticsearch-dsl document):

```python
s = SchoolDocument(name='Blah', address='somewhere')
s.save()

for s in SchoolDocument.search().filter('term', name='Blah'):
    print(s)
    s.name = s.name + '-test'
    s.save()  # will save django and index to ES
```

You can work with django objects if you prefer - they will get persisted into Elastic whenever they are saved:

```python
s = School.objects.create(name='blah', address='somewhere')
# it was persisted, see:
doc = SchoolDocument.get(s.id)
print(doc.name)
```

You can switch between django and document representations:

```python
django_school = School.objects.get(pk=1)

document_school = SchoolDocument.from_django(django_school)

django_again = document_school.to_django()

# they are not the same instances though
assert django_school is not django_again
```

## DRF example

ESViewSet is inherited from `ModelViewSet`, so feel free to use any of its features. You have to remember that
`get_object` will give you DSL Document, not an instance of model.

In the viewset, specify a document, not a model/queryset.

```python
from django_es_drf import ESViewSet


class SchoolAPI(ESViewSet):
    document = SchoolDocument
```

If you need to pre-filter the initial queryset, override the `get_queryset`, call the parent and add your own initial
filter:

```python
from django_es_drf import ESViewSet


class SchoolAPI(ESViewSet):
    document = SchoolDocument

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter('term', cooperating=True)
```

### Returned fields from listing

A `DynamicSourceFilter` is added automatically to filters and can be used to filter the properties returned in listings.

You can specify the props returned on the viewset:

```python
class SchoolAPI(ESViewSet):
    document = SchoolDocument
    source = ['id', 'name']
```

or alternatively, use `_include` or `_exclude` GET parameters containing a list of fields separated by commas
(if `source` is set, they are active only on the fields from the source, otherwise from all fields)

The filter is only used for listing and listing-like operations (that is those where object id is not present in the
URL). If you want to restrict the filter only on some calls, add a `is_dynamic_source_filtering_enabled(self, request)`
method on the viewset class.

Example:

```
GET /schools/?_exclude=address
```

### Search, facets

DRF filter backends (that is `filter_backends` property on viewset) are used for both aggregations and search.

#### Search via "q" GET parameters

Implicitly `filter_backends` contain `QueryFilterBackend` that parses and interprets `q` and `parser` GET parameters:

* the `parser` parameter contains name of the query interpreter that will be used. The interpreters are registered on '
  ESViewSet.query_interpreters' dictionary which defaults
  to ``{"simple": simple_query_interpreter, "luqum": luqum_query_interpreter}``. If the parameter is not passed,
  ESViewSet.default_query_interpreter is used. If invalid value is passed, empty result list is returned.
* `q` parameter is passed to the interpreter which applies it to a queryset

##### Simple search

The simple interpreter performs `multi_match` operation on all fields.

##### Luqum search

This search interpreter takes the content of the query and interprets it as a luqum query string. This library enables
use of `nested` mapping in query and supports boolean operators.
See [https://luqum.readthedocs.io/en/latest/about.html](https://luqum.readthedocs.io/en/latest/about.html)
for details on the language/capabilities.

#### Facets and faceted filtering

To enable aggregations and filtering by bucket values, add `aggs` to the viewset class. Example:

```python
from django_es_drf import ESViewSet, BucketAgg


class SchoolAPI(ESViewSet):
    document = SchoolDocument
    aggs = [
        BucketAgg("name"),
        BucketAgg("address")
    ]
```

You can use the following aggregations:

* `BucketAgg(name, field=None, type='terms')` - a terms bucket filtering. If field is not set, it is the same as `name`.
  Dot notation in the `field` is supported.
* `NestedAgg(name, path, filter)` - generates a nested aggregation
* `TranslatedBucketAgg(name, type="terms", field=None, map=None)` - translates the bucket keys through a map to get
  human labels

The aggregations are chainable. Chaining `BucketAgg` does not mean nesting - the aggregations are on the same level.

Bigger Example:

```python
aggs = [
    TranslatedBucketAgg('available', label='Available', map={
        True: 'yes',
        False: 'no'
    }),
    NestedAgg("tagsWithYear")
        .bucket("tagsWithYear.tag", label="Tag")
        .bucket("tagsWithYear.year", label="Year"),
]
```

Any options not interpreted by ES (in this case 'label') are copied into the API output (and might be used, for example,
in UI renderer).

Sample returned value (aggs = `aggs = [BucketAgg("name"), BucketAgg("address")]`):

```json
{
  "aggs": [
    {
      "code": "name",
      "__missing__": 0,
      "__count__": 2,
      "doc_count_error_upper_bound": 0,
      "sum_other_doc_count": 0,
      "buckets": [
        {
          "key": "test 1",
          "doc_count": 1
        },
        {
          "key": "test 2",
          "doc_count": 1
        }
      ]
    },
    {
      "code": "address",
      "__missing__": 0,
      "__count__": 2,
      "doc_count_error_upper_bound": 0,
      "sum_other_doc_count": 0,
      "buckets": [
        {
          "key": "blah",
          "doc_count": 2
        }
      ]
    }
  ],
  ...
}
```

##### Filtering by aggregation buckets

To filter by aggregation buckets, add `?f=<bucket_code>:<value>:<bucket_code>:<value>...` to the url. URLEncode '%'
and ':' if there is ':' in the unlikely case these chars are in the value. If you need a different syntax, define
a `parse_facet_query(self, request)` method on you viewset that returns either None or dictionary with facet code as a
key and a list of values to match as the value.

Example:

```GET /schools/?f=name:test 2```

Response:

```json5
            {
  "count": 1,
  // ...
  "hits": [
    {
      "id": 2,
      "name": "test 2",
      "address": "blah"
    }
  ],
  "aggs": [
    // ...
  ]
}
```

##### Filtering without aggregations

A bucket aggregation can be used just to filter the queryset, not to generate any aggregations. To do so, specify
`display=False` option to the aggregation. The `?f` will still be available, but no aggregations will be generated.

```python
aggs = [
    BucketAgg('available', display=False),
    NestedAgg("tagsWithYear")
        .bucket("tagsWithYear.tag", label="Tag")
        .bucket("tagsWithYear.year", label="Year"),
]
```

## Django Document and mapping

### Custom declaration for fields

Any fields that are already present on the document will be keep as they are. In the example above, to set that
`name` is a `text` and not `keyword` (the default), just declare:

```python
import elasticsearch_dsl as e


@registry.register(School)
class SchoolDocument(DjangoDocument):
    name = e.Text()

    class Index:
        name = "schools"
```

### Excluding fields

To exclude a field from the automatic generation, add it to `excluded`. If "nested/object" mapping will be generated,
you can use a dot-separated path.

```python
@registry.register(School, excluded=['address'])
class SchoolDocument(DjangoDocument):
    class Index:
        name = "schools"
```

### Custom mapping between serializer fields and ES fields

Add your own mapping - the key is the DRF field type, value is a function that takes the field and context and returns
ES field:
The context is an instance of `RegistrationContext`.

```python
import elasticsearch_dsl as e
import rest_framework.serializers as s


@registry.register(School,
                   mapping={
                       s.CharField: lambda fld, ctx, **kwargs: e.Keyword()
                   })
class SchoolDocument(DjangoDocument):
    class Index:
        name = "schools"
```

### Disabling the mapping

Add `generate=False` to decorator's parameters:

```python
import elasticsearch_dsl as e


@registry.register(School,
                   generate=False)
class SchoolDocument(DjangoDocument):
    # you need to provide your own mapping here

    class Index:
        name = "schools"
```

### Relations

The framework has a rudimentary support for read-only relations. If there is an M2M or ForeignKey on model and
serializer uses target's serializer to embed the representation of the relation target, the document will contain an
object mapping for the target's data. It can be changed to Nested via mapping parameter in Document's registration
decorator.

The framework does not provide any support for propagating changes on related models. If you need this, write your own
change listeners or use a more complete library, such as django-elasticsearch-dsl-drf.

A simple example with a foreign key:

```python
class City(models.Model):
    name = models.CharField(max_length=100)


class School(models.Model):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, related_name="+", on_delete=models.CASCADE)


@registry.register(School, serializer_meta={"depth": 1})
class SchoolDocument(DjangoDocument):
    class Index:
        name = "schools"
```

*Note:* the `depth` in `serializer_meta` argument - it instructs the generated model serializer to create a serializer
for city as well. This is roughly equivalent to the following code:

```python
from rest_framework import serializers


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        exclude = ()


class SchoolSerializer(serializers.ModelSerializer):
    city = CitySerializer()

    class Meta:
        model = School
        exclude = ()


@registry.register(School, serializer=SchoolSerializer)
class SchoolDocument(DjangoDocument):
    class Index:
        name = "schools"
```

If you want to change the type to nested:

```python
import elasticsearch_dsl as e


@registry.register(School, serializer_meta={"depth": 1}, mapping={
    'city': e.Nested
})
class SchoolDocument(DjangoDocument):
    class Index:
        name = "schools"

```

*Note:* There is no support for creating nested objects. If you need this support, you'll have to write your
own `create`/`update` method on the serializer.

## Serializer

Optionally you might want to provide your own serializer, to transform/generate additional fields into the document.

The serializer is just a plain DRF serializer that converts django fields to document's fields, there is nothing fancy
about it.

*Note:* If you use `SerializerMethodField`, be sure to add the correct field into the mapping:

```python
from rest_framework import serializers


class SchoolSerializer(serializers.ModelSerializer):
    name_with_address = serializers.SerializerMethodField()

    def get_name_with_address(self, instance):
        return f"{instance.name}, {instance.address}"

    class Meta:
        model = School
        exclude = ()


@registry.register(School, serializer=SchoolSerializer, mapping={
    'name_with_address': e.Text
})
class SchoolDocument(DjangoDocument):
    class Index:
        name = "schools"
```
