from eggscript import OVOSSkillCompiler
from os.path import dirname


if __name__ == "__main__":
    c = OVOSSkillCompiler()
    c.load_eggscript_file(f"{dirname(__file__)}/layers.eggscript")
    c.export("myskill")
