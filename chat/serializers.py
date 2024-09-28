from rest_framework import serializers
from .models import Newsletter, CustomUser


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Newsletter
        fields = ['id', 'title', 'content']



