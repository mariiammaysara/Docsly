import os
from string import Template

class TemplateParser:
    """
    Advanced Template Parser that loads prompts from localized python files.
    Structure: locales/{lang}/{group}.py
    """
    def __init__(self, language: str = None, default_language: str = 'en'):
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.default_language = default_language
        self.language = None
        self.set_language(language)

    def set_language(self, language: str):
        if not language:
            self.language = self.default_language
            return

        language_path = os.path.join(self.current_path, "locales", language)
        if os.path.exists(language_path):
            self.language = language
        else:
            self.language = self.default_language

    def get(self, group: str, key: str, vars: dict = {}):
        if not group or not key:
            return None
        
        # Determine the targeted language path
        targeted_language = self.language
        group_path = os.path.join(self.current_path, "locales", targeted_language, f"{group}.py")
        
        if not os.path.exists(group_path):
            targeted_language = self.default_language
            group_path = os.path.join(self.current_path, "locales", targeted_language, f"{group}.py")

        if not os.path.exists(group_path):
            return None
        
        # Import group module dynamically
        # Using src. prefix to match project structure
        module_path = f"src.stores.llm.templates.locales.{targeted_language}.{group}"
        try:
            module = __import__(module_path, fromlist=[group])
            if not module:
                return None
            
            key_attribute = getattr(module, key)
            if isinstance(key_attribute, Template):
                return key_attribute.substitute(vars)
            return key_attribute
        except Exception as e:
            print(f"Error loading template {key} from {group}: {e}")
            return None
