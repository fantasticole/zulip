# Webhooks for external integrations.

from typing import Any, Dict

import ujson
from django.http import HttpRequest, HttpResponse
from django.utils.translation import ugettext as _

from zerver.decorator import api_key_only_webhook_view
from zerver.lib.actions import check_send_stream_message
from zerver.lib.request import REQ, has_request_variables
from zerver.lib.response import json_error, json_success
from zerver.models import UserProfile

CODESHIP_SUBJECT_TEMPLATE = '{project_name}'
CODESHIP_MESSAGE_TEMPLATE = '[Build]({build_url}) triggered by {committer} on {branch} branch {status}.'

CODESHIP_DEFAULT_STATUS = 'has {status} status'
CODESHIP_STATUS_MAPPER = {
    'testing': 'started',
    'error': 'failed',
    'success': 'succeeded',
}


@api_key_only_webhook_view('Codeship')
@has_request_variables
def api_codeship_webhook(request: HttpRequest, user_profile: UserProfile,
                         payload: Dict[str, Any]=REQ(argument_type='body'),
                         stream: str=REQ(default='codeship')) -> HttpResponse:
    payload = payload['build']
    subject = get_subject_for_http_request(payload)
    body = get_body_for_http_request(payload)

    check_send_stream_message(user_profile, request.client, stream, subject, body)
    return json_success()


def get_subject_for_http_request(payload: Dict[str, Any]) -> str:
    return CODESHIP_SUBJECT_TEMPLATE.format(project_name=payload['project_name'])


def get_body_for_http_request(payload: Dict[str, Any]) -> str:
    return CODESHIP_MESSAGE_TEMPLATE.format(
        build_url=payload['build_url'],
        committer=payload['committer'],
        branch=payload['branch'],
        status=get_status_message(payload)
    )


def get_status_message(payload: Dict[str, Any]) -> str:
    build_status = payload['status']
    return CODESHIP_STATUS_MAPPER.get(build_status, CODESHIP_DEFAULT_STATUS.format(status=build_status))
