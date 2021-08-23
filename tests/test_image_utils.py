import pytest
from fan_tools.python import rel_path
from fan_tools.image_utils import Transpose


@pytest.fixture
def png_content():
    with rel_path('./image.png').open('rb') as f:
        yield f.read()


def test_png_to_jpg(png_content):
    out = Transpose().process_binary(png_content, raise_on_open=True)
    assert len(out) > 0
    assert out != png_content
