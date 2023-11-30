import psutil
from datetime import datetime
import requests
import sentry_sdk
import os
from sys import platform

MATTA_OS_ENDPOINT = "https://os.matta.ai/"

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
        path = os.path.join(os.getenv('APPDATA'), 'OctoPrint', 'uploads')
    return os.path.expanduser(path)


def make_timestamp():
    """Generates a timestamp string in the format 'YYYY-MM-DDTHH:MM:SS.sssZ'"""
    dt = datetime.utcnow().isoformat(sep="T", timespec="milliseconds") + "Z"
    return dt


def init_sentry(version):
    sentry_sdk.init(
        dsn="https://8a15383bc2f14c1ca06e4fe5c1788265@o289703.ingest.sentry.io/4504774026592256",
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=0.01,
        release=f"MattaOSLite@{version}",
    )
    
def get_file_from_backend(bucket_file, auth_token):
    """Gets a file from the backend"""
    full_url = get_api_url() + "print-jobs/printer/gcode/uploadfile"
    headers = generate_auth_headers(auth_token)
    data = {"bucket_file": bucket_file}
    try:
        resp = requests.post(
            url=full_url, data=data, headers=headers, timeout=5,
        )
        # print data from resp
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        raise e        # Windows

def inject_auth_key(webrtc_data, json_msg, logger):
    """
    Injects the auth key into the webrtc data.
    """
    if "auth_key" in json_msg:
        webrtc_data["webrtc_data"]["auth_key"] = json_msg["auth_key"]
        logger.debug("MattaConnect plugin - injected auth key into webrtc data.", json_msg["auth_key"])
    return webrtc_data