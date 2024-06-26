import re
import inspect
import os
from concurrent.futures import ThreadPoolExecutor

from .worker import download_file_and_print, upload_file_to_backend
from .utils import get_file_from_url, make_timestamp, post_file_to_backend_for_download, download_file_from_url
from octoprint.filemanager import FileDestinations


class MattaPrinter:
    """Virtual Printer class for storing current parameters"""

    def __init__(self, printer, logger, file_manager, settings, *args, **kwargs):
        self._printer = printer
        self._logger = logger
        self._file_manager = file_manager
        self._settings = settings
        self.printing = False  # True when print job is running
        self.finished = True  # True for loop when print job has just finished

        self.flow_rate = 100  # in percent
        self.feed_rate = 100  # in percent
        self.z_offset = 0.0  # in mm
        self.hotend_temp_offset = 0.0  # in degrees C
        self.bed_temp_offset = 0.0  # in degrees C

        self.gcode_line_num_no_comments = 0
        self.gcode_cmd = ""

        self.new_print_job = False
        self.current_job = None

        # Initialize the ThreadPoolExecutor
        self.executor = ThreadPoolExecutor()

    def reset(self):
        """Resets all parameters to default values"""
        self.flow_rate = 100
        self.feed_rate = 100
        self.z_offset = 0.0
        self.hotend_temp_offset = 0.0
        self.bed_temp_offset = 0.0

    def set_flow_rate(self, new_flow_rate):
        """
        Sets the flow rate of the printer.

        Args:
            new_flow_rate (int): The new flow rate in percent.

        """
        if new_flow_rate > 0:
            self.flow_rate = new_flow_rate

    def set_feed_rate(self, new_feed_rate):
        """
        Sets the feed rate of the printer.

        Args:
            new_feed_rate (int): The new feed rate in percent.

        """
        if new_feed_rate > 0:
            self.feed_rate = new_feed_rate

    def set_z_offset(self, new_z_offset):
        """
        Sets the Z offset of the printer.

        Args:
            new_z_offset (float): The new Z offset value.

        """
        self.z_offset = new_z_offset

    def connected(self):
        """
        Checks if the printer is connected.

        Returns:
            bool: True if the printer is connected, False otherwise.
        """
        get_current_connection = self._printer.get_current_connection()
        (connection_string, port, baudrate, printer_profile) = get_current_connection
        if port is None or baudrate is None:
            return False
        return True

    def get_data(self):
        """
        Retrieves data about the printer's current state, temperatures, and other information.

        Returns:
            dict: A dictionary containing the printer's state, temperature data, and printer data.
        """
        data = {
            "state": self._printer.get_state_string(),
            "temperature_data": self._printer.get_current_temperatures(),
            "printer_data": self._printer.get_current_data(),
        }
        return data

    def parse_line_for_updates(self, line):
        """
        Parses a line for updates to printer parameters and applies them.

        Args:
            line (str): The line of text to parse.

        """
        try:
            if "Flow" in line:
                flow_regex = re.compile(r"Flow: (\d+)\%")
                match = flow_regex.search(line)
                new_flow_rate = int(match.group(1))
                self.set_flow_rate(new_flow_rate)
            elif "Feed" in line:
                feed_regex = re.compile(r"Feed: (\d+)\%")
                match = feed_regex.search(line)
                new_feed_rate = int(match.group(1))
                self.set_feed_rate(new_feed_rate)
            elif "Probe Z Offset" in line:
                z_offset_regex = re.compile(r"Probe Z Offset: (-?(\d+)((\.\d+)?))")
                match = z_offset_regex.search(line)
                new_z_offset = float(match.group(1))
                self.set_z_offset(new_z_offset)
        except re.error as e:
            self._logger.debug(f"Regex Error in virtual printer: {e}")
        except Exception as e:
            self._logger.debug(f"General Error in virtual printer: {e}")

    def get_current_job(self):
        """Retrieves information on the current print job"""
        return self._printer.get_current_job()

    def make_job_name(self):
        """Generates a job name string in the format 'filename_timestamp'"""
        job_details = self.get_current_job()
        filename, _ = os.path.splitext(job_details["file"]["name"])
        dt = make_timestamp()
        return f"{filename}_{dt}"

    def is_operational(self):
        """Checks if the printer is operational"""
        return self._printer.is_ready() or self._printer.is_operational()

    def just_finished(self):
        """Checks if the state has turned from printing to finished"""
        if self.printing == False and self.finished == False:
            return True
        return False

    def has_job(self):
        """Checks if the printer currently has a print job."""
        if (
            self._printer.is_printing()
            or self._printer.is_paused()
            or self._printer.is_pausing()
        ):
            self.printing = True
            self.finished = False
            return True
        self.extruding = False
        self.printing = False
        return False

    def handle_cmds(self, json_msg):
        """
        Handles different commands received as JSON messages.

        Args:
            json_msg (dict): The JSON message containing the command.

        """
        if "motion" in json_msg:
            if json_msg["motion"]["cmd"] == "home":
                try:
                    self._printer.home(axes=json_msg["motion"]["axes"])
                except KeyError:
                    self._printer.home()
            elif json_msg["motion"]["cmd"] == "move":
                self._printer.jog(
                    axes=json_msg["motion"]["axes"],
                    relative=True,
                )
            elif json_msg["motion"]["cmd"] == "extrude":
                self._printer.extrude(amount=float(json_msg["motion"]["value"]))
            elif json_msg["motion"]["cmd"] == "retract":
                self._printer.extrude(amount=float(json_msg["motion"]["value"]))
        elif "temperature" in json_msg:
            if json_msg["temperature"]["cmd"] == "temperature":
                self._printer.set_temperature(
                    heater=json_msg["temperature"]["heater"],
                    value=float(json_msg["temperature"]["value"]),
                )
        elif "execute" in json_msg:
            if json_msg["execute"]["cmd"] == "pause":
                self._printer.pause_print()
            elif json_msg["execute"]["cmd"] == "resume":
                self._printer.resume_print()
            elif json_msg["execute"]["cmd"] == "cancel":
                self._printer.cancel_print()
            elif json_msg["execute"]["cmd"] == "toggle":
                self._printer.toggle_pause_print()
            elif json_msg["execute"]["cmd"] == "connect":
                self._printer.connect()
        elif "files" in json_msg:
            if json_msg["files"]["cmd"] == "print":
                on_sd = True if json_msg["files"]["loc"] == "sd" else False
                self._printer.select_file(
                    json_msg["files"]["file"], sd=on_sd, printAfterSelect=True
                )
            elif json_msg["files"]["cmd"] == "select":
                on_sd = True if json_msg["files"]["loc"] == "sd" else False
                self._printer.select_file(
                    json_msg["files"]["file"], sd=on_sd, printAfterSelect=False
                )
            elif json_msg["files"]["cmd"] == "upload":
                # Download the file from the URL and save it to the local file system
                destination = (
                    FileDestinations.SDCARD
                    if json_msg["files"]["loc"] == "sd"
                    else FileDestinations.LOCAL
                )
                file_url = json_msg["files"]["url"]

                # Get the signature of the add_file method
                sig = inspect.signature(self._file_manager.add_file)

                # Check if 'destination' or 'location' are in the parameters
                has_destination = 'destination' in sig.parameters
                has_location = 'location' in sig.parameters

                json_file = json_msg["files"]
                
                # call the download_file_and_print function
                # in new thread and do not block the main thread
                
                self.executor.submit(
                    download_file_and_print,
                    file_url,
                    destination,
                    sig,
                    json_file,
                    self._file_manager,
                    self._printer,
                )

            elif json_msg["files"]["cmd"] == "delete":
                destination = (
                    FileDestinations.SDCARD
                    if json_msg["files"]["loc"] == "sd"
                    else FileDestinations.LOCAL
                )
                if json_msg["files"]["type"] == "folder":
                    self.executor.submit(
                        self._file_manager.remove_folder,
                        path=json_msg["files"]["folder"],
                        location=destination,
                    )
                else:
                    self.executor.submit(
                        self._file_manager.remove_file,
                        path=json_msg["files"]["file"],
                        location=destination,
                    )
            elif json_msg["files"]["cmd"] == "new_folder":
                destination = (
                    FileDestinations.SDCARD
                    if json_msg["files"]["loc"] == "sd"
                    else FileDestinations.LOCAL
                )
                self._file_manager.add_folder(
                    path=json_msg["files"]["folder"],
                    destination=destination,
                    ignore_existing=True,
                    display=None,
                )
            elif json_msg["files"]["cmd"] == "download":
                destination = (
                    FileDestinations.SDCARD
                    if json_msg["files"]["loc"] == "sd"
                    else FileDestinations.LOCAL
                )
                full_path = self._file_manager.path_on_disk(
                    destination, json_msg["files"]["file"]
                )
                self.executor.submit(
                    upload_file_to_backend,
                    full_path,
                    self._settings.get(["auth_token"]),
                )
        elif "gcode" in json_msg:
            if json_msg["gcode"]["cmd"] == "send":
                self._printer.commands(commands=json_msg["gcode"]["lines"])
