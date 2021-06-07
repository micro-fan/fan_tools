import os
import zipfile
from functools import reduce
import io
from typing import Callable, Iterable, Optional, Union


FileType = Union[str, os.PathLike, io.BytesIO]


def default_filterfunc(name: str) -> bool:
    if os.path.basename(name) == '.DS_Store':
        return False
    if name.startswith('__MACOSX'):
        return False
    return True


def merge_zip(
    file1: FileType,
    file2: FileType,
    filterfunc: Callable = default_filterfunc,
) -> io.BytesIO:
    """
    Merge `zip1` and `zip2`.

    The second zip will overwrite the first zip.
    """
    zip1 = zipfile.ZipFile(file1)
    zip2 = zipfile.ZipFile(file2)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a') as zip_file:
        written = []

        for filename in filter(filterfunc, zip2.namelist()):
            zip_file.writestr(filename, zip2.open(filename).read())
            written.append(filename)

        for filename in filter(filterfunc, zip1.namelist()):
            if filename not in written:
                zip_file.writestr(filename, zip1.open(filename).read())

    zip_buffer.seek(0)
    return zip_buffer


def merge_many_zip(files: Iterable[FileType]) -> io.BytesIO:
    return reduce(merge_zip, files)


def force_zip(file: FileType, name: Optional[str] = None) -> Union[io.BytesIO, FileType]:
    if zipfile.is_zipfile(file):
        # Method `is_zipfile` change the stream position to the last byte.
        file.seek(0)
        return file
    else:
        assert name is not None, 'If `file` is not zipfile, argument `name` is required.'
        zip_buffer = io.BytesIO()

        if isinstance(file, os.PathLike):
            file = os.fspath(file)
        if isinstance(file, str):
            file = io.open(file, 'rb')

        with zipfile.ZipFile(zip_buffer, 'a') as zip_file:
            file.seek(0)
            zip_file.writestr(os.path.basename(name), file.read())
        return zip_buffer
