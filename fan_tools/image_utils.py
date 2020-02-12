import logging

import io
from PIL import Image


# From: https://github.com/matthewwithanm/pilkit/blob/master/pilkit/processors/base.py#L113-L170
from django.core.files.uploadedfile import InMemoryUploadedFile


class TransposeError(Exception): pass


class Transpose:
    """
    Rotates or flips the image.
    """

    log = logging.getLogger('Transpose')

    AUTO = 'auto'
    FLIP_HORIZONTAL = Image.FLIP_LEFT_RIGHT
    FLIP_VERTICAL = Image.FLIP_TOP_BOTTOM
    ROTATE_90 = Image.ROTATE_90
    ROTATE_180 = Image.ROTATE_180
    ROTATE_270 = Image.ROTATE_270

    methods = [AUTO]
    _EXIF_ORIENTATION_STEPS = {
        1: [],
        2: [FLIP_HORIZONTAL],
        3: [ROTATE_180],
        4: [FLIP_VERTICAL],
        5: [ROTATE_270, FLIP_HORIZONTAL],
        6: [ROTATE_270],
        7: [ROTATE_90, FLIP_HORIZONTAL],
        8: [ROTATE_90],
    }

    def __init__(self, *args):
        """
        Possible arguments:
            - Transpose.AUTO
            - Transpose.FLIP_HORIZONTAL
            - Transpose.FLIP_VERTICAL
            - Transpose.ROTATE_90
            - Transpose.ROTATE_180
            - Transpose.ROTATE_270
        The order of the arguments dictates the order in which the
        Transposition steps are taken.
        If Transpose.AUTO is present, all other arguments are ignored, and
        the processor will attempt to rotate the image according to the
        EXIF Orientation data.
        """
        super(Transpose, self).__init__()
        if args:
            self.methods = args

    def rgba_to_rgb(self, img, mode='jpg'):
        fill_color = '#ffffff'
        background = Image.new('RGB', img.size, fill_color)

        split = img.split()
        if img.mode == 'P' and len(split) < 4:
            split = img.convert('RGBA').split()

        if len(split) == 4:
            background.paste(img, mask=split[3])
        else:
            background.paste(img)
        return background

    def process_binary(self, binary, format='jpeg', raise_on_open=False):
        assert type(binary) in (bytes, bytearray), f'Wrong binary type: {type(binary)}'
        try:
            try:
                img = Image.open(io.BytesIO(binary))
            except Exception:
                if raise_on_open:
                    raise TransposeError
                raise

            if self.AUTO in self.methods:
                try:
                    orientation = img._getexif()[0x0112]
                    ops = self._EXIF_ORIENTATION_STEPS[orientation]
                except (IndexError, KeyError, TypeError, AttributeError):
                    ops = []
            else:
                ops = self.methods
            for method in ops:
                self.log.debug('Operation: {}'.format(method))
                img = img.transpose(method)
            buf = io.BytesIO()
            if img.mode in ('RGBA', 'LA', 'P') and format.upper() in ('JPG', 'JPEG'):
                img = self.rgba_to_rgb(img)
            img.save(buf, format=format, quality=100)
            buf.seek(0)
            return buf.read()
        except TransposeError:
            raise
        except Exception:
            self.log.exception('During transpose binary:')
            return binary

    def process(self, orig_img, format=None):
        try:
            fname = orig_img.name
            if format is None:
                format = fname.split('.')[-1].upper()
                if format.startswith('JP'):
                    format = 'JPEG'
            buf = io.BytesIO(self.process_binary(orig_img.read(), format=format))
            # seek to the end of file
            buf.seek(0, 2)
            out = InMemoryUploadedFile(buf, "image", fname, orig_img.content_type, buf.tell(), None)
            return out
        except Exception:
            return orig_img
