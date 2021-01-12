import pathlib
import shutil

from starlette.background import BackgroundTask


class ValidationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


async def remove_temp_folder(folder_path: pathlib.Path):
    try:
        shutil.rmtree(folder_path)
    except OSError:
        pass


def remove_temp_folder_task(folder_path: pathlib.Path):
    return BackgroundTask(remove_temp_folder, folder_path=folder_path)


def get_timeout(request_data: dict, param_name: str = "timeout", default: int = 60) -> int:
    timeout = default
    if timeout_data := request_data.get(param_name):
        try:
            timeout = int(timeout_data)
        except ValueError:
            pass
    return timeout
