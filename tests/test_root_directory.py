import io
import pathlib
import zipfile

import pytest

from fan_tools.python import root_directory


@pytest.fixture
def simple_file(tmpdir):
    def create(filename: str, content):
        file_dir = tmpdir
        parts = filename.split('/')
        for part in parts[:-1]:
            if pathlib.Path(f'{file_dir}/{part}').exists():
                continue
            file_dir = file_dir.mkdir(part)
        file_dir = file_dir.join(filename.split('/')[-1])
        file_path = pathlib.Path(file_dir)
        mode = 'w'
        if isinstance(content, bytes):
            mode += 'b'
        with open(file_path, mode) as file:
            file.write(content)
            return file_path

    yield create


class TestRootDirectory:
    def test_zip_file(self, tmpdir, simple_file):
        zip_file = pathlib.Path(f"{tmpdir}/zip_file.zip")
        with zipfile.ZipFile(zip_file, "a") as zip:
            cases = [
                'root_dir/test_file.txt',
                'root_dir/subfolder/test_file.txt',
            ]
            for case in cases:
                file = simple_file(case, '')
                zip.write(file, case)
            zip.writestr(zipfile.ZipInfo(f'empty_dir/'), '')
            zip.close()
        assert root_directory(io.BytesIO(zip_file.read_bytes())) == pathlib.Path('root_dir')

    def test_folders(self, tmpdir, simple_file):
        tmpdir.mkdir("root_dir").join("test_file.txt").write("")
        tmpdir.join("root_dir").mkdir("subfolder").join("test_file.txt").write("")
        assert root_directory(pathlib.Path(tmpdir)) == pathlib.Path(f'{tmpdir}/root_dir')

    def test_exclude(self, tmpdir, simple_file):
        tmpdir.mkdir("root_dir").join("test_file.txt").write("")
        tmpdir.join("root_dir").mkdir("subfolder").join("test_file.txt").write("")
        tmpdir.mkdir("EXCLUDE")
        tmpdir.mkdir("__MACOS").join("test_file.txt").write("")
        assert root_directory(pathlib.Path(tmpdir), exclude=["__MACOS", "EXCLUDE"]) == pathlib.Path(
            f'{tmpdir}/root_dir'
        )
