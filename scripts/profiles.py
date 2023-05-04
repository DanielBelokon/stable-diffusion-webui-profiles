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
        self.display_options = shared.Options()
        self.settings_components = {}

    def profile_update(self, profile_name):
        if not os.path.exists(profile_name):
            self.ps.add(profile_name)

        self.ps.set_current(profile_name)

        # Load new options file and set the new config "filename" (used for saving elsewhere)
        opts.load(self.ps.current_path())
        shared.config_filename = self.ps.current_path()

        self.ps.save()

        # Restart webui (should work on vlad's auto)
        try:
            shared.restart_server(restart=True)
        except:
            shared.state.need_restart = True
            shared.state.interrupt()

    def profile_add(self, profile_name, image_output_dir=""):
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

        self.apply_overrides(profile_name, image_output_dir)

        return gr.Radio.update(choices=self.ps.list()), gr.Radio.update(choices=self.ps.list())

    def profile_delete(self, profile_name):
        self.ps.remove(profile_name)
        return gr.Radio.update(choices=self.ps.list()), gr.Radio.update(choices=self.ps.list(), value=None)

    def apply_overrides(self, profile_name, image_output_dir):
        if image_output_dir == "":
            return

        tmp_opts = shared.Options()
        tmp_opts.load(self.ps.profile_path(profile_name))
        tmp_opts.outdir_samples = "" if tmp_opts.outdir_samples == "" else image_output_dir + "/images"
        tmp_opts.outdir_txt2img_samples = image_output_dir + "/txt2img-images"
        tmp_opts.outdir_img2img_samples = image_output_dir + "/img2img-images"
        tmp_opts.outdir_extras_samples = image_output_dir + "/extras-images"
        tmp_opts.outdir_grids = "" if tmp_opts.outdir_grids == "" else image_output_dir + "/grids"
        tmp_opts.outdir_txt2img_grids = image_output_dir + "/txt2img-grids"
        tmp_opts.outdir_img2img_grids = image_output_dir + "/img2img-grids"
        tmp_opts.save(self.ps.profile_path(profile_name))

    def initialize_profile(self):
        self.ps.load()
        if os.path.exists(self.ps.current_path()):
            print("Profile set to " + self.ps.current())
        else:
            print("Set profile not found, reverting to default")
            self.ps.set_current("Default")

        shared.config_filename = self.ps.current_path()
        if os.path.exists(self.ps.current_path()):
            opts.load(shared.config_filename)
        else:
            opts.save(self.ps.current_path())

