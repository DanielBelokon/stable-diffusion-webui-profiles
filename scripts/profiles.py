import json
import os

import gradio as gr

from modules import shared
from modules.shared import opts, OptionInfo
from modules import scripts
from scripts.profile_state import profiles_settings_data, profiles_settings_path


def on_ui_settings():
    section = ("profiles", "Profiles")


def profile_update(profile_name):
    if not os.path.exists(profile_name):
        print("Profile doesn't exist - cloning current config...")
        profile_add(profile_name)

    else:
        opts.load(profile_name)

    shared.config_filename = profile_name
    profiles_settings_data["profile"] = profile_name
    with open(profiles_settings_path, 'w') as file:
        json.dump(profiles_settings_data, file)

    shared.state.interrupt()
    shared.state.need_restart = True


def profile_add(profile_name):
    if profile_name == "":
        print("Config Name can't be empty")
    else:
        if not os.path.exists(profile_name):
            opts.save(profile_name)
        else:
            print("Found existing profile, updating list...")
        if profile_name not in profiles_settings_data["profile_list"]:
            profiles_settings_data["profile_list"].append(profile_name)
            with open(profiles_settings_path, 'w') as file:
                json.dump(profiles_settings_data, file)

    return gr.Radio.update(choices=profiles_settings_data["profile_list"])


def initialize_profile():
    global profiles_settings_data
    if os.path.exists(profiles_settings_path):
        with open(profiles_settings_path, "r", encoding="utf8") as profiles_settings_file:
            print("Preloading profile settings... ")
            profiles_settings_data = json.load(profiles_settings_file)

    print("Profile set to " + profiles_settings_data["profile"])
    shared.config_filename = profiles_settings_data["profile"]
    opts.load(shared.config_filename)


def change_preview(profile):
    configfile = []
    with open(profile, 'r', encoding="utf8") as file:
        configfile = json.load(file)

    return gr.Json.update(value=configfile)


def add_tab():
    global profiles_settings_data
    if os.path.exists(profiles_settings_path):
        with open(profiles_settings_path, "r", encoding="utf8") as profiles_settings_file:
            profiles_settings_data = json.load(profiles_settings_file)

    if profiles_settings_data:
        profile_list = profiles_settings_data["profile_list"]
        cur_profile = profiles_settings_data["profile"]
    else:
        profile_list = ["config.json"]
        cur_profile = "config.json"

    with open(cur_profile, 'r', encoding="utf8") as file:
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
            fn=profile_update,
            _js="reload_ui_profile",
            inputs=[profile_radio],
            outputs=[]
        )

        add_profile.click(
            fn=profile_add,
            inputs=[new_profile_input],
            outputs=[profile_radio]
        )

        profile_radio.change(fn=change_preview, inputs=profile_radio, outputs=profile_display)

    return [(tab, "Profiles", "profiles")]


scripts.script_callbacks.on_ui_tabs(add_tab)
# scripts.script_callbacks.on_ui_settings(on_ui_settings)
scripts.script_callbacks.on_before_ui(initialize_profile)

