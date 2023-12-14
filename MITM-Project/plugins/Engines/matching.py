import os
import yara
class YaraRuleEngine:
    def __init__(self,directory_path):
        self.compiled_rules = []
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                try:
                    rule = yara.compile(filepath=file_path)
                    self.compiled_rules.append(rule)
                except yara.SyntaxError as e:
                    print(f"Error compiling rule '{filename}': {e}")

    def match_rules(self,obj):
        match_object=[]
        for rule in self.compiled_rules:
            match_object.append(rule.match(data=str(obj)))
        return match_object