from rest_framework.renderers import JSONRenderer

from django_es_drf.json import ESEncoderClass


class ESRenderer(JSONRenderer):
    encoder_class = ESEncoderClass
