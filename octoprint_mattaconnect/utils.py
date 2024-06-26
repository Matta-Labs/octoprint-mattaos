import psutil
import requests
import sentry_sdk
import time
import os
from datetime import datetime
from sys import platform


MATTA_OS_ENDPOINT = "https://os.matta.ai/"
# MATTA_OS_ENDPOINT = "http://localhost"

MATTA_TMP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".matta")

SAMPLING_TIMEOUT = 1.25  # sample every 1.25 seconds


def get_cloud_http_url():
    """
    Gets the cloud HTTP URL.

    Returns:
        str: The cloud URL.
    """
    # make sure the URL ends with a slash
    url = MATTA_OS_ENDPOINT
    if not url.endswith("/"):
        url += "/"
    return url


def get_cloud_websocket_url():
    """
    Gets the cloud websocket URL.

    Returns:
        str: The cloud URL.
    """
    # make sure the URL ends with a slash
    url = MATTA_OS_ENDPOINT.replace("http", "ws")
    if not url.endswith("/"):
        url += "/"
    return url


def get_api_url():
    """
    Gets the cloud API URL.

    Returns:
        str: The cloud URL.
    """
    return get_cloud_http_url() + "api/v1/"


def generate_auth_headers(token):
    """
    Generates the authentication headers for API requests.

    Returns:
        dict: The authentication headers.
    """
    return {"Authorization": token}


def convert_bytes_to_formatted_string(bytes):
    """
    Converts bytes to a formatted string representation (KB, MB, or GB).
    """
    if bytes > 1024**3:
        bytes = str(round(bytes / 1024**3, 2)) + "GB"
    elif bytes > 1024**2:
        bytes = str(round(bytes / 1024**2, 2)) + "MB"
    elif bytes > 1024:
        bytes = str(round(bytes / 1024, 2)) + "KB"
    return bytes


def get_current_memory_usage(os):
    """
    Gets the current memory usage of the computer/SBC depending on the OS.

    Args:
        os (str): The operating system identifier. Valid values are "linux", "windows", or "mac".

    Returns:
        tuple: A tuple containing three values: used memory (formatted string),
               total memory (formatted string), and memory usage percentage.
    """
    if os == "linux":
        used = psutil.virtual_memory().used
        used = convert_bytes_to_formatted_string(used)
        total = psutil.virtual_memory().total
        total = convert_bytes_to_formatted_string(total)
        percent = psutil.virtual_memory().percent
        return used, total, percent
    elif os == "windows":
        used = psutil.virtual_memory().used
        used = convert_bytes_to_formatted_string(used)
        total = psutil.virtual_memory().total
        total = convert_bytes_to_formatted_string(total)
        percent = psutil.virtual_memory().percent
        return used, total, percent
    elif os == "mac":
        used = psutil.virtual_memory().used
        used = convert_bytes_to_formatted_string(used)
        total = psutil.virtual_memory().total
        total = convert_bytes_to_formatted_string(total)
        percent = psutil.virtual_memory().percent
        return used, total, percent
    else:
        return 0, 0, 0


def get_gcode_upload_dir():
    """
    Returns the path for the directory where G-code files are uploaded based on the platform being used.

    Returns:
        str: The path for the G-code upload directory.
    """
    if platform == "linux" or platform == "linux2":
        # linux
        raspberrypi_uploads_path = os.path.expanduser("~/.octoprint/uploads")
        if os.path.exists(raspberrypi_uploads_path):
            path = raspberrypi_uploads_path
        else:
            path = "/octoprint/octoprint/uploads"
    elif platform == "darwin":
        # OS X
        path = "~/Library/Application Support/OctoPrint/uploads"
    elif platform == "win32" or platform == "win64":
        # Windows
        path = os.path.join(os.getenv("APPDATA"), "OctoPrint", "uploads")
    return os.path.expanduser(path)


