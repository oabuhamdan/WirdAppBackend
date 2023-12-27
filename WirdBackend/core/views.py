import datetime
from datetime import datetime, timedelta

from django.core.cache import cache
from django.db.models import Value, Sum, F
from django.db.models.functions import Concat
from django.utils.translation import get_language
from django.utils.translation import gettext
from hijri_converter import Gregorian
from rest_condition import And
from rest_condition import Or
from rest_framework import generics
from rest_framework import status
from rest_framework import views
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from core import models_helper, util_methods
from core.models import ContestPerson
from core.permissions import IsContestMember, IsContestSuperAdmin, IsAuthenticatedAndReadOnly
from core.serializers import *
from core.util_classes import MyModelViewSet
from member_panel.models import PointRecord


class ContestView(MyModelViewSet):
    name = 'create-contest-view'
    authenticated_allowed_methods = ['join_contest', 'list']
    verified_allowed_methods = ['create']
    member_allowed_methods = ['switch_contest', 'list', 'current']
    super_admin_allowed_methods = ["edit_contest"]
    serializer_class = ContestSerializer
    throttle_scope = "contest_view"

    def perform_create(self, serializer):
        contest = serializer.save()
        username = util_methods.get_username_from_session(self.request)
        person = Person.objects.get(username=username)
        ContestPerson.objects.create(person=person, contest=contest, contest_role=0)
        return contest

    @action(detail=False, methods=['post'])
    def switch_contest(self, request):
        if self.get_queryset().filter(id=request.data.get("id", "")).exists():
            request.session["current_contest"] = request.data['contest_id']
            request.session.modified = True
            return Response(gettext("contest switched successfully"), status=status.HTTP_200_OK)
        else:
            return Response(gettext("person is not enrolled in this contest"), status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def join_contest(self, request):
        try:
            contest_id = request.data.get('contest_id', "")
            contest = Contest.objects.get(contest_id=contest_id, readonly_mode=False)
            person_id = Person.objects.get(username=util_methods.get_username_from_session(request)).id
            ContestPerson.objects.get_or_create(person_id=person_id, contest=contest, contest_role=3)
            return Response(gettext("joined the new contest"), 200)
        except Contest.DoesNotExist:
            return Response(gettext("cannot join this contest or access code is wrong"), 400)

    @action(detail=False, methods=["get", "put"], throttle_classes=[UserRateThrottle],
            permission_classes=[Or(IsContestSuperAdmin(), IsAuthenticatedAndReadOnly())])
    def current(self, request):
        contest_id = util_methods.get_current_contest_id_from_session(request)
        instance = Contest.objects.get(id=contest_id)
        return Response(self.get_serializer(instance).data)

    def get_queryset(self):
        username = util_methods.get_username_from_session(self.request)
        return models_helper.get_person_contests(username)

    serializer_fields = dict(
        list=["id", "contest_id", "name", "access_code", "profile_photo"],
        create=["contest_id", "name", "description", "contest_photo", "start_date", "end_date"],
        join_contest=["contest_id"],
        switch_contest=["id"],
    )

    def get_serializer(self, *args, **kwargs):
        return super().get_serializer(*args, fields=self.serializer_fields.get(self.action, None), **kwargs)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        current_user_role = util_methods.get_current_user_role_from_session(request)
        current_contest_id = util_methods.get_current_contest_id_from_session(request)
        data = PersonSerializer(user).data
        data["current_user_role"] = current_user_role
        data["current_contest_id"] = current_contest_id
        return Response(data)

    def get_object(self):
        user = self.request.user
        return user


class TopMembersOverall(views.APIView):
    permission_classes = [And(IsAuthenticated(), IsContestMember()), ]

    def get(self, request, *args, **kwargs):
        contest_id = util_methods.get_current_contest_id_from_session(request)
        results = cache.get(contest_id)
        if not results:
            first_name = "person__person__first_name"
            last_name = "person__person__last_name"
            username = "person__person__username"
            results = PointRecord.objects.filter(person__contest__id=contest_id, person__contest_role__in=[1, 4]) \
                .annotate(username=F(username), name=Concat(first_name, Value(' '), last_name)) \
                .values("username", "person_id", 'name') \
                .annotate(total_points=Sum("point_total")).order_by("-total_points")
            cache.set(contest_id, results, 60 * 10)

        return Response(results)


class TopMembersByDate(views.APIView):
    permission_classes = [And(IsAuthenticated(), IsContestMember()), ]

    def get(self, request, *args, **kwargs):
        contest_id = util_methods.get_current_contest_id_from_session(request)
        date = kwargs["date"]
        key = f"{contest_id}_{date}"
        results = cache.get(key)
        if not results:
            first_name = "person__person__first_name"
            last_name = "person__person__last_name"
            username = "person__person__username"
            results = PointRecord.objects.filter(record_date=date,
                                                 person__contest__id=contest_id,
                                                 person__contest_role__in=[1, 4]) \
                .annotate(username=F(username), name=Concat(first_name, Value(' '), last_name)) \
                .values("username", "person_id", 'name') \
                .annotate(total_daily_points=Sum("point_total")) \
                .order_by('-total_daily_points')
            cache.set(key, results, 60 * 10)

        return Response(results)


class CalendarView(views.APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request, *args, **kwargs):
        results = []
        start = request.query_params.get("start", None)
        current_date = datetime.today() if start is None else datetime.strptime(start, '%d-%m-%Y').date()
        offset = int(request.query_params.get("offset", 5))
        step = 1 if offset > 0 else -1
        lang = get_language()
        for i in range(0, offset, step):
            hijri_date = Gregorian.fromdate(current_date).to_hijri()
            hijri_date_words = f"{hijri_date.day} {hijri_date.month_name(language=lang)} {hijri_date.year}"
            greg_date_words = current_date.strftime('%d %B %Y')
            date_dict = dict(greg_date=current_date.strftime("%d-%m-%Y"),
                             greg_date_words=greg_date_words,
                             hijri_date=hijri_date.dmyformat(separator="-"),
                             hijri_date_words=hijri_date_words)
            current_date += timedelta(days=step)
            results.append(date_dict)

        return Response(results)
