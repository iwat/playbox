import configparser
import json
import re
import requests
from threading import Thread
from random import shuffle
from time import sleep

from playsound import playsound


def disable_ipv6():
    import requests.packages.urllib3.util.connection as urllib3_cn
    requests.packages.urllib3.util.connection.HAS_IPV6 = False


class Player(Thread):

    def __init__(self, files, dropbox):
        super().__init__(daemon=True)
        self.files = files
        self.dropbox = dropbox
        self.index = 0
        self.controller = None

        for idx, file in enumerate(files):
            print(f"{idx}: {file['path_display']}")

    def run(self):
        while True:
            file = self.files[self.index]
            print(f"Playing {self.index}: {file['path_lower']}")
            self.controller = playsound(self.dropbox.get_temp_link(file["path_lower"]), block=False)
            sleep(1)
            while not self.controller.is_concluded():
                sleep(1)

            self.index += 1
            if self.index >= len(self.files):
                self.index = 0

    def is_playing(self):
        return self.controller is not None and not self.controller.is_concluded()

    def select(self, index):
        if index >= len(self.files):
            print("Out of range")
        else:
            self.index = index-1
            self.controller.stop()

    def next(self):
        if self.controller is not None:
            self.controller.stop()


class Dropbox:

    def __init__(self, token):
        self.token = token

    def list_files(self, path):
        payload = {
            "path": path,
            "recursive": False,
            "include_media_info": False,
            "include_deleted": False,
            "include_has_explicit_shared_members": False,
            "include_mounted_folders": True,
            "include_non_downloadable_files": True,
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        resp = requests.post("https://api.dropboxapi.com/2/files/list_folder",
                             headers=headers, data=json.dumps(payload))
        return resp.json()["entries"]

    def get_temp_link(self, path_lower: str) -> str:
        payload = {"path": path_lower}
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        resp = requests.post("https://api.dropboxapi.com/2/files/get_temporary_link",
                             headers=headers, data=json.dumps(payload))
        resp_body = resp.json()
        return resp_body["link"]


def main(stdscr):
    config = configparser.ConfigParser()
    config.read("config.ini")

    if config["playbox"]["disable_ipv6"] == "true":
        disable_ipv6()

    dropbox = Dropbox(config["playbox"]["token"])
    print("Listing files")

    files = dropbox.list_files(config["playbox"]["path"])
    shuffle(files)

    player = Player(files, dropbox)
    player.start()

    while True:
        while not player.is_playing():
            sleep(1)
        command = input("Command?")
        if command == "n":
            player.next()
        elif re.match("^[0-9]+$", command) != None:
            player.select(int(command))


main(None)
