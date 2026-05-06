from __future__ import annotations

import unittest

from jquants_return_ranking.security import REDACTED, sanitize_text


class SecurityTests(unittest.TestCase):
    def test_sanitize_text_replaces_explicit_secret(self):
        message = sanitize_text("request failed for secret-token-123", ("secret-token-123",))

        self.assertNotIn("secret-token-123", message)
        self.assertIn(REDACTED, message)

    def test_sanitize_text_replaces_common_api_key_fields(self):
        samples = [
            "x-api-key: abcdef",
            'api_key = "abcdef"',
            "JQUANTS_API_KEY=abcdef",
        ]

        for sample in samples:
            with self.subTest(sample=sample):
                message = sanitize_text(sample)
                self.assertNotIn("abcdef", message)
                self.assertIn(REDACTED, message)


if __name__ == "__main__":
    unittest.main()
