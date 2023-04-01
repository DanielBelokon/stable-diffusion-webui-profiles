import modules
import os
import json


class ProfileState:
    settings_path = os.path.join(modules.scripts.basedir(), "profiles_settings.json")
    data = {"profile": "config.json", "profile_list": ["config.json"]}

    def save(self):
        with open(self.settings_path, 'w') as ps_fd:
            json.dump(self.data, ps_fd)

    def load(self):
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'r') as ps_fd:
                self.data = json.load(ps_fd)

    def profile_path(self, profile):
        return profile

    def list(self):
        return self.data["profile_list"]

    def add(self, profile_name):
        if profile_name not in self.data["profile_list"]:
            self.data["profile_list"].append(profile_name)
            self.save()

    def current(self):
        return self.data["profile"]

    def current_path(self):
        return self.profile_path(self.current())

    def set_current(self, profile):
        self.data["profile"] = profile

