import re
import os
import base64
from .utils import get_file_from_backend, make_timestamp
from octoprint.filemanager import FileDestinations
from octoprint.filemanager.util import StreamWrapper, DiskFileWrapper

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
            self._logger.error(f"Regex Error in virtual printer: {e}")
        except Exception as e:
            self._logger.error(f"General Error in virtual printer: {e}")

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
                destination = FileDestinations.SDCARD if json_msg["files"]["loc"] == "sd" else FileDestinations.LOCAL
                file_content = base64.b64decode(json_msg["files"]["content"])
                content_string = file_content.decode("utf-8")

                class FileObjectWithSaveMethod:
                    def save(self, destination_path):
                        with open(destination_path, 'w') as file:
                            file.write(str(content_string))

                self._file_manager.add_file(
                    path=json_msg["files"]["file"],
                    file_object=FileObjectWithSaveMethod(),
                    destination=destination,
                    allow_overwrite=True,
                )
            elif json_msg["files"]["cmd"] == "upload_big":
                destination = FileDestinations.SDCARD if json_msg["files"]["loc"] == "sd" else FileDestinations.LOCAL
                bucket_file = json_msg["files"]["content"]
                
                # call backend to get file
                response = get_file_from_backend(bucket_file, self._settings.get(["auth_token"]))

                class FileObjectWithSaveMethod:
                    def save(self, destination_path):
                        with open(destination_path, 'w') as file:
                            file.write(response)

                self._file_manager.add_file(
                    path=json_msg["files"]["file"],
                    file_object=FileObjectWithSaveMethod(),
                    destination=destination,
                    allow_overwrite=True,
                )
            elif json_msg["files"]["cmd"] == "delete":
                destination = FileDestinations.SDCARD if json_msg["files"]["loc"] == "sd" else FileDestinations.LOCAL
                if json_msg["files"]["type"] == "folder":
                    self._file_manager.remove_folder(path=json_msg["files"]["file"], destination=destination)
                else: 
                    self._file_manager.remove_file(path=json_msg["files"]["file"], destination=destination)
            elif json_msg["files"]["cmd"] == "new_folder":
                destination = FileDestinations.SDCARD if json_msg["files"]["loc"] == "sd" else FileDestinations.LOCAL
                self._file_manager.add_folder(
                    path=json_msg["files"]["folder"],
                    destination=destination,
                    ignore_existing=True,
                    display=None,
                )
        elif "gcode" in json_msg:
            if json_msg["gcode"]["cmd"] == "send":
                self._printer.commands(commands=json_msg["gcode"]["lines"])