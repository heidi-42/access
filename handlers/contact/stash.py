from aiohttp.web import HTTPConflict, HTTPForbidden

import heidi.email
from heidi.data import User, Contact
from heidi.util import hmset_serialize
from heidi.etext.access import UNKNOWN_EMAIL, CONTACT_EXISTS

from jsonschema import validate

from code import generate_unique_code
from handlers import route

schema = {
    'type': 'object',
    'properties': {
        'email': {
            'type': 'string',
            # len('@voenmeh.ru') == 11
            'pattern': r'^[a-zA-Z0-9_-]{1,245}(@voenmeh\.ru)$'
        },

        # Postgres will ensure data integrity on this one
        'provider': {
            'type': 'string',
        },

        # Retrieve this from the provider API in user-independent manner
        'value': {
            'type': 'string',
        }
    },

    'required': [
        'email',
        'provider',
        'value',
    ]
}

stash_ttl = 60 * 24


@route.put('/contact/stash')
async def get_contact_stash(request):
    payload = await request.json()
    validate(payload, schema)

    # Normalization
    email = payload['email'].lower()
    user = await User.query.where(User.email == email).gino.one_or_none()
    if not user:
        raise HTTPForbidden(reason=UNKNOWN_EMAIL) 

    contact = await Contact.query.where(
        (Contact.user == user.id) &
        (Contact.provider == payload['provider']) &
        (Contact.value == payload['value'])
    ).gino.one_or_none()

    # Current data layer does not ensure contact uniqueness in
    # user-provider scope
    if contact:
        raise HTTPConflict(reason=CONTACT_EXISTS)

    redis = request.app['redis']
    code = f'access:{await generate_unique_code(redis)}'

    to_stash = {
        'user': user.id,
        'provider': payload['provider'],
        'value': payload['value'],
    }

    transaction = redis.multi_exec()
    transaction.hmset(code, *hmset_serialize(to_stash))
    transaction.expire(code, stash_ttl)
    await transaction.execute()

    await heidi.email.template_email(
        recipients=[email],
        template='stash_contact.jinja2',
        # Cutting off the prefix
        data={'code': code[7:]}
    )

