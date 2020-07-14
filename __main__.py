import fire
from aiohttp import web
from heidi.util import fearward, jsonify_response
from heidi.util import init_redis, init_data_layer

from handlers import route as routing_table


def run(port):
    app = web.Application(middlewares=[
        jsonify_response,
        fearward,
    ])

    app.add_routes(routing_table)

    app.on_startup.extend([
        init_redis,
        init_data_layer,
    ])

    web.run_app(app, port=port)


fire.Fire(run)
