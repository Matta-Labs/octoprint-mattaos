'''
This module is responsible for downloading and uploading files to the MattaOS
as well as long websocket processes
'''
import os
import queue
import threading
from inspect import Signature
from .utils import download_file_from_url, post_file_to_backend_for_download

# class FileWorker:
#     def __init__(self, file_manager, printer) -> None:
#         self.file_manager = file_manager
#         self.printer = printer

#         self.start_worker_threads()

#     def start_worker_threads(self):
#         # Make queue for managing the download and print tasks
#         if not hasattr(self, "queue"):
#             self.queue = queue.Queue()
#             self.queue_condition = threading.Condition()

#         # Start the main worker thread
#         self.main_thread = threading.Thread(target=self.thread_loop)
#         self.main_thread.daemon = True
#         self.thread_running = True
#         self.main_thread.start()
#         self._logger.info("Main worker thread running.")

#     def thread_loop(self):

class FileObjectWithSaveMethod:
    response = None
    def __init__(self, response) -> None:
        self.response = response
    def save(self, destination_path):
        with open(destination_path, "w") as file:
            file.write(self.response)

def download_file_and_print(file_url, destination, signature: Signature, json_file: dict, file_manager, printer):
    
    # Check if 'destination' or 'location' are in the parameters
    has_destination = 'destination' in signature.parameters
    has_location = 'location' in signature.parameters

    # download the file from the URL
    response = download_file_from_url(file_url)
    if response is None:
        return

    if has_destination:
        file_manager.add_file(
            path=json_file["file"],
            file_object=FileObjectWithSaveMethod(response),
            destination=destination,
            allow_overwrite=True,
        )
    elif has_location:
        file_manager.add_file(
            path=json_file["file"],
            file_object=FileObjectWithSaveMethod(response),
            location=destination,
            allow_overwrite=True,
        )
    else:
        file_manager.add_file(
            path=json_file["file"],
            file_object=FileObjectWithSaveMethod(response),
            allow_overwrite=True,
        )

    if json_file["print"]:
        on_sd = True if json_file["loc"] == "sd" else False
        printer.select_file(
            json_file["file"], sd=on_sd, printAfterSelect=True
        )

def upload_file_to_backend(full_path, auth_token):
    with open(full_path, "r") as file:
        file_content = file.read()
        response = post_file_to_backend_for_download(
            os.path.basename(full_path),
            file_content,
            auth_token,
        )