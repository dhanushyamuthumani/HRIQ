import unittest
import os
from core.text_extractor import extract_text

class TestTextExtractor(unittest.TestCase):
    def test_unsupported_format(self):
        text = extract_text("test.txt")
        self.assertIsNone(text)

    def test_non_existent_file(self):
        text = extract_text("non_existent.pdf")
        self.assertIsNone(text)

if __name__ == "__main__":
    unittest.main()
