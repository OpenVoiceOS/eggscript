from eggscript import CliInterpreter
from os.path import dirname

if __name__ == "__main__":
    c = CliInterpreter()
    c.load_eggscript_file(f"{dirname(__file__)}/dialogs.eggscript")
    c.run()

