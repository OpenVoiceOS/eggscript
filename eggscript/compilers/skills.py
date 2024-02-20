import socket
from datetime import datetime
from os import listdir, makedirs
from os.path import dirname, join
import re
from eggscript import EggParser


class OVOSSkillCompiler(EggParser):
    def __init__(self):
        super().__init__()
        self.skill_name = "Egg Script Skill"
        self.skill_author = socket.gethostname()

    @property
    def package_name(self):
        return self.pkg_name or \
               "ovos-" + self.skill_import.lower().replace("_", "-") + "-" + self.skill_author

    @property
    def skill_class(self):
        class_name = self.skill_name.title().replace(" ", "")
        if not class_name.lower().endswith("skill"):
            class_name += "Skill"
        return class_name

    @property
    def skill_import(self):
        return "skill_" + self.skill_name.lower().replace(" ", "_").replace("-", "_")

    @property
    def skill_id(self):
        skill_name = self.skill_name.lower().replace(" ", "-").replace("_", "-")
        author = self.skill_author.lower().replace(" ", "")
        return f'{skill_name}.{author}'

    def get_license_text(self):
        license_path = join(dirname(dirname(__file__)), "licenses")
        license_templates = listdir(license_path)
        license_text = "Copyright (c) {{ year }} {{ organization }}"
        if self.license.lower() + ".txt" in license_templates:
            with open(join(license_path, self.license.lower() + ".txt")) as f:
                license_text = f.read()
        return license_text. \
            replace("{{ year }}", str(datetime.now().year)). \
            replace("{{ organization }}", self.skill_author)

    def compile_intents(self):
        intent_code = []
        dialog_files = {}
        intent_files = {}

        for intent_name, intent in self.intents.items():
            enabled_layers = []
            disabled_layers = []
            handler = intent_name.lower().replace(" ", "_")
            intent_files[f'{handler}.intent'] = intent.utterances

            code = ""

            for action, payload in intent.actions:
                if action == "speak":
                    dialog_name = re.sub("[^0-9a-zA-Z]+", " ", payload[0]). \
                        lower().strip().replace(" ", "_")
                    dialog_data = "{"
                    for p in payload:
                        # re.findall('\{.*?\}',p)
                        for v in re.findall('\{(.*?)\}',p):
                            code += f"        {v} = message.data.get('{v}', '')\n"
                            dialog_data += f'"{v}": {v}, '
                    dialog_data = dialog_data.rstrip(", ") + "}"
                    code += f"        self.speak_dialog('{dialog_name}'"
                    if dialog_data != "{}":
                        code += f", {dialog_data}"
                    code += f")\n"
                    dialog_files[f'{dialog_name}.dialog'] = payload
                elif action == "enable_layer":
                    enabled_layers.append(payload)
                elif action == "disable_layer":
                    disabled_layers.append(payload)
                elif action == "code":
                    for line in payload.split("\n"):
                        code += f"        {line}\n"

            intent_template = f"\n    @layer_intent('{handler}.intent', '{intent.layer}')\n"
            for l in enabled_layers:
                intent_template += f"    @enables_layer(layer_name='{l}')\n"
            for l in disabled_layers:
                intent_template += f"    @disables_layer(layer_name='{l}')\n"
            intent_template += f"    def handle_{handler}(self, message):\n{code or 'pass'}"

            intent_code.append(intent_template)
        return intent_code, dialog_files, intent_files

    def compile(self):
        skill_name = self.skill_name.lower().replace(" ", "-").replace("_", "-")
        intent_code, dialog_files, intent_files = self.compile_intents()
        intent_code = "\n".join(intent_code)
        skill_code = f"""
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.skills.decorators import layer_intent, enables_layer, disables_layer, resets_layers

class {self.skill_class}(OVOSSkill):
    def __init__(self):
        super().__init__()
    {intent_code}
        
def create_skill():
    return {self.skill_class}()
"""
        setup = f"""
from setuptools import setup

PLUGIN_ENTRY_POINT = '{self.skill_id}={self.skill_import}:{self.skill_class}'

setup(
    name='{self.package_name}',
    version='{self.skill_version}',
    description='ovos {skill_name} skill plugin',
    url='{self.skill_url}',
    author='{self.skill_author}',
    author_email='{self.author_email}',
    license='{self.license}',
    packages=['{self.skill_import}'],
    include_package_data=True,
    install_requires=[],
    keywords='ovos skill plugin',""" + """
    package_dir={'""" + self.skill_import + """': ""},
    package_data={'""" + self.skill_import + """': ['locale/*', 'ui/*', 'res/*', 'dialog/*', 'vocab/*']},
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
        """
        manifest = """
recursive-include dialog *
recursive-include vocab *
recursive-include locale *
recursive-include res *
recursive-include ui *
        """

        return {
            "dialogs": dialog_files,
            "intents": intent_files,
            "__init__.py": skill_code,
            "setup.py": setup,
            "MANIFEST.in": manifest,
            "LICENSE": self.get_license_text()
        }

    def export(self, folder):
        files = self.compile()

        makedirs(folder, exist_ok=True)

        if files["LICENSE"]:
            with open(f"{folder}/LICENSE", "w") as f:
                f.write(files["LICENSE"])
        if files["MANIFEST.in"]:
            with open(f"{folder}/MANIFEST.in", "w") as f:
                f.write(files["MANIFEST.in"])
        if files["__init__.py"]:
            with open(f"{folder}/__init__.py", "w") as f:
                f.write(files["__init__.py"])
        if files["setup.py"]:
            with open(f"{folder}/setup.py", "w") as f:
                f.write(files["setup.py"])

        makedirs(f"{folder}/dialog/{self.lang}", exist_ok=True)
        for name, utts in files['dialogs'].items():
            with open(join(f"{folder}/dialog/{self.lang}", name), "w") as f:
                f.write("\n".join(utts))

        makedirs(f"{folder}/vocab/{self.lang}", exist_ok=True)
        for name, utts in files['intents'].items():
            with open(join(f"{folder}/vocab/{self.lang}", name), "w") as f:
                f.write("\n".join(utts))


if __name__ == "__main__":

    c = OVOSSkillCompiler()
    c.load_eggscript_file(f"{dirname(dirname(dirname(__file__)))}/example_scripts/dialogs.eggscript")
    skill = c.compile()
    print(skill["__init__.py"])
