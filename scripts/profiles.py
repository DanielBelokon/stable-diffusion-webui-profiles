import json
import os

import gradio as gr

from modules import shared
from modules.shared import opts, OptionInfo
from modules import scripts
from scripts.profile_state import ProfileState


class ConfigProfiles:

    def __init__(self):
        self.ps = ProfileState()

    def on_ui_settings(self):
        section = ("profiles", "Profiles")

    def profile_update(self, profile_name):
        if not os.path.exists(profile_name):
            self.ps.add(profile_name)

        self.ps.set_current(profile_name)

        # Load new options file and set the new config "filename" (used for saving elsewhere)
        opts.load(self.ps.current_path())
        shared.config_filename = self.ps.current_path()

        self.ps.save()

        # Restart webui
        shared.state.interrupt()
        shared.state.need_restart = True

    def profile_add(self, profile_name):
        if profile_name == "":
            print("Config Name can't be empty")
        else:
            if not self.ps.exists(profile_name):
                self.ps.add(profile_name)
            else:
                print("Profile already exists")

            if not os.path.exists(self.ps.profile_path(profile_name)):
                opts.save(self.ps.profile_path(profile_name))
            else:
                print("Found matching config file, added to profile index")

        return gr.Radio.update(choices=self.ps.list())

    def initialize_profile(self):
        self.ps.load()
        print("Profile set to " + self.ps.current())
        shared.config_filename = self.ps.current_path()
        opts.load(shared.config_filename)

    def change_preview(self, profile):
        configfile = []
        with open(self.ps.profile_path(profile), 'r', encoding="utf8") as file:
            configfile = json.load(file)

        return gr.Json.update(value=configfile)

    def add_tab(self):
        self.ps.load()

        if self.ps.data:
            profile_list = self.ps.list()
            cur_profile = self.ps.current()
        else:
            profile_list = ["config.json"]
            cur_profile = "config.json"

        with open(self.ps.profile_path(cur_profile), 'r', encoding="utf8") as file:
            configfile = json.load(file)

        with gr.Blocks(analytics_enabled=False) as tab:
            gr.Markdown("# Config Profiles ")
            gr.Markdown("### Current Profile: " + cur_profile)
            with gr.Column(variant='panel', scale=1):
                with gr.Row(variant='panel').style(equal_height=True):
                    with gr.Row():
                        profile_radio = gr.Radio(label="Profiles", choices=profile_list, value=cur_profile)
                        apply_profile = gr.Button("Apply", elem_id="profile_apply", variant='primary')
                with gr.Row(variant='panel').style(equal_height=True):
                    with gr.Row():
                        new_profile_input = gr.Textbox("", placeholder="new-config.json", label="New Profile Name")
                        # new_profile_base = gr.Radio(label="Profiles", choices=["Selected", "Current", "Default"], value="Current")
                        add_profile = gr.Button("Add", elem_id="profile_add")
            with gr.Column(scale=3):
                profile_display = gr.Json(value=configfile)

            apply_profile.click(
                fn=self.profile_update,
                _js="reload_ui_profile",
                inputs=[profile_radio],
                outputs=[]
            )

            add_profile.click(
                fn=self.profile_add,
                inputs=[new_profile_input],
                outputs=[profile_radio]
            )

            profile_radio.change(fn=self.change_preview, inputs=profile_radio, outputs=profile_display)

        return [(tab, "Profiles", "profiles")]


conprof = ConfigProfiles()

scripts.script_callbacks.on_ui_tabs(conprof.add_tab)
# scripts.script_callbacks.on_ui_settings(on_ui_settings)
scripts.script_callbacks.on_before_ui(conprof.initialize_profile)

