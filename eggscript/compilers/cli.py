from os import makedirs

from eggscript.interpreters.cli import CliInterpreter

template = """
from difflib import SequenceMatcher
import random
import subprocess
import sys

def fuzzy_match(x: str, against: str) -> float:
   return SequenceMatcher(None, x, against).ratio()


def match_one(query, choices):
   if isinstance(choices, dict):
       _choices = list(choices.keys())
   elif isinstance(choices, list):
       _choices = choices
   else:
       raise ValueError('a list or dict of choices must be provided')

   best = (_choices[0], fuzzy_match(query, _choices[0]))
   for c in _choices[1:]:
       score = fuzzy_match(query, c)
       if score > best[1]:
           best = (c, score)

   if isinstance(choices, dict):
       return (choices[best[0]], best[1])
   else:
       return best


class ChatBot:
   def __init__(self):
       self.active_layers = [1]
       self.intents = ##INTENTS##

   @property
   def active_intents(self):
       return [i for i in self.intents.values()
               if i['layer'] in self.active_layers]

   def calc_intent(self, utt):
       return {i['name']: match_one(utt, i['utterances'])[1]
               for i in self.active_intents}

   def get_best_intent(self, utt):
       scores = self.calc_intent(utt)
       best = max([(i, s) for i, s in scores.items()], key=lambda k:k[1])[0]
       return self.intents[best]

   def execute_intent(self, intent):
       for action, payload in intent['actions']:
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
           intent = self.get_best_intent(utt)
           self.execute_intent(intent)

if __name__ == "__main__":
    c = ChatBot()
    c.run()
"""


class CliCompiler(CliInterpreter):

    def __init__(self):
        super().__init__()
        self.active_layers = [1]

    def compile(self):
        intent_dict = {intent_name: intent.__dict__
                       for intent_name, intent in self.intents.items()}
        return template.replace("##INTENTS##", str(intent_dict))

    def export(self, folder):
        makedirs(folder, exist_ok=True)
        with open(f"{folder}/chatbot.py", "w") as f:
            f.write(self.compile())


if __name__ == "__main__":
    from os.path import dirname

    c = CliCompiler()
    c.load_eggscript_file(f"{dirname(dirname(dirname(__file__)))}/example_scripts/hello.eggscript")
    c.export("hellobot")
