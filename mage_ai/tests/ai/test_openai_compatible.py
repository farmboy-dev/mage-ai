import asyncio
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from mage_ai.ai.openai_client import OpenAIClient
from mage_ai.orchestration.ai.config import OpenAIConfig


class CompatibleAITest(unittest.IsolatedAsyncioTestCase):
    async def test_internal_chat_and_tools(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                requests.append((self.path, body, self.headers.get('Authorization')))
                message = {'role': 'assistant', 'content': '```json\n{"answer": 42}\n```'}
                if 'tools' in body:
                    message.update(content=None, tool_calls=[{
                        'id': 'test-call', 'type': 'function', 'function': {
                            'name': 'classify_description',
                            'arguments': json.dumps({'BlockType': 'BlockType__transformer'}),
                        },
                    }])
                data = json.dumps({'id': 'local', 'object': 'chat.completion', 'created': 0,
                                   'model': body['model'], 'choices': [
                                       {'index': 0, 'message': message, 'finish_reason': 'stop'},
                                   ]}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        repo = SimpleNamespace(ai_config={}, openai_api_key=None,
                               openai_base_url=f'http://127.0.0.1:{server.server_port}/v1',
                               openai_model='internal-model')
        try:
            with patch('mage_ai.ai.openai_client.get_repo_config', return_value=repo):
                client = OpenAIClient(OpenAIConfig())
            try:
                result = await client.inference_with_prompt({'value': '42'}, 'Answer {value}')
                self.assertEqual(result, {'answer': 42})
                result = await client.find_block_params('Transform rows')
                self.assertEqual(result['block_type'], 'transformer')
                self.assertTrue(all(path == '/v1/chat/completions' for path, _, _ in requests))
                self.assertTrue(all(body['model'] == 'internal-model' for _, body, _ in requests))
                self.assertEqual(requests[0][1]['messages'][0]['content'], 'Answer 42')
                self.assertEqual(requests[0][2], 'Bearer not-required')
            finally:
                await client.openai_client.close()
        finally:
            await asyncio.to_thread(server.shutdown)
            server.server_close()
            thread.join()

    async def test_missing_endpoint_never_builds_a_client(self):
        repo = SimpleNamespace(ai_config={}, openai_api_key='test',
                               openai_base_url=None, openai_model='internal-model')
        with patch.dict(os.environ, {}, clear=True), patch(
            'mage_ai.ai.openai_client.get_repo_config', return_value=repo,
        ), patch('mage_ai.ai.openai_client.AsyncOpenAI') as constructor:
            with self.assertRaisesRegex(ValueError, 'base URL and model'):
                OpenAIClient(OpenAIConfig())
            constructor.assert_not_called()

    async def test_configuration_precedence_and_readiness(self):
        repo = SimpleNamespace(ai_config={'open_ai_config': {'openai_model': 'nested'}},
                               openai_api_key=None, openai_base_url=None, openai_model=None)
        with patch.dict(os.environ, {'OPENAI_BASE_URL': 'http://internal/v1',
                                     'OPENAI_MODEL': 'environment', 'OPENAI_API_KEY': 'test'}):
            config = OpenAIConfig.resolve(repo)
            self.assertTrue(config.configured)
            self.assertEqual(config.openai_model, 'nested')
            self.assertEqual(config.openai_api_key, 'test')
            repo.openai_model = 'project'
            self.assertEqual(OpenAIConfig.resolve(repo).openai_model, 'project')
        for url in ('', 123, 'file:///tmp/model', 'https://host/v1?key=secret',
                    'http://host:wrong/v1', 'http://host:99999/v1', 'http://host:0/v1',
                    'http://user:secret@host/v1', 'http://bad host/v1'):
            self.assertFalse(OpenAIConfig(openai_base_url=url, openai_model='model').configured)

    async def test_json_fences_and_plain_text(self):
        client = object.__new__(OpenAIClient)
        client.model = 'internal-model'
        create = AsyncMock()
        client.openai_client = SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(create=create)))
        for content in ('```json {"value": 1}```', '```{"value": 1}```',
                        '```json\n{"value": 1}\n```', '{"value": 1}'):
            create.return_value = SimpleNamespace(choices=[SimpleNamespace(
                message=SimpleNamespace(content=content))])
            self.assertEqual(await client.inference_with_prompt({}, 'Return JSON'), {'value': 1})
        create.return_value.choices[0].message.content = 'plain text'
        self.assertEqual(await client.inference_with_prompt({}, 'Return text', False), 'plain text')
        create.return_value.choices[0].message.content = '```'
        self.assertEqual(await client.inference_with_prompt({}, 'Return JSON'), {})

    async def test_model_without_tool_support_has_clear_error(self):
        client = object.__new__(OpenAIClient)
        client.model = 'internal-model'
        create = AsyncMock(return_value=SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(tool_calls=None))]))
        client.openai_client = SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(create=create)))
        with self.assertRaisesRegex(ValueError, 'must support tool calling'):
            await client.find_block_params('Load data')
