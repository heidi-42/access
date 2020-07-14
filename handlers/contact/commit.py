from string import ascii_letters, digits
from aiohttp.web import HTTPBadRequest

from heidi.data import Contact
from heidi.etext.access import NO_CODE, BAD_CODE, CODE_NOT_FOUND

from handlers import route

CODE_ALPHABET = ascii_letters + digits


def is_code(text):
    if len(text) != 6:
        return False
    return all(char in CODE_ALPHABET for char in text)


@route.get('/contact/commit')
async def get_contact_commit(request):
    if 'code' not in request.rel_url.query:
        raise HTTPBadRequest(reason=NO_CODE)

    code = request.rel_url.query['code']
    if not is_code(code):
        raise HTTPBadRequest(reason=BAD_CODE)

    key = f'access:{code}'

    redis = request.app['redis']
    if not await redis.exists(key):
        raise HTTPBadRequest(reason=CODE_NOT_FOUND)

    stashed = await redis.hgetall(key)

    user, provider = int(stashed['user']), stashed['provider']
    value = stashed['value']
    await Contact.create(user=user, provider=provider, value=value)

    await redis.delete(key)

