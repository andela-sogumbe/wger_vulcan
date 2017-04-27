# -*- coding: utf-8 -*-

# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License

import logging
from urllib.parse import urlencode, quote
from base64 import b64encode
import requests
from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, reverse_lazy
from django.core import mail
from django.utils.translation import ugettext as _
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as django_login
from django.template.loader import render_to_string
from django.conf import settings

from wger.core.forms import FeedbackRegisteredForm, FeedbackAnonymousForm
from wger.core.demo import create_demo_entries, create_temporary_user
from wger.core.models import (DaysOfWeek,
                              FitBitAppDetails,
                              UserFitBitDetails,
                              UserFitBitScope,)
from wger.manager.models import Schedule
from wger.nutrition.models import NutritionPlan
from wger.weight.models import WeightEntry
from wger.weight.helpers import get_last_entries


logger = logging.getLogger(__name__)


# ************************
# Misc functions
# ************************
def index(request):
    '''
    Index page
    '''
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('core:dashboard'))
    else:
        return HttpResponseRedirect(reverse('software:features'))


def demo_entries(request):
    '''
    Creates a set of sample entries for guest users
    '''
    if not settings.WGER_SETTINGS['ALLOW_GUEST_USERS']:
        return HttpResponseRedirect(reverse('software:features'))

    if (((not request.user.is_authenticated() or request.user.userprofile.is_temporary)
         and not request.session['has_demo_data'])):
        # If we reach this from a page that has no user created by the
        # middleware, do that now
        if not request.user.is_authenticated():
            user = create_temporary_user()
            django_login(request, user)

        # OK, continue
        create_demo_entries(request.user)
        request.session['has_demo_data'] = True
        messages.success(request, _('We have created sample workout, workout schedules, weight '
                                    'logs, (body) weight and nutrition plan entries so you can '
                                    'better see what  this site can do. Feel free to edit or '
                                    'delete them!'))
    return HttpResponseRedirect(reverse('core:dashboard'))


