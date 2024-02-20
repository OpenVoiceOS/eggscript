from eggscript import CliCompiler
from os.path import dirname


if __name__ == "__main__":
    c = CliCompiler()
    c.load_eggscript_file(f"{dirname(__file__)}/hello.eggscript")
    c.export("bot")
