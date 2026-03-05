from rest_framework import serializers


class SyncSerializer(serializers.Serializer):
    pid       = serializers.IntegerField()
    milestone = serializers.CharField()
    date      = serializers.DateField()
