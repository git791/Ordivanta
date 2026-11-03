import asyncio
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send

from app.main import app

async def test_scope():
    received_headers = {}
    async def mock_receive():
        return {'type': 'http.request', 'body': b'', 'more_body': False}

    async def mock_send(message):
        if message['type'] == 'http.response.start':
            received_headers['status'] = message['status']
            for k, v in message.get('headers', []):
                received_headers[k.decode('latin1')] = v.decode('latin1')

    # 1. Test OPTIONS preflight with double slash //api/health
    scope = {
        'type': 'http',
        'http_version': '1.1',
        'method': 'OPTIONS',
        'path': '//api/health',
        'raw_path': b'//api/health',
        'query_string': b'',
        'headers': [
            (b'origin', b'https://ordivanta.vercel.app'),
            (b'access-control-request-method', b'GET'),
            (b'access-control-request-headers', b'content-type'),
        ],
    }
    await app(scope, mock_receive, mock_send)
    print('Preflight status:', received_headers.get('status'))
    print('Preflight allow origin:', received_headers.get('access-control-allow-origin'))
    print('Preflight allow methods:', received_headers.get('access-control-allow-methods'))
    assert received_headers.get('status') == 200
    assert received_headers.get('access-control-allow-origin') == 'https://ordivanta.vercel.app'

    # 2. Test GET with double slash //api/health
    get_headers = {}
    async def mock_send_get(message):
        if message['type'] == 'http.response.start':
            get_headers['status'] = message['status']
            for k, v in message.get('headers', []):
                get_headers[k.decode('latin1')] = v.decode('latin1')

    scope_get = {
        'type': 'http',
        'http_version': '1.1',
        'method': 'GET',
        'path': '//api/health',
        'raw_path': b'//api/health',
        'query_string': b'',
        'headers': [
            (b'origin', b'https://ordivanta.vercel.app'),
        ],
    }
    await app(scope_get, mock_receive, mock_send_get)
    print('GET status:', get_headers.get('status'))
    print('GET allow origin:', get_headers.get('access-control-allow-origin'))
    assert get_headers.get('status') == 200
    assert get_headers.get('access-control-allow-origin') == 'https://ordivanta.vercel.app'

    print('VERIFICATION COMPLETED SUCCESSFULLY!')

if __name__ == '__main__':
    asyncio.run(test_scope())
