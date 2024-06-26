import re
import time
import threading
import requests
import csv
import json
import io
from cachetools import TTLCache
from .utils import (
    get_api_url,
    get_gcode_upload_dir,
    make_timestamp,
    generate_auth_headers,
    SAMPLING_TIMEOUT,
    MATTA_TMP_DATA_DIR,
)
import os
import shutil
from PIL import Image
from .printer import MattaPrinter

class DataEngine:
    def __init__(
        self,
        matta_printer: MattaPrinter,
        settings,
        logger,
    ):
        self._printer = matta_printer
        self._settings = settings
        self._logger = logger
        self.image_count = 0
        self.gcode_path = None
        self.csv_print_log = None
        self.csv_writer = None
        self.csv_path = None
        self.first_layer_end_line = None
        self.first_layer_csv_uploaded = False
        self.upload_attempts = 0
        self.bad_url_cache = TTLCache(maxsize=100, ttl=120)
        self.unsuccessful_image_count = 0
        self.start_data_thread()

    def start_data_thread(self):
        """
        Start the main combined thread for capturing both CSV and images
        """
        self._logger.debug("Setting up main data thread...")
        self.main_data_thread = threading.Thread(target=self.data_thread_loop)
        self.main_data_thread.daemon = True
        self.main_data_thread.start()
        self._logger.debug("Main data thread running.")

    def get_job_dir(self, with_data_dir=True):
        """Gets the directory for the current print job."""
        if self._printer.current_job is not None:
            job_name = self._printer.current_job.replace(":", "-")
            if with_data_dir:
                return os.path.join(MATTA_TMP_DATA_DIR, job_name)
            return job_name
        else:
            return None

    def create_job_dir(self):
        """
        Creates the directory for the current print job.
        Returns the path of the created directory.
        """
        data_path = self.get_job_dir()
        try:
            os.makedirs(data_path)
            self._logger.debug(f"Successfully created job directory at {data_path}")
        except OSError as e:
            self._logger.error(
                f"Failed to create directory - OS Error ({e.errno}): {e.strerror}, Directory: {data_path}"
            )
            self._logger.error(f"Current directory: {os.getcwd()}")
        return data_path

    def reset_job_data(self):
        """
        Reset the job-related data after a print job.
        """
        self.csv_print_log = None
        self.csv_writer = None
        self.first_layer_csv_uploaded = False
        self.first_layer_end_line = None
        try:
            shutil.rmtree(self.get_job_dir())
        except OSError as e:
            pass
        except TypeError as e:
            pass
        self.csv_path = None
        self._printer.new_print_job = True
        self._printer.current_job = None
        self.gcode_path = None
        self.image_count = 0
        self._printer.gcode_line_num_no_comments = None
        self._printer.gcode_cmd = None

    def create_metadata(self):
        temps = self._printer.get_data()["temperature_data"]
        metadata = {
            "count": self.image_count,
            "timestamp": make_timestamp(),
            "flow_rate": self._printer.flow_rate,
            "feed_rate": self._printer.feed_rate,
            "z_offset": self._printer.z_offset,
            "hotend_target": temps["tool0"]["target"],
            "hotend_actual": temps["tool0"]["actual"],
            "bed_target": temps["bed"]["target"],
            "bed_actual": temps["bed"]["actual"],
            "gcode_line_num": self._printer.gcode_line_num_no_comments,
            "gcode_cmd": self._printer.gcode_cmd,
            "nozzle_tip_coords_x": int(self._settings.get(["nozzle_tip_coords_x"])),
            "nozzle_tip_coords_y": int(self._settings.get(["nozzle_tip_coords_y"])),
            "flip_h": self._settings.get(["flip_h"]),
            "flip_v": self._settings.get(["flip_v"]),
            "rotate": self._settings.get(["rotate"]),
            "printer_state": self._printer.get_data()["state"],
        }
        return metadata

    def gcode_upload(self, job_name, gcode_path):
        """
        Uploads G-code files to the specified base URL.

        Args:
            files (dict): A dictionary containing the files to upload.
            headers (dict): Additional headers to include in the request.

        Raises:
            requests.exceptions.RequestException: If an error occurs during the upload.
        """
        self._logger.debug("Posting gcode")
        with open(gcode_path, "rb") as gcode:
            gcode_name = os.path.basename(gcode_path)
            metadata = {
                "name": os.path.splitext(gcode_name)[0],
                "long_name": job_name,
                "gcode_file": gcode_name,
                "start_time": make_timestamp(),
            }
            data = {"data": json.dumps(metadata)}
            files = {
                "gcode_obj": (job_name, gcode, "text/plain"),
            }
            full_url = get_api_url() + "print-jobs/remote/start-job"
            headers = generate_auth_headers(self._settings.get(["auth_token"]))
            try:
                resp = requests.post(
                    url=full_url,
                    data=data,
                    files=files,
                    headers=headers,
                )
                resp.raise_for_status()
            except requests.exceptions.RequestException as e:
                self._logger.error(e)
        # get first layer end line
        self.find_first_layer_end_line(gcode_path)

    def image_upload(self, image):
        """
        Uploads image files to the specified base URL.

        Args:
            files (dict): A dictionary containing the files to upload.
            headers (dict): Additional headers to include in the request.

        Raises:
            requests.exceptions.RequestException: If an error occurs during the upload.
        """
        self._logger.debug("Posting image")
        image_name = f"image_{self.image_count}.png"

        # Load the image using PIL
        pil_image = Image.open(io.BytesIO(image))

        # Flip the image if necessary
        if self._settings.get(["flip_h"]):
            pil_image = pil_image.transpose(Image.FLIP_LEFT_RIGHT)
        if self._settings.get(["flip_v"]):
            pil_image = pil_image.transpose(Image.FLIP_TOP_BOTTOM)
        if self._settings.get(["rotate"]):
            pil_image = pil_image.transpose(Image.ROTATE_90)

        # Convert the PIL image back to bytes
        byte_arr = io.BytesIO()
        pil_image.save(byte_arr, format="PNG")
        image = byte_arr.getvalue()

        metadata = {
            "name": image_name,
            "img_file": image_name,
        }
        metadata.update(self.create_metadata())
        data = {"data": json.dumps(metadata)}
        files = {
            "image_obj": (image_name, image, "image/png"),
        }
        full_url = get_api_url() + "images/print/predict/new-image"
        headers = generate_auth_headers(self._settings.get(["auth_token"]))
        try:
            resp = requests.post(
                url=full_url,
                data=data,
                files=files,
                headers=headers,
                timeout=5,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    def first_layer_upload(self, job_name, gcode_path, csv_path, first_layer_csv_path):
        """
        Sends the first layer csv to the server for analysis.

        Args:
            job_name (str): The name of the print job.
            gcode_path (str): The path to the G-code file.
            csv_path (str): The path to the CSV file.
        
        Raises:
            requests.exceptions.RequestException: If an error occurs during the upload.

        """
        self._logger.debug(csv_path)
        with open(csv_path, "rb") as csv:
            gcode_name = os.path.basename(gcode_path)
            csv_name = os.path.basename(first_layer_csv_path)
            metadata = {
                "name": os.path.splitext(gcode_name)[0],
                "long_name": job_name,
                "first_layer_csv_file": csv_name,
            }
            data = {"data": json.dumps(metadata)}
            files = {
                "csv_obj": (first_layer_csv_path, csv, "text/csv"),
            }
            full_url = get_api_url() + "print-jobs/remote/first-layer-upload"
            headers = generate_auth_headers(self._settings.get(["auth_token"]))
            retries = 3
            decay = 2  # decay factor for wait time between retries

            for i in range(retries):
                try:
                    resp = requests.post(
                        url=full_url,
                        data=data,
                        files=files,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    break  # if the request is successful, we break the loop
                except requests.exceptions.RequestException as e:
                    if i < retries - 1:  # no need to wait after the last try
                        time.sleep(decay ** i)  # wait time increases with each retry
                    else:
                        self._logger.error(e)
                        raise e

    def finished_upload(self, job_name, gcode_path, csv_path):
        """
        Notifies the server that the print job has finished.

        Args:
            job_name (str): The name of the print job.

        Raises:
            requests.exceptions.RequestException: If an error occurs during the upload.
        """
        self._logger.debug(csv_path)
        with open(csv_path, "rb") as csv:
            gcode_name = os.path.basename(gcode_path)
            csv_name = os.path.basename(csv_path)
            metadata = {
                "name": os.path.splitext(gcode_name)[0],
                "long_name": job_name,
                "csv_file": csv_name,
                "end_time": make_timestamp(),
            }
            data = {"data": json.dumps(metadata)}
            files = {
                "csv_obj": (csv_name, csv, "text/csv"),
            }
            full_url = get_api_url() + "print-jobs/remote/end-job"
            headers = generate_auth_headers(self._settings.get(["auth_token"]))
            import time

            retries = 3
            decay = 2  # decay factor for wait time between retries

            for i in range(retries):
                try:
                    resp = requests.post(
                        url=full_url,
                        data=data,
                        files=files,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    break  # if the request is successful, we break the loop
                except requests.exceptions.RequestException as e:
                    if i < retries - 1:  # no need to wait after the last try
                        time.sleep(decay ** i)  # wait time increases with each retry
                    else:
                        self._logger.error(e)
                        raise e

    def is_new_job(self):
        """
        Checks if a new print job has started and performs necessary setup tasks.

        Returns:
            bool: True if a new job has started, False otherwise.
        """
        if self._printer.has_job():
            # self._logger.debug(f"Has job: {self._printer.current_job}")
            if self._printer.new_print_job:
                self._logger.debug("New job.")
                self._printer.new_print_job = False
                self._printer.current_job = self._printer.make_job_name()
                self._logger.debug(f"New job: {self._printer.current_job}")
                try:
                    self.setup_print_log()
                    self.gcode_upload(self._printer.current_job, self.gcode_path)
                except Exception as e:
                    self._logger.error(
                        f"Failed to set up data collection for print job: {e}"
                    )
            return True

        elif self._printer.is_operational():
            if self._printer.just_finished():
                self._logger.debug("Just finished a print job.")
                try:
                    self.cleanup_print_log()
                    self._logger.debug("Print log cleaned up.")
                    self.finished_upload(
                        self._printer.current_job, self.gcode_path, self.csv_path
                    )
                    self._logger.debug("Posted!")
                    self.finished = True
                    self._printer.finished = True
                except Exception as e:
                    self._logger.error(f"Failed to finish print job: {e}")
                    self.upload_attempts += 1
                    if self.upload_attempts > 3:
                        self.reset_job_data()
                        self.upload_attempts = 0
                        self.finished = True
                        self._printer.finished = True

            self.reset_job_data()
        return False

    def setup_print_log(self):
        """
        Set up the print log file and start the image thread.
        """
        job_dir = self.create_job_dir()
        self.csv_path = os.path.join(job_dir, "print_log.csv")
        self.first_layer_csv_path = os.path.join(job_dir, "first_layer.csv")
        self.gcode_path = os.path.join(
            get_gcode_upload_dir(),
            self._printer.get_current_job()["file"]["path"],
        )
        self._logger.debug("G-code file copied.")
        try:
            self.csv_print_log = open(self.csv_path, "w")
            self.csv_writer = csv.writer(self.csv_print_log, delimiter=",")
            self.csv_writer.writerow(self.csv_headers())
            self.csv_print_log.flush()
        except IOError as e:
            self._logger.error(f"Failed to open print log file: {e}")
            self.csv_print_log = None
            self.csv_writer = None

    def cleanup_print_log(self):
        """
        Clean up the print log file and image thread after the print has finished.
        """
        try:
            self.csv_print_log.flush()
            self.csv_print_log.close()
        except AttributeError:
            self._logger.error("CSV print log was never made...")
        except Exception as e:
            self._logger.error(f"Failed to close print log file: {e}")

    def find_first_layer_end_line(self, gcode_path):
        """
        Find the line number of the first layer end in the G-code file.

        Args:
            gcode_path (str): The path to the G-code file.

        Returns:
            int: The line number of the first layer end.
        """
        with open(gcode_path, "r") as gcode:
            gcode_lines = gcode.readlines()
            # find lines that are not comments and have E in them
            e_lines = []
            z_change_lines = []

            i=0
            for line in gcode_lines:
                if line.startswith(";") or line == "\n":
                    continue
                i+=1
                if "E" in line:
                    e_lines.append(i)
                if "Z" in line:
                    # regex string after Z and before space or the end of the line
                    regex = r"Z(-?\d*\.?\d+)"
                    z_change = re.search(regex, line)
                    if z_change:
                        z_change_lines.append((i, float(z_change.group(1))))
                      
            self._logger.info(f"Z change lines length: {len(z_change_lines)}")
            self._logger.info(f"E lines length: {len(e_lines)}")
            self._logger.info(f"Z change lines: {z_change_lines[:20]}")

            # find the first layer start extrusion line if Es are in 8 out of 10 consecutive lines
            consecutive_e_lines = 0
            first_layer_start_line = None
            threshold = 10
            for threshold in range(10, 20, 1):
                for i, line in enumerate(e_lines):
                    if i + 8 >= len(e_lines):
                        break
                    if e_lines[i + 8] - e_lines[i] < threshold:
                        first_layer_start_line = e_lines[i]
                        break
                if first_layer_start_line is not None:

                    break
            
            # find what Z value is at the first layer start line
            first_layer_start_z = None
            for line in z_change_lines:
                if line[0] > first_layer_start_line:
                    first_layer_end_line = line[0]
                    break
                first_layer_start_z = line[1]
                
            self._logger.info(f"First layer start line: {first_layer_start_line}")
            self._logger.info(f"First layer start Z: {first_layer_start_z}")
            self._logger.info(f"First layer end line: {first_layer_end_line}")

            self.first_layer_end_line = first_layer_end_line
            return
                    
            

    def csv_headers(self):
        """Returns a list of CSV headers used for data collection."""
        return [
            "count",
            "timestamp",
            "flow_rate",
            "feed_rate",
            "z_offset",
            "target_hotend",
            "hotend",
            "target_bed",
            "bed",
            "gcode_line_num_no_comments",
            "gcode_cmd",
            "nozzle_tip_coords_x",
            "nozzle_tip_coords_y",
            "flip_h",
            "flip_v",
            "rotate",
        ]

    def csv_data_row(self):
        """Fetches data and returns a list for populating a row of a CSV."""
        temps = self._printer.get_data()["temperature_data"]
        row = [
            self.image_count,
            make_timestamp(),
            self._printer.flow_rate,
            self._printer.feed_rate,
            self._printer.z_offset,
            temps["tool0"]["target"],
            temps["tool0"]["actual"],
            temps["bed"]["target"],
            temps["bed"]["actual"],
            self._printer.gcode_line_num_no_comments,
            self._printer.gcode_cmd,
            int(self._settings.get(["nozzle_tip_coords_x"])),
            int(self._settings.get(["nozzle_tip_coords_y"])),
            self._settings.get(["flip_h"]),
            self._settings.get(["flip_v"]),
            self._settings.get(["rotate"]),
        ]
        return row

    def generate_auth_headers(self):
        """
        Generates the authentication headers for API requests.

        Returns:
            dict: The authentication headers.
        """
        return {"Authorization": self._settings.get(["auth_token"])}

    def update_csv(self):
        try:
            self.csv_writer.writerow(self.csv_data_row())
            self.csv_print_log.flush()
        except Exception as e:
            self._logger.error(e)
        
        # check if first layer is done
        buffer_length = 8
        
        if self.first_layer_csv_uploaded == False and int(self._printer.gcode_line_num_no_comments) > self.first_layer_end_line + buffer_length:
            self.first_layer_csv_uploaded = True
            self.first_layer_upload(self._printer.current_job, self.gcode_path, self.csv_path, self.first_layer_csv_path)

    def update_image(self):
        try:
            if self._settings.get(["snapshot_url"]) not in self.bad_url_cache:
                resp = requests.get(self._settings.get(["snapshot_url"]), stream=True)
                if resp.status_code != 200:
                    raise Exception("Unsuccessful request, status code: " + str(resp.status_code))
            else:
                raise Exception("Bad URL")
            self.unsuccessful_image_count = 0
            self.image_upload(resp.content)
            self.image_count += 1
        except Exception as e:
            if "unsuccessful request" in str(e).lower():
                self._logger.info("Unsuccessful request image request.")
                self.unsuccessful_image_count += 1
                if self.unsuccessful_image_count > 3:
                    self._logger.info("Maximum failed image requests reached, blacklisting snapshot URL for 2 minutes.")
                    self.bad_url_cache[self._settings.get(["snapshot_url"])] = True

    def data_thread_loop(self):
        """
        Main loop for collecting data:
        - to populate the CSV log
        - to capture image frames

        This loop runs at a rate determined by SAMPLING_TIMEOUT.

        Returns:
            None
        """
        self._logger.debug("Starting main data loop method.")
        old_time = time.perf_counter()
        time_buffer = 0.0

        while True:
            current_time = time.perf_counter()
            if (
                self.is_new_job()
                and (current_time - old_time) > SAMPLING_TIMEOUT - time_buffer
            ):
                time_buffer = max(0, current_time - old_time - SAMPLING_TIMEOUT)
                old_time = current_time
                self.update_csv()
                self.update_image()
            time.sleep(0.1)  # slow things down to 100ms to run other threads
