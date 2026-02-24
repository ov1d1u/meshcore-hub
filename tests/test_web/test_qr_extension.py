"""Tests for QR code markdown extension."""

import pytest

from meshcore_hub.web.qr_extension import QRCodeExtension, QRCodePreprocessor


class TestQRCodePreprocessor:
    """Test the QR code preprocessor."""

    def test_simple_qr_code(self):
        """Test generating a simple QR code."""
        preprocessor = QRCodePreprocessor(None)
        line = ":qr:https://example.com:"
        result = preprocessor._replace_qr_codes(line)

        # Should contain base64 encoded PNG
        assert "data:image/png;base64," in result
        assert "![QR Code]" in result

    def test_qr_code_with_special_characters(self):
        """Test QR code with URL-encoded special characters."""
        preprocessor = QRCodePreprocessor(None)
        line = ":qr:meshcore://channel/add?name=%23iasi&secret=abc123:"
        result = preprocessor._replace_qr_codes(line)

        assert "data:image/png;base64," in result
        assert "![QR Code]" in result

    def test_qr_code_in_table_cell(self):
        """Test QR code in markdown table cell."""
        preprocessor = QRCodePreprocessor(None)
        line = "| Channel | :qr:https://example.com: |"
        result = preprocessor._replace_qr_codes(line)

        assert "data:image/png;base64," in result

    def test_multiple_qr_codes_in_line(self):
        """Test multiple QR codes in one line."""
        preprocessor = QRCodePreprocessor(None)
        line = ":qr:https://example1.com: and :qr:https://example2.com:"
        result = preprocessor._replace_qr_codes(line)

        # Should have 2 data URIs
        count = result.count("data:image/png;base64,")
        assert count == 2

    def test_no_qr_code(self):
        """Test line without QR code syntax."""
        preprocessor = QRCodePreprocessor(None)
        line = "This is a normal line with no QR codes"
        result = preprocessor._replace_qr_codes(line)

        # Should be unchanged
        assert result == line

    def test_qr_code_with_colons_in_url(self):
        """Test QR code with URLs containing colons."""
        preprocessor = QRCodePreprocessor(None)
        line = ":qr:https://example.com:8080/path:"
        result = preprocessor._replace_qr_codes(line)

        # Should successfully extract the URL with colons
        assert "data:image/png;base64," in result

    def test_qr_code_generation_error_handling(self):
        """Test that invalid data still returns valid output."""
        preprocessor = QRCodePreprocessor(None)
        # Even with a very long string, should not crash
        long_string = "x" * 2000
        line = f":qr:{long_string}:"
        result = preprocessor._replace_qr_codes(line)

        # Should still generate a QR code (even if it's an error correction type)
        assert "data:image/png;base64," in result


class TestQRCodeExtension:
    """Test the markdown extension integration."""

    def test_extension_registration(self):
        """Test that the extension registers with Markdown."""
        import markdown

        md = markdown.Markdown(extensions=[QRCodeExtension()])

        # Check that the preprocessor is registered
        assert "qr_code" in md.preprocessors

    def test_full_markdown_with_qr_codes(self):
        """Test full markdown processing with QR codes."""
        import markdown

        md = markdown.Markdown(extensions=[QRCodeExtension()])

        markdown_text = """
# Test Page

Here is a QR code: :qr:https://example.com:

And in a table:

| Name | QR Code |
|------|---------|
| Test | :qr:https://test.com: |
"""

        result = md.convert(markdown_text)

        # Should have converted both QR codes to base64 images
        assert result.count("data:image/png;base64,") == 2