# *********************************************
#               Display stuff
# *********************************************
    def save_profile_config(self, profile):
        print("Saving to " + self.ps.profile_path(profile))
        self.display_options.save(self.ps.profile_path(profile))

    def set_display_setting(self, key, value):
        self.display_options.set(key, value)

    def create_settings_display(self):
        previous_section = None
        current_tab = None
        current_row = None
        gr.Markdown(value="# These settings will only apply to the selected profile ")

        # Basically copied from ui.py, creates settings tab with current selected profile (display_options) data
        with gr.Tabs():
            for i, (key, item) in enumerate(self.display_options.data_labels.items()):
                section_must_be_skipped = item.section[0] is None
                if previous_section != item.section and not section_must_be_skipped:
                    elem_id, text = item.section

                    if current_tab is not None:
                        current_row.__exit__()
                        current_tab.__exit__()

                    gr.Group()
                    current_tab = gr.TabItem(elem_id="p_settings_{}".format(elem_id), label=text, open=False)
                    current_tab.__enter__()
                    current_row = gr.Column(variant='compact')
                    current_row.__enter__()

                    previous_section = item.section

                if not section_must_be_skipped:
                    info = self.display_options.data_labels[key]
                    t = type(info.default)

                    args = info.component_args() if callable(info.component_args) else info.component_args

                    if info.component is not None:
                        comp = info.component
                    elif t == str:
                        comp = gr.Textbox
                    elif t == int:
                        comp = gr.Number
                    elif t == bool:
                        comp = gr.Checkbox
                    else:
                        raise Exception(f'bad options item type: {str(t)} for key {key}')

                    elem_id = "p_setting_" + key
                    with gr.Row():
                        key_comp = gr.Textbox(visible=False, value=key)
                        value = self.display_options.data[key] if key in self.display_options.data else self.display_options.data_labels[key].default
                        self.settings_components[key] = comp(label=info.label, value=value, elem_id=elem_id, **(args or {}))
                        self.settings_components[key].change(fn=self.set_display_setting, inputs=[key_comp, self.settings_components[key]], outputs=[])
            if current_tab is not None:
                current_row.__exit__()
                current_tab.__exit__()
            gr.Group()
            current_tab = gr.TabItem(elem_id="p_settings_extensions", label="Extensions", open=False)
            current_tab.__enter__()
            current_row = gr.Column(variant='compact')
            current_row.__enter__()

            # Create and populate extensions tab
            with gr.Row():
                from modules import extensions
                self.settings_components["enabled_extensions"] = gr.CheckboxGroup(choices=[ext.name for ext in extensions.extensions],
                                                                                  value=[ext.name for ext in extensions.extensions if ext.name not in self.display_options.disabled_extensions],
                                                                                  label="Enabled Extensions")

            self.settings_components["enabled_extensions"].change(
                fn=lambda en_list: self.display_options.set("disabled_extensions", [ext for ext in self.settings_components["enabled_extensions"].choices if ext not in en_list]),
                inputs=[self.settings_components["enabled_extensions"]],
                outputs=[]
            )

    def display_update_components(self, profile):
        self.display_options.load(self.ps.profile_path(profile))
        updated_components_fucking_gradio = []
        for key, comp in self.settings_components.items():
            # "disabled extensions" saved instead (for whatever reason?), we do it outside the loop
            if key == "enabled_extensions":
                continue
            updated_components_fucking_gradio.append(comp.update(value=self.display_options.data[key] if key in self.display_options.data else self.display_options.data_labels[key].default))


        from modules import extensions
        updated_components_fucking_gradio.append(gr.CheckboxGroup.update(value=[ext.name for ext in extensions.extensions if ext.name not in self.display_options.disabled_extensions]))

        return updated_components_fucking_gradio

    def add_tab(self):
        self.ps.load()

        if self.ps.data:
            profile_list = self.ps.list()
            cur_profile = self.ps.current()
        else:
            profile_list = {"Default": "config.json"}
            cur_profile = "Default"
        if os.path.exists(self.ps.current_path()):
            with open(self.ps.current_path(), 'r', encoding="utf8") as file:
                configfile = json.load(file)
                self.display_options.load(self.ps.current_path())
        else:
            configfile = []
            print("Current config not found!")
            self.ps.remove(cur_profile)
            profile_list = self.ps.list()

        with gr.Blocks(analytics_enabled=False) as tab:
            gr.Markdown("# Config Profiles ")
            gr.Markdown("### Current Profile: " + cur_profile)
            gr.Markdown("Any settings you change in the settings tab or extensions you disable/enable will only apply to the active profile")

            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("## Switch and inspect profiles ")
                    with gr.Row(variant='panel'):
                        profile_radio = gr.Radio(label="Profiles", choices=profile_list, value=cur_profile)
                        apply_profile = gr.Button("Load selected profile", elem_id="profile_apply", variant='primary')
                    gr.Markdown("## Add new profiles ")
                    with gr.Row(variant='panel'):
                        with gr.Row():
                            new_profile_input = gr.Textbox("NewProfile", placeholder="new-config.json", label="New Profile Name")
                            image_output = gr.Textbox("outputs", placeholder="Leave empty for current profile's dir",
                                                      label="Profile's root Image outputs folder")

                        add_profile = gr.Button("Create", elem_id="profile_add")

                    with gr.Accordion(label="Edit Selected Profile", open=False):
                        settings_submit = gr.Button(value="Save", variant='primary', elem_id="p_settings_submit")
                        self.create_settings_display()

                    with gr.Accordion(label="Delete Profiles", open=False):
                        delete_profile_radio = gr.Radio(label="Profiles", choices=profile_list)
                        delete_profile_button = gr.Button("DELETE", elem_id="profile_delete", variant='stop')

            settings_submit.click(
                fn=self.save_profile_config,
                inputs=[profile_radio], outputs=[]
            )

            apply_profile.click(
                fn=self.profile_update,
                _js="reload_ui_profile",
                inputs=[profile_radio],
                outputs=[]
            )

            add_profile.click(
                fn=self.profile_add,
                inputs=[new_profile_input, image_output],
                outputs=[profile_radio, delete_profile_radio]
            )

            delete_profile_button.click(
                fn=self.profile_delete,
                inputs=delete_profile_radio,
                outputs=[profile_radio, delete_profile_radio]
            )


            profile_radio.change(fn=self.display_update_components, inputs=profile_radio, outputs=list(self.settings_components.values()))

        return [(tab, "Profiles", "profiles")]


conprof = ConfigProfiles()

scripts.script_callbacks.on_ui_tabs(conprof.add_tab)
scripts.script_callbacks.on_before_ui(conprof.initialize_profile)

