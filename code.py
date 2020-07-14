import secrets
import string

ALPHABET = string.ascii_uppercase + string.digits


def generate_code(length=6):
    return ''.join([secrets.choice(ALPHABET) for _ in range(length)])


async def generate_unique_code(redis, length=6):
    code = generate_code(length)
    while await redis.exists(code):
        code = generate_code(length)
    return code
