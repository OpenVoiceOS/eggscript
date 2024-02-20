class Intent:
    def __init__(self, name, layer=1):
        self.name = name
        self.layer = layer
        self.utterances = []
        self.actions = []

    def set_utterances(self, utterances):
        self.utterances = utterances

    def speak_dialog(self, dialogs):
        self.actions.append(("speak", dialogs))

    def activate_layer(self, n):
        self.actions.append(("enable_layer", n))

    def deactivate_layer(self, n):
        self.actions.append(("disable_layer", n))

    def exec_code(self, code):
        self.actions.append(("code", code))


class EggParser:
    def __init__(self, lang="en-us", debug=False):
        self.debug = debug
        self.eggscript = "// empty script"
        self.intents = {}

        # script metadata
        self.skill_name = ""
        self.skill_author = ""
        self.skill_url = ""
        self.author_email = ""
        self.license = ""
        self.skill_version = "0.0.0a1"
        self.pkg_name = ""
        self.lang = lang

        # runtime state
        self._current_intent = None
        self._ident = None
        self._current_utts = []
        self._current_dialog = []
        self._code_block = ""
        self._state = ""

    def soft_reset(self):
        self._state = ""
        self._ident = None
        self._current_intent = None
        self._current_utts = []
        self._current_dialog = []
        self._code_block = ""

    def reset(self):
        self.soft_reset()
        self.eggscript = "// empty script"
        self.intents = {}

    def load_eggscript_file(self, path):
        with open(path) as f:
            self.eggscript = f.read()
        self._parse()

    def _save_intent(self):
        if self._current_utts:
            self._current_intent.set_utterances(self._current_utts)
        if self._current_dialog:
            self._current_intent.speak_dialog(self._current_dialog)
        self.intents[self._current_intent.name] = self._current_intent

        if self.debug:
            print(f"""
                Intent: {self._current_intent.name}
                Layer: {self._current_intent.layer}
                Utterances: {self._current_intent.utterances}
                Actions: {self._current_intent.actions}""")

        self.soft_reset()

    def _end_state(self):
        if self._state == "utterance":
            self._current_intent.set_utterances(self._current_utts)
            self._current_utts = []
        elif self._state == "dialog":
            self._current_intent.speak_dialog(self._current_dialog)
            self._current_dialog = []
        elif self._state == "code":
            self._current_intent.exec_code(self._code_block)
            self._code_block = ""

    def _parse(self):
        lines = [l for l in self.eggscript.split("\n") if l and not l.startswith("//")]
        for l in lines:
            if l.strip().startswith("@"):
                if l.strip().startswith("@name"):
                    self.skill_name = l.split("@name ")[-1]
                if l.strip().startswith("@author"):
                    self.skill_author = l.split("@author ")[-1]
                if l.strip().startswith("@email"):
                    self.author_email = l.split("@email ")[-1]
                if l.strip().startswith("@license"):
                    self.license = l.split("@license ")[-1]
                if l.strip().startswith("@url"):
                    self.skill_url = l.split("@url ")[-1]
                if l.strip().startswith("@version"):
                    self.skill_version = l.split("@version ")[-1]
                if l.strip().startswith("@lang"):
                    self.lang = l.split("@lang ")[-1]
                if l.strip().startswith("@pkgname"):
                    self.pkg_name = l.split("@pkgname ")[-1]

            elif l.strip().startswith("#"):
                self._end_state()
                if self._current_intent:
                    self._save_intent()

                self._state = "intent"
                self._current_intent = Intent(name=l.split("# ")[-1],
                                              layer=len(l.split(" ")[0]))
            elif set(list(l)) == {"-"}:
                self._end_state()
                self._state = "deactivate_layer"
                self._current_intent.deactivate_layer(len(l.strip()))
            elif set(list(l)) == {"+"}:
                self._end_state()
                self._state = "activate_layer"
                self._current_intent.activate_layer(len(l.strip()))
            elif l.strip().startswith("+"):
                ident = len(l.split("+")[0])
                if self._state != "utterance":
                    self._end_state()
                    self._state = "utterance"
                else:
                    if self._ident is None or ident != self._ident:
                        self._end_state()

                self._ident = ident
                self._current_utts.append(l.split("+ ")[-1])

            elif l.strip().startswith("-"):
                ident = len(l.split("-")[0])
                if self._state != "dialog":
                    self._end_state()
                    self._state = "dialog"
                else:
                    if self._ident is None or ident != self._ident:
                        self._end_state()
                self._state = "dialog"
                self._ident = ident
                self._current_dialog.append(l.split("- ")[-1])

            elif l.strip().startswith("```"):
                self._end_state()
                if self._state != "code":
                    self._state = "code"
            elif self._state == "code":
                self._code_block += l + "\n"

        if self._current_intent:
            self._save_intent()


if __name__ == "__main__":
    ns = EggParser()
    ns.load_eggscript_file("/home/user/PycharmProjects/eggscript/dialogs.eggscript")
    #         Intent: hello world
    #         Layer: 1
    #         Utterances: ['hello world']
    #         Actions: [('speak', ['hello world'])]
    #
    #         Intent: weather in location
    #         Layer: 1
    #         Utterances: ['how is the weather in {location}']
    #         Actions: [('speak', ['how am i supposed to know the weather in {location}'])]
    #
    #         Intent: weather
    #         Layer: 1
    #         Utterances: ['what is the weather like', 'how is the weather', 'how does it look outside']
    #         Actions: [('speak', ['i do not know how to check the weather', 'stick your head ouf of the window and check for yourself'])]
    #
    #         Intent: count to 10
    #         Layer: 1
    #         Utterances: ['count to 10']
    #         Actions: [('speak', ['i will only count to 5', 'i only know how to count to 5']), ('speak', ['1']), ('speak', ['2']), ('speak', ['3']), ('speak', ['4']), ('speak', ['5'])]

    ns.load_eggscript_file("/home/user/PycharmProjects/eggscript/layers.eggscript")
    #         Intent: tell me about
    #         Layer: 1
    #         Utterances: ['tell me about {thing}']
    #         Actions: [('speak', ['{thing} exists']), ('enable_layer', 2)]
    #
    #         Intent: tell me more
    #         Layer: 2
    #         Utterances: ['tell me more', 'continue']
    #         Actions: [('speak', ['i do not know more']), ('disable_layer', 2)]

    ns.load_eggscript_file("/home/user/PycharmProjects/eggscript/hello.eggscript")
    #         Intent: hello world
    #         Layer: 1
    #         Utterances: ['hello world']
    #         Actions: [('speak', ['hello world']), ('code', 'hello = "world"\nif hello == "world":\n   print("python code!")\n')]
