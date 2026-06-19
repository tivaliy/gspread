import datetime
import json
from unittest import TestCase
from unittest.mock import Mock

from gspread.http_client import HTTPClient


class HTTPClientSerializerTest(TestCase):
    def _make_client(self):
        session = Mock()
        session.request.return_value.ok = True  # so request() returns, doesn't raise
        return HTTPClient(auth=None, session=session), session

    def test_default_uses_json_kwarg(self):
        """Without a serializer, the body goes out via json= (unchanged behavior)."""
        client, session = self._make_client()
        body = {"values": [[1, 2, 3]]}

        client.request("post", "http://example.com", json=body)

        _, kwargs = session.request.call_args
        self.assertEqual(kwargs["json"], body)
        self.assertIsNone(kwargs["data"])

    def test_custom_serializer_uses_data_and_header(self):
        """With a serializer, the body is serialized into data= with a JSON header."""
        client, session = self._make_client()
        client.set_serializer(lambda b: json.dumps(b, default=str))
        body = {"values": [[1, 2, 3]]}

        client.request("post", "http://example.com", json=body)

        _, kwargs = session.request.call_args
        self.assertIsNone(kwargs["json"])
        self.assertEqual(kwargs["data"], json.dumps(body, default=str))
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")

    def test_custom_serializer_handles_non_native_types(self):
        """The actual use case from the issue: serialize a date the stdlib can't."""
        client, session = self._make_client()
        client.set_serializer(lambda b: json.dumps(b, default=lambda o: o.isoformat()))
        body = {"values": [[datetime.date(2026, 6, 19)]]}

        client.request("post", "http://example.com", json=body)

        _, kwargs = session.request.call_args
        self.assertIn("2026-06-19", kwargs["data"])