@login_required
def dashboard(request):
    '''
    Show the index page, in our case, the last workout and nutritional plan
    and the current weight
    '''

    template_data = {}

    # Load the last workout, either from a schedule or a 'regular' one
    (current_workout, schedule) = Schedule.objects.get_current_workout(request.user)

    template_data['current_workout'] = current_workout
    template_data['schedule'] = schedule

    # Load the last nutritional plan, if one exists
    try:
        plan = NutritionPlan.objects.filter(user=request.user).latest('creation_date')
    except ObjectDoesNotExist:
        plan = False
    template_data['plan'] = plan

    # Load the last logged weight entry, if one exists
    try:
        weight = WeightEntry.objects.filter(user=request.user).latest('date')
    except ObjectDoesNotExist:
        weight = False
    template_data['weight'] = weight
    template_data['last_weight_entries'] = get_last_entries(request.user)

    # Format a bit the days so it doesn't have to be done in the template
    used_days = {}
    if current_workout:
        for day in current_workout.day_set.select_related():
            for day_of_week in day.day.select_related():
                used_days[day_of_week.id] = day.description

    week_day_result = []
    for week in DaysOfWeek.objects.all():
        day_has_workout = False

        if week.id in used_days:
            day_has_workout = True
            week_day_result.append((_(week.day_of_week), used_days[week.id], True))

        if not day_has_workout:
            week_day_result.append((_(week.day_of_week), _('Rest day'), False))

    template_data['weekdays'] = week_day_result

    if plan:

        # Load the nutritional info
        template_data['nutritional_info'] = plan.get_nutritional_values()


    # Check if user has authorized fitbit, if not button will be
    # added in the template
    fitbit_details = UserFitBitDetails.objects.filter(wger_user_id=request.user,
                                                      enabled_fitbit=True).first()
    if fitbit_details and fitbit_details.enabled_fitbit:
        template_data["has_fitbit"] = True
    else:
        template_data["has_fitbit"] = False
        fitbit_app = FitBitAppDetails.objects.all().first()
        site_uri = settings.SITE_URL.replace("localhost",
                                             "127.0.0.1")
        redirect_uri = site_uri + reverse("core:dashboard")
        scope = ["activity", "nutrition", "heartrate", "location", "nutrition",
                 "profile", "settings", "sleep", "social", "weight"]

        params = {"response_type": "code",
                  "client_id": fitbit_app.client_id,
                  "redirect_uri": redirect_uri,
                  "scope": " ".join(scope)}

        # Set url for 'sync with fitbit button'
        params = urlencode(params, quote_via=quote)
        fitbit_auth_url = "https://www.fitbit.com/oauth2/authorize?" + params
        template_data["fitbit_auth_url"] = fitbit_auth_url

        # If redirecting from fitbit authorisation page, get the access token
        # you should probably check referers in the future
        auth_code = request.GET.get("code")
        if auth_code:
            raw_auth_header = fitbit_app.client_id + ":" + fitbit_app.client_secret

            # Base 64 encode for authorization header
            auth_header = "Basic " + b64encode(raw_auth_header.encode()).decode()

            headers = {"Authorization": auth_header}
            params = {"code": auth_code,
                      "grant_type": "authorization_code",
                      "client_id": fitbit_app.client_id,
                      "redirect_uri": redirect_uri}

            access_url = "https://api.fitbit.com/oauth2/token"
            # Get user access_token and refresh_token
            access_request = requests.post(access_url,
                                           data=params,
                                           headers=headers)
            current_timestamp = datetime.timestamp(datetime.now())
            expiry_timestamp = current_timestamp + data["expires_in"]
            expires_in = datetime.fromtimestamp(expiry_timestamp)

            if access_request.status_code == 200:
                data = access_request.json()
                user_fitbit_data = {"wger_user_id": request.user,
                                    "user_id": data["user_id"],
                                    "access_token": data["access_token"],
                                    "refresh_token": data["refresh_token"],
                                    "enabled_fitbit": True,
                                    "expires_in": expires_in}
                UserFitBitDetails.objects.create(**user_fitbit_data)

                scopes_returned = data["scope"]

                user_scope = {"user": request.user}
                for scope_to_check in scope:
                    if scope_to_check in scopes_returned:
                        user_scope[scope_to_check] = True

                UserFitBitScope.objects.create(**user_scope)
                template_data["has_fitbit"] = True

    return render(request, 'index.html', template_data)


class ContactClassView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(ContactClassView, self).get_context_data(**kwargs)
        context.update({'contribute': reverse('software:contribute'),
                        'issues': reverse('software:issues'),
                        'feedback': reverse('core:feedback')})
        return context


class FeedbackClass(FormView):
    template_name = 'form.html'
    success_url = reverse_lazy('core:contact')

    def get_initial(self):
        '''
        Fill in the contact, if available
        '''
        if self.request.user.is_authenticated():
            return {'contact': self.request.user.email}
        return {}

    def get_context_data(self, **kwargs):
        '''
        Set necessary template data to correctly render the form
        '''
        context = super(FeedbackClass, self).get_context_data(**kwargs)
        context['title'] = _('Feedback')
        # TODO: change template so it iterates through form and not formfields
        context['form_fields'] = context['form']
        context['form_action'] = reverse('core:feedback')
        context['submit_text'] = _('Send')
        context['contribute_url'] = reverse('software:contribute')
        context['extend_template'] = 'base_empty.html' if self.request.is_ajax() else 'base.html'
        return context

    def get_form_class(self):
        '''
        Load the correct feedback form depending on the user
        (either with reCaptcha field or not)
        '''
        if self.request.user.is_anonymous() or self.request.user.userprofile.is_temporary:
            return FeedbackAnonymousForm
        else:
            return FeedbackRegisteredForm

    def form_valid(self, form):
        '''
        Send the feedback to the administrators
        '''
        messages.success(self.request, _('Your feedback was successfully sent. Thank you!'))

        context = {}
        context['user'] = self.request.user
        context['form_data'] = form.cleaned_data

        subject = 'New feedback'
        message = render_to_string('user/email_feedback.html', context)
        mail.mail_admins(subject, message)

        return super(FeedbackClass, self).form_valid(form)
