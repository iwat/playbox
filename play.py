import configparser
import dropbox
import re
import signal
import sys
from threading import Thread
from random import shuffle
from time import sleep

from playsound import playsound


def disable_ipv6():
    import requests
    requests.packages.urllib3.util.connection.HAS_IPV6 = False


class Player(Thread):

    def __init__(self, files, dbx, callback):
        super().__init__(daemon=True)
        self.files = files
        self.dbx = dbx
        self.index = 0
        self.callback = callback
        self.controller = None

    def run(self):
        while True:
            file = self.files[self.index]
            self.callback(self.index, file.path_lower)

            self.controller = playsound(self.dbx.files_get_temporary_link(file.path_lower).link, block=False)
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


def build_dropbox(config):
    if "oauth_refresh_token" in config["playbox"] is not None:
        dbx = dropbox.Dropbox(
                oauth2_refresh_token=config["playbox"]["oauth_refresh_token"],
                app_key=config["playbox"]["dropbox_app_key"],
                app_secret=config["playbox"]["dropbox_app_secret"])
        dbx.users_get_current_account()
        return dbx
    else:
        auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(
                consumer_key=config["playbox"]["dropbox_app_key"],
                consumer_secret=config["playbox"]["dropbox_app_secret"],
                token_access_type="offline")

        authorize_url = auth_flow.start()
        print("1. Go to: " + authorize_url)
        print("2. Click \"Allow\" (you might have to log in first).")
        print("3. Copy the authorization code.")
        auth_code = input("Enter the authorization code here: ").strip()

        try:
            oauth_result = auth_flow.finish(auth_code)
        except Exception as e:
            print('Error: %s' % (e,))
            exit(1)

        dbx = dropbox.Dropbox(oauth2_access_token=oauth_result.access_token)
        dbx.users_get_current_account()

        config = configparser.ConfigParser()
        config.read("config.ini")
        config["playbox"]["oauth_access_token"] = oauth_result.access_token
        config["playbox"]["oauth_refresh_token"] = oauth_result.refresh_token
        with open("config.ini", "w") as configfile:
            config.write(configfile)

        return dbx


def main(stdscr):
    config = configparser.ConfigParser()
    config.read("config.ini")

    if config["playbox"]["disable_ipv6"] == "true":
        disable_ipv6()

    dbx = build_dropbox(config)
    print("Listing files")

    files = []
    result = dbx.files_list_folder(config["playbox"]["path"])
    files.extend(result.entries)

    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        files.extend(result.entries)

    shuffle(files)
    for idx, file in enumerate(files):
        print(f"{idx}: {file.path_display}")

    prompt = False

    def on_play(ndx, path):
        print(f"\rPlaying {ndx}: {path}")
        if prompt:
            print("Command? ", end='', flush=True)

    player = Player(files, dbx, on_play)
    player.start()

    while True:
        while not player.is_playing():
            sleep(1)
        prompt = True
        command = input("Command? ")
        prompt = False
        if command == "n":
            player.next()
        elif re.match("^[0-9]+$", command) != None:
            player.select(int(command))
        elif command == "q":
            sys.exit(0)


def handler(signum, frame):
    sys.exit(1)


signal.signal(signal.SIGINT, handler)
main(None)
