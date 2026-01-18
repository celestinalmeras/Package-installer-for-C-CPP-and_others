import requests
from bs4 import BeautifulSoup
import os
import sys
import time
import json

# =========================================================
# PYINSTALLER RESOURCE PATH
# =========================================================

def resource_path(relative_path):
    """
    Retourne le bon chemin que l'on soit :
    - en script Python
    - en exécutable PyInstaller --onefile
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# =========================================================
# CONFIGURATION
# =========================================================

CONFIG_FILE = "config.json"
LANG_DIR = "lang"

SUPPORTED_LANGS = {
    "fr": "Français",
    "en": "English"
}

# =========================================================
# LANG & CONFIG MANAGEMENT
# =========================================================

def ask_language():
    print("Select language / Sélectionne la langue:")
    for code, name in SUPPORTED_LANGS.items():
        print(f"  {code} - {name}")

    while True:
        choice = input("> ").strip().lower()
        if choice in SUPPORTED_LANGS:
            return choice
        print("Invalid choice / Choix invalide")

def save_config(language):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"language": language}, f, indent=4)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        lang = ask_language()
        save_config(lang)
        return {"language": lang}

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_language(lang):
    lang_path = os.path.join(resource_path(LANG_DIR), f"{lang}.json")

    if not os.path.exists(lang_path):
        print(f"Missing language file: {lang_path}")
        sys.exit(1)

    with open(lang_path, "r", encoding="utf-8") as f:
        return json.load(f)

CONFIG = load_config()
LANG = CONFIG["language"]
LANG_DATA = load_language(LANG)

def t(key):
    return LANG_DATA.get(key, f"[{key}]")

# =========================================================
# CORE LOGIC
# =========================================================

def search_packages(query):
    url = f"https://packages.msys2.org/search?t=pkg&q={query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    tbody = soup.find("tbody")

    results = []
    if tbody:
        for tr in tbody.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) == 3:
                a = tds[0].find("a")
                results.append({
                    "name": a.text.strip(),
                    "link": a["href"],
                    "version": tds[1].text.strip(),
                    "desc": tds[2].text.strip()
                })
    return results

def choose_package(results):
    print("\n" + t("results_found"))
    for i, pkg in enumerate(results):
        print(f"[{i}] {pkg['name']} - {pkg['version']}")

    while True:
        try:
            choice = int(input("\n" + t("choose_number")))
            if 0 <= choice < len(results):
                return results[choice]
        except ValueError:
            pass
        print(t("invalid_choice"))

def get_specific_package_name(soup, architecture="mingw64"):
    for dt in soup.find_all("dt", class_="text-muted small"):
        if architecture == dt.get_text(strip=True):
            dd = dt.find_next_sibling("dd")
            if dd and dd.find("a"):
                return dd.find("a").get_text(strip=True)
    return None

def unlock_pacman():
    lock_file = r"C:\msys64\var\lib\pacman\db.lck"
    os.system('taskkill /F /IM pacman.exe /T >nul 2>&1')
    os.system('taskkill /F /IM gpg-agent.exe /T >nul 2>&1')
    time.sleep(0.5)

    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except Exception as e:
            print(t("unknown_error").format(error=e))

# =========================================================
# MAIN
# =========================================================

def main():
    unlock_pacman()

    print("\n" + t("step_update_full"))
    os.system(r'C:\msys64\usr\bin\bash.exe -l -i -c "pacman -Syu"')

    print("\n" + t("step_update_finish"))
    os.system(r'C:\msys64\usr\bin\bash.exe -l -i -c "pacman -Su"')

    query = input("\n" + t("ask_library")).strip()
    results = search_packages(query)

    if not results:
        print(t("no_results"))
        return

    chosen = choose_package(results)

    pkg_url = chosen["link"]
    if pkg_url.startswith("/"):
        pkg_url = "https://packages.msys2.org" + pkg_url

    resp = requests.get(pkg_url)
    soup = BeautifulSoup(resp.text, "html.parser")

    nom_paquet = get_specific_package_name(soup, "mingw64")

    if nom_paquet:
        unlock_pacman()
        print("\n" + t("installing").format(package=nom_paquet))
        os.system(
            f'C:\\msys64\\usr\\bin\\bash.exe -l -i -c "pacman -S {nom_paquet}" && pause'
        )
    else:
        print(t("package_not_found"))

if __name__ == "__main__":
    main()
