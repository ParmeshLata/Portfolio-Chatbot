import json
import os
import re
import requests

PUSHOVER_URL = 'https://api.pushover.net/1/messages.json'


def push(message):
    user, token = os.getenv('PUSHOVER_USER'), os.getenv('PUSHOVER_TOKEN')
    if not user or not token:
        return {'recorded': False, 'error': 'Pushover is not configured'}
    try:
        response = requests.post(PUSHOVER_URL,
                                 data={'user': user, 'token': token, 'message': message[:1024]},
                                 timeout=5)
        response.raise_for_status()
        payload = response.json()
        return {'recorded': payload.get('status') == 1}
    except (requests.RequestException, ValueError) as exc:
        return {'recorded': False, 'error': type(exc).__name__}


def record_user_details(email, name='Name not provided', notes='not provided'):
    if not isinstance(email, str) or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        return {'recorded': False, 'error': 'Invalid email'}
    return push(f'Recruiter contact: {str(name)[:100]} | {email[:254]} | {str(notes)[:500]}')


def record_unknown_question(question):
    if not isinstance(question, str) or not question.strip():
        return {'recorded': False, 'error': 'Missing question'}
    return push(f'Unknown profile question: {question[:900]}')


tools = [
    {'type': 'function', 'function': {
        'name': 'record_user_details',
        'description': 'Record contact details only when the visitor explicitly asks to be contacted and knowingly provides their email.',
        'parameters': {'type': 'object', 'properties': {
            'email': {'type': 'string'}, 'name': {'type': 'string'},
            'notes': {'type': 'string'}}, 'required': ['email'], 'additionalProperties': False}}},
    {'type': 'function', 'function': {
        'name': 'record_unknown_question',
        'description': 'Notify the owner about a candidate-specific question that the available profile cannot answer.',
        'parameters': {'type': 'object', 'properties': {'question': {'type': 'string'}},
                       'required': ['question'], 'additionalProperties': False}}}
]

REGISTRY = {'record_user_details': record_user_details,
            'record_unknown_question': record_unknown_question}


def handle_tool_calls(tool_calls, seen=None):
    seen = seen if seen is not None else set()
    results = []
    for call in tool_calls:
        name = call.function.name
        try:
            args = json.loads(call.function.arguments)
            if not isinstance(args, dict) or name not in REGISTRY:
                raise ValueError('Invalid tool or arguments')
            allowed = {'record_user_details': {'email', 'name', 'notes'},
                       'record_unknown_question': {'question'}}[name]
            if set(args) - allowed:
                raise ValueError('Unexpected arguments')
            signature = json.dumps([name, args], sort_keys=True)
            if signature in seen:
                outcome = {'recorded': False, 'duplicate': True}
            else:
                seen.add(signature)
                outcome = REGISTRY[name](**args)
        except (ValueError, TypeError, KeyError) as exc:
            outcome = {'recorded': False, 'error': str(exc)[:150]}
        results.append({'role': 'tool', 'tool_call_id': call.id,
                        'content': json.dumps(outcome)})
    return results
