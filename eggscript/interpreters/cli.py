import random
import subprocess
import sys

from ovos_utils.parse import match_one

from eggscript import EggParser


class CliInterpreter(EggParser):
    def __init__(self):
        super().__init__()
        self.active_layers = [1]

    @property
    def active_intents(self):
        return [i for i in self.intents.values()
                if i.layer in self.active_layers]

    def calc_intent(self, utt):
        return {i.name: match_one(utt, i.utterances)[1]
                for i in self.active_intents}

    def get_best_intent(self, utt):
        scores = self.calc_intent(utt)
        best = max([(i, s) for i, s in scores.items()], key=lambda k: k[1])[0]
        return self.intents[best]

    def execute_intent(self, intent):
        for action, payload in intent.actions:
            if action == "speak":
                print("bot:", random.choice(payload))
            elif action == "enable_layer":
                if int(payload) not in self.active_layers:
                    self.active_layers.append(int(payload))
            elif action == "disable_layer":
                if int(payload) in self.active_layers:
                    self.active_layers.remove(int(payload))
            elif action == "code":
                with open("/tmp/intent.py", "w") as f:
                    f.write(payload)
                out = subprocess.check_output([sys.executable, "/tmp/intent.py"]).decode("utf-8")
                if out.strip():
                    print(out.strip())

    def run(self):
        while True:
            utt = input("input: ")
            itent = self.get_best_intent(utt)
            self.execute_intent(itent)


if __name__ == "__main__":
    from os.path import dirname

    c = CliInterpreter()
    c.load_eggscript_file(f"{dirname(dirname(dirname(__file__)))}/example_scripts/hello.eggscript")
    c.run()
