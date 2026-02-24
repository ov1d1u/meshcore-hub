"""Markdown extension for QR code generation.

This extension provides a simple syntax to generate QR codes as base64-encoded
PNG images that can be embedded in markdown pages.

Syntax:
    :qr:data_to_encode:

Examples:
    Simple text: :qr:https://example.com:
    
    URLs with query parameters: :qr:meshcore://channel/add?name=%23iasi&secret=abc:
    
    In tables:
    | Name | QR Code |
    |------|---------|
    | Link | :qr:https://example.com: |

The generated QR codes are output as markdown images with base64-encoded PNG data:
    ![QR Code](data:image/png;base64,...)

This allows the QR codes to be displayed directly in the rendered HTML without
requiring external image files.
"""

import base64
import logging
from io import BytesIO

import qrcode
from markdown import Extension
from markdown.preprocessors import Preprocessor

logger = logging.getLogger(__name__)


class QRCodePreprocessor(Preprocessor):
    """Preprocessor that converts QR code markdown syntax to base64 images."""

    def run(self, lines):
        """Process lines and replace QR code syntax with base64 images.

        Syntax: :qr:data_to_encode:
        """
        new_lines = []
        for line in lines:
            if ":qr:" in line:
                line = self._replace_qr_codes(line)
            new_lines.append(line)
        return new_lines

    def _replace_qr_codes(self, line: str) -> str:
        """Replace all :qr:data: patterns with base64 encoded QR code images.

        Args:
            line: The line to process.

        Returns:
            The line with QR codes replaced by base64 image tags.
        """
        import re

        def replace_qr(match):
            data = match.group(1)
            try:
                qr_code = self._generate_qr_code(data)
                return f'![QR Code]({qr_code} "QR Code")'
            except Exception as e:
                logger.error(f"Failed to generate QR code for '{data}': {e}")
                return match.group(0)

        # Match :qr:....: pattern, handling URLs with colons
        # This uses a lookahead to find the end: either a pipe (|), space + pipe, or end of line
        # Non-greedy match (.+?) combined with positive lookahead ensures we stop at the right place
        pattern = r":qr:(.+?):\s*(?=\||$|\s+(?:[a-zA-Z]|:))"
        line = re.sub(pattern, replace_qr, line)
        return line

    def _generate_qr_code(self, data: str) -> str:
        """Generate a QR code as a base64 encoded PNG image.

        Args:
            data: The data to encode in the QR code.

        Returns:
            A data URI with the base64 encoded PNG image.
        """
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # Return as data URI
        return f"data:image/png;base64,{img_base64}"


class QRCodeExtension(Extension):
    """Markdown extension for QR code generation."""

    def extendMarkdown(self, md):
        """Register the QR code preprocessor with the Markdown instance.

        Args:
            md: The Markdown instance.
        """
        md.preprocessors.register(QRCodePreprocessor(md), "qr_code", 25)


def makeExtension(**kwargs):
    """Create and return the extension instance."""
    return QRCodeExtension(**kwargs)
