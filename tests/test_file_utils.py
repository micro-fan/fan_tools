import pathlib
import zipfile
from io import BytesIO

import pytest
from fan_tools.file_utils import force_zip, merge_many_zip, merge_zip


@pytest.fixture(scope='session')
def zip1():
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a') as zip_file:
        zip_file.writestr('conflict_file', 'value_from_1_arch')
        zip_file.writestr('file_from_1_archive', 'value_for_file_from_1_archive')
    return zip_buffer


@pytest.fixture(scope='session')
def zip2():
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a') as zip_file:
        zip_file.writestr('conflict_file', 'value_from_2_arch')
        zip_file.writestr('file_from_2_archive', 'value_for_file_from_2_archive')
    return zip_buffer


@pytest.fixture(scope='session')
def zip3():
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a') as zip_file:
        zip_file.writestr('conflict_file', 'value_from_3_arch')
        zip_file.writestr('file_from_3_archive', 'value_for_file_from_3_archive')
    return zip_buffer


@pytest.fixture
def zip2_as_str(tmpdir):
    zip_buffer = tmpdir.join('zip2.zip')
    with zipfile.ZipFile(zip_buffer, 'a') as zip_file:
        zip_file.writestr('conflict_file', 'value_from_2_arch')
        zip_file.writestr('file_from_2_archive', 'value_for_file_from_2_archive')
    return zip_buffer


@pytest.fixture
def zip3_as_pathlike(tmpdir):
    zip_buffer = pathlib.Path(tmpdir.join('zip3.zip'))
    with zipfile.ZipFile(zip_buffer, 'a') as zip_file:
        zip_file.writestr('conflict_file', 'value_from_3_arch')
        zip_file.writestr('file_from_3_archive', 'value_for_file_from_3_archive')
    return zip_buffer


def test_merge_zip(zip1, zip2):
    zip_ = zipfile.ZipFile(merge_zip(zip1, zip2))

    assert zip_.open('conflict_file').read().decode() == 'value_from_2_arch'
    assert zip_.open('file_from_1_archive').read().decode() == 'value_for_file_from_1_archive'
    assert zip_.open('file_from_2_archive').read().decode() == 'value_for_file_from_2_archive'


def test_merge_many_zip(zip1, zip2, zip3):
    zip_ = zipfile.ZipFile(merge_many_zip((zip1, zip2, zip3)))

    assert zip_.open('conflict_file').read().decode() == 'value_from_3_arch'
    assert zip_.open('file_from_1_archive').read().decode() == 'value_for_file_from_1_archive'
    assert zip_.open('file_from_2_archive').read().decode() == 'value_for_file_from_2_archive'
    assert zip_.open('file_from_3_archive').read().decode() == 'value_for_file_from_3_archive'


def test_merge_many_zip_different_types(zip1, zip2_as_str, zip3_as_pathlike):
    zip_ = zipfile.ZipFile(merge_many_zip((zip1, zip2_as_str, zip3_as_pathlike)))

    assert zip_.open('conflict_file').read().decode() == 'value_from_3_arch'
    assert zip_.open('file_from_1_archive').read().decode() == 'value_for_file_from_1_archive'
    assert zip_.open('file_from_2_archive').read().decode() == 'value_for_file_from_2_archive'
    assert zip_.open('file_from_3_archive').read().decode() == 'value_for_file_from_3_archive'


def test_force_zip(zip1):
    res1 = force_zip(zip1)
    assert res1 == zip1

    filename = 'test.json'
    content = b'{"a":"b"}'
    res2 = force_zip(BytesIO(content), filename)

    assert zipfile.is_zipfile(res2)

    zip_obj = zipfile.ZipFile(res2)

    assert len(zip_obj.namelist()) == 1
    assert zip_obj.read(filename) == content
