import logging

import io
from PIL import Image


# From: https://github.com/matthewwithanm/pilkit/blob/master/pilkit/processors/base.py#L113-L170
from django.core.files.uploadedfile import InMemoryUploadedFile


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

    def process(self, orig_img):
        try:
            img = Image.open(orig_img)
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
            fname = orig_img.name
            fmt = fname.split('.')[-1].upper()
            if fmt.startswith('JP'):
                fmt = 'JPEG'
            img.save(buf, format=fmt, quality=100)
            buf.seek(0, 2)
            out = InMemoryUploadedFile(buf, "image", fname, orig_img.content_type, buf.tell(), None)
            return out
        except:
            return orig_img
