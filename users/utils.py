# users/utils.py
import pycountry


def get_all_languages():
    languages = []
    for lang in pycountry.languages:
        if hasattr(lang, "alpha_2"):
            languages.append({
                "code": lang.alpha_2,
                "name": lang.name
            })
    return sorted(languages, key=lambda x: x["name"])
