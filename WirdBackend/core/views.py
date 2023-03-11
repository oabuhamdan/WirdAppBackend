from rest_framework import viewsets, mixins, permissions

from core import models_helper
from core.my_view import MyModelViewSet
from core.serializers import *


class ContestView(MyModelViewSet):
    serializer_class = ContestSerializer
    name = 'create-contest-view'
    member_allowed_methods = ['retrieve', 'list']
    admin_allowed_methods = ['retrieve', 'list']
    super_admin_allowed_methods = ['retrieve', 'list', 'update', 'partial_update']

    def get_queryset(self):
        username = util.get_username_from_session(self.request)
        return models_helper.get_person_contests_queryset(username)


class SignUpView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        user_type = self.request.query_params.get("type", "participant")
        if user_type == "participant":
            return ParticipantSignupSerializer
        elif user_type == "creator":
            return CreatorSignupSerializer