def make_timestamp():
    """Generates a timestamp string in the format 'YYYY-MM-DDTHH:MM:SS.sssZ'"""
    dt = datetime.utcnow().isoformat(sep="T", timespec="milliseconds") + "Z"
    return dt


def before_send(event, hint):
    if "logentry" in event and "message" in event["logentry"]:
        list_of_common_errors = [
            "Handshake status 404 Not Found"
            "Handshake status 500 Internal Server Error",
            "Handshake status 502 Bad Gateway",
            "Handshake status 504 Gateway Timeout",
            "Connection refused - goodbye",
            "Temporary failure in name resolution",
        ]
        for error in list_of_common_errors:
            if error in event["logentry"]["message"]:
                return None
        return event


def init_sentry(version):
    sentry_sdk.init(
        dsn="https://687d2f7c85af84f983b3d9980468c24c@o289703.ingest.sentry.io/4506337826570240",
        # Set traces_sample_rate to 0.1 to capture 10%
        # of transactions for performance monitoring.
        traces_sample_rate=0.1,
        before_send=before_send,
        # Set profiles_sample_rate to 0.1 to profile 10%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=0.1,
        release=f"octoprint-mattaos@{version}",
    )


def get_file_from_backend(bucket_file, auth_token):
    """Gets a file from the backend"""
    full_url = get_api_url() + "print-jobs/printer/gcode/uploadfile"
    headers = generate_auth_headers(auth_token)
    data = {"bucket_file": bucket_file}
    try:
        resp = requests.post(
            url=full_url,
            data=data,
            headers=headers,
        )
        # print data from resp
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        raise e  # Windows


def get_file_from_url(file_url):
    """
    Downloads file from URL and returns the file content as a string.

    Args:
        file_url (str): The URL to download the file from.
    """
    retries = 3
    decay = 2  # decay factor for wait time between retries

    for i in range(retries):
        try:
            resp = requests.get(file_url)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            if i < retries - 1:  # no need to wait after the last try
                time.sleep(decay ** i)  # wait time increases with each retry
            else:
                raise e

def download_file_from_url(file_url):
    """
    Stream large file download to a string.

    Args:
        file_url (str): The URL to download the file from.
    """
    retries = 3
    decay = 2  # decay factor for wait time between retries

    for i in range(retries):
        try:
            with requests.get(file_url, stream=True) as r:
                r.raise_for_status()
                file_content = ''
                for chunk in r.iter_content(chunk_size=8192, decode_unicode=True): 
                    # if chuck is bytes, decode it to utf-8
                    if not isinstance(chunk, str):
                        chunk = chunk.decode('utf-8')
                    file_content += chunk
            return file_content
        except Exception as e:
            if i < retries - 1:  # no need to wait after the last try
                time.sleep(decay ** i)  # wait time increases with each retry
            else:
                raise e
            
def post_file_to_backend_for_download(file_name, file_content, auth_token):
    """Posts a file to the backend"""
    full_url = get_api_url() + "printers/upload-from-edge/download-request"
    headers = generate_auth_headers(auth_token)
    # get the content type given file name extension (gcode, stl, etc.)
    content_type = "text/plain"
    if (
        file_name.lower().endswith(".stl")
        or file_name.lower().endswith(".obj")
        or file_name.lower().endswith(".3mf")
    ):
        content_type = "application/octet-stream"
    files = {
        "file": (file_name, file_content, content_type),
    }
    try:
        resp = requests.post(
            url=full_url,
            files=files,
            headers=headers,
        )
        # print data from resp
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise e


def inject_auth_key(webrtc_data, json_msg, logger):
    """
    Injects the auth key into the webrtc data.
    """
    if webrtc_data and json_msg and "auth_key" in json_msg:
        webrtc_data["webrtc_data"]["auth_key"] = json_msg["auth_key"]
        logger.info(
            "MattaConnect plugin - injected auth key into webrtc data: %s",
            json_msg["auth_key"],
        )
    return webrtc_data
