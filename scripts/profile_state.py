import modules.scripts
import os
import json


class ProfileState:
    settings_path = os.path.join(modules.scripts.basedir(), "profiles_state.json")
    profiles_dir_path = os.path.join(modules.scripts.basedir(), "profiles")
    data = {
            "profile": "Default",
            "profile_list": {
                        "Default": "config.json"
                    }
    }

    def save(self):
        with open(self.settings_path, 'w') as ps_fd:
            json.dump(self.data, ps_fd)

    def load(self):
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'r') as ps_fd:
                self.data = json.load(ps_fd)

    def profile_path(self, profile):
        return self.data["profile_list"][profile]

    def list(self):
        return list(self.data["profile_list"].keys())

    def add(self, profile_name):
        if profile_name not in self.data["profile_list"]:
            if not os.path.exists(self.profiles_dir_path):
                os.mkdir(self.profiles_dir_path)

            self.data["profile_list"][profile_name] = os.path.join(self.profiles_dir_path, profile_name + ".json")
            self.save()

    def current(self):
        return self.data["profile"]

    def current_path(self):
        return self.profile_path(self.current())

    def set_current(self, profile):
        self.data["profile"] = profile
        self.save()

    def exists(self, profile):
        return profile in self.list()

    def remove(self, profile):
        if profile == "Default" or profile == self.current():
            print("Can't delete default or active profile")
            return

        if profile not in self.list():
            return
        path = self.profile_path(profile)
        self.data["profile_list"].pop(profile)
        print("Deleting " + path)
        os.remove(path)
        if self.current() == profile:
            self.set_current("Default")
        self.save()

