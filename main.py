import requests
from bs4 import BeautifulSoup
import datetime
import time
import re
import sys

def load_tokens(file_path="tokeny.txt"):
    """
    Načte tokeny ze souboru a vrátí je jako slovník.
    Očekávaný formát:
      MENZA_K8_TOKEN = "..."
      SHIBSESSION_TOKEN = "..."
    """
    tokens = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    # Odstraní případné uvozovky z hodnoty
                    value = value.strip().strip('"')
                    tokens[key] = value
        return tokens
    except FileNotFoundError:
        print(f"❌ Chyba: Soubor s tokeny '{file_path}' nebyl nalezen.")
        sys.exit(1)

# Načtení tokenů ze souboru tokeny.txt
tokens = load_tokens("tokeny.txt")
MENZA_K8_TOKEN = tokens.get("MENZA_K8_TOKEN", "")
SHIBSESSION_TOKEN = tokens.get("SHIBSESSION_TOKEN", "")

CANTEEN_ID = 1 # Výchozí hodnota: Harcov (1), Husova (2), Voroněžská (3)


def get_current_date():
    """Získá od uživatele korektní datum ve formátu YYYY-MM-DD s možností odkliknutí 'Enter' pro dnešní datum."""
    while True:
        print("\n" + "=" * 50)
        print(" 📅  Stiskněte [Enter] pro dnešní datum ".center(50))
        print("=" * 50)

        datum = input("\n🔹 Zadejte datum objednávky (formát RRRR-MM-DD): ").strip()

        # Pokud uživatel stiskne Enter, použije se dnešní datum
        if not datum:
            dnes = datetime.datetime.now().strftime("%Y-%m-%d")
            print(f"\n✅ \033[92mPoužito dnešní datum: {dnes}\033[0m")
            return dnes

        try:
            # Pokus o parsování data a implicitní kontrola existence data
            datetime.datetime.strptime(datum, "%Y-%m-%d")
            print(f"\n✅ \033[92mDatum úspěšně zadáno: {datum}\033[0m")
            return datum
        except ValueError:
            print("\n❌ \033[91mChyba: Neplatný formát nebo neexistující datum.\033[0m")
            print("🔹 \033[91mZadejte prosím datum ve tvaru RRRR-MM-DD (např. 2024-02-15).\033[0m")
            print("=" * 50)


def get_menza_page(date=None, canteen_id=1, current_date=""):
    """Načte stránku menzy pro datum a kantýnu"""
    if date is None:
        date = current_date

    # Výběr menzy podle ID
    canteen_url = "harcov"
    if canteen_id == 2:
        canteen_url = "husova"
    elif canteen_id == 3:
        canteen_url = "voronezska"

    # Složení URL
    url = f"https://menza.tul.cz/{canteen_url}/{date}/"

    # Nastavení cookies
    cookies = {
        "mobileDetect": "0",
        "MENZA-K8": MENZA_K8_TOKEN,
        "_shibsession_": SHIBSESSION_TOKEN,
        #"MsgFP": "",
        "MsgCh": "1"
    }

    # Nastavení hlaviček
    headers = {
        "Accept": "text/html, */*; q=0.01",
        "Accept-Language": "cs,en;q=0.9",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    }

    try:
        response = requests.get(url, cookies=cookies, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ Chyba při načítání stránky menzy: {e}")
        return None


def check_login_status(html_content):
    """Zkontroluje, zda je uživatel přihlášen hledáním odkazu pro odhlášení"""
    if not html_content:
        return False

    soup = BeautifulSoup(html_content, 'html.parser')
    logout_link = soup.find('a', href='/odhlasit/')

    return logout_link is not None


def parse_meals(html_content):
    """Parsuje jídla z HTML obsahu"""
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    all_meals = []

    # Najde všechny sekce jídel (obědy, večeře)
    sections = soup.find_all('section')

    for section in sections:
        section_header = section.find('header')
        if not section_header:
            continue

        section_title = section_header.find('h1').text if section_header.find('h1') else "Neznámá sekce"

        # Najde všechna jídla v této sekci
        meal_articles = section.find_all('article')
        for article in meal_articles:
            # Přeskočí, pokud je to polévka
            if article.get('class') and 'pol' in article.get('class'):
                continue

            meal_data = {
                'section': section_title,
                'canteen_id': article.get('data-canteen-id'),
                'menu_id': article.get('data-menu-id'),
                'available': True if article.get('data-menu-id') else False,
                'order_id': article.get('data-menu-id'),
                'rating': article.get('data-rating')
            }

            # Získá detaily jídla
            table = article.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        # Získá číslo jídla
                        meal_number = cells[0].text.strip()
                        meal_data['number'] = meal_number if meal_number else "N/A"

                        # Získá název jídla a vyčistí HTML tagy
                        name_cell = cells[1]
                        if name_cell.find('h1'):
                            h1_content = name_cell.find('h1')
                            # Vyčistí obsah h1 pro odstranění HTML tagů a získá pouze text
                            meal_name = h1_content.get_text().strip()
                            # Odstraní velikost porce z názvu
                            meal_name = re.sub(r'\d+g$', '', meal_name).strip()
                            meal_data['name'] = meal_name
                        else:
                            meal_data['name'] = "Neznámé jídlo"

                        # Získá poznámky k jídlu, ale přeskočí velikost porce
                        meal_data['notes'] = ""

                        # Přeskočí ingredience
                        meal_data['ingredients'] = ""

                        # Získá cenu
                        price_cell = cells[4]
                        price = price_cell.find('span')
                        if price:
                            price_text = price.text.strip()
                            # Extrahuje pouze číslo
                            price_match = re.search(r'(\d+,\d+)', price_text)
                            if price_match:
                                meal_data['price'] = price_match.group(1).replace(',', '.')
                            else:
                                meal_data['price'] = "N/A"
                        else:
                            meal_data['price'] = "N/A"

            all_meals.append(meal_data)

    return all_meals


def display_meals(meals):
    """Zobrazí jídla ve formátovaném způsobu."""
    if not meals:
        print("\n⚠️ Nenalezena žádná jídla.")
        return

    current_section = None
    meal_index = 1
    meal_mapping = {}

    for meal in meals:
        # Zobrazí záhlaví sekce, pokud je nová
        if current_section != meal['section']:
            current_section = meal['section']
            print(f"\n{'=' * 50}")
            print(f" 🍽️  {current_section} ")
            print(f"{'=' * 50}")

        # Formátování indikátoru dostupnosti
        availability = "✅ DOSTUPNÉ" if meal['available'] else "❌ VYPRODÁNO"
        order_id = f" (ID: {meal['order_id']})" if meal['available'] else ""

        # Zobrazení jídla ve formátovaném stylu
        print(f"\n[{meal_index}] {meal['number']} - {meal['name']}")
        print(f"   💰 Cena: {meal['price']} Kč | {availability}{order_id}")
        print(f"{'-' * 30}")

        # Uloží do mapování jídel
        meal_mapping[meal_index] = meal
        meal_index += 1

    return meal_mapping



def order_meal(meal_data, canteen_id,current_date):
    """Objedná vybrané jídlo"""
    # Extrahuje order ID z dat jídla
    order_id = meal_data['order_id']
    if not order_id:
        print(f"❌ Nelze objednat {meal_data['name']} – není dostupné.")
        return False

    url = f"https://menza.tul.cz/harcov/{current_date}/"

    # Nastavení cookies
    cookies = {
        "mobileDetect": "0",
        "MENZA-K8": MENZA_K8_TOKEN,
        "_shibsession_": SHIBSESSION_TOKEN,
        #"MsgFP": "",
        "MsgCh": "1"
    }

    # Nastavení hlaviček
    headers = {
        "Accept": "text/html, */*; q=0.01",
        "Accept-Language": "cs,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://menza.tul.cz",
        "Referer": "https://menza.tul.cz/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    # Připraví data pro objednávku
    data = {
        "ORDER": "",
        "JID": order_id,
        "CANTEEN": str(canteen_id)
    }

    try:
        response = requests.post(url, cookies=cookies, headers=headers, data=data)

        # Pokud dostaneme HTTP 200, považujeme to za úspěch
        if response.status_code == 200:
            #print(f"Úspěšně objednáno {meal_data['name']}!")
            return True
        else:
            print(f"❌ Nepodařilo se objednat {meal_data['name']}. Status kód: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Chyba při objednávání jídla: {e}")
        return False


def select_canteen():
    """Umožní uživateli vybrat menzu"""
    print("\n🔸 Vyberte menzu:")
    print("1 - Harcov")
    print("2 - Husova")
    print("3 - Voroněžská")

    while True:
        try:
            choice = int(input("➤ Zadejte vaši volbu (1-3): "))

            if 1 <= choice <= 3:
                return choice

            print("❌ Neplatná volba. Zadejte číslo mezi 1 a 3.")

        except ValueError:
            print("⚠️ Chyba: Zadejte prosím platné číslo.")


def select_meals(meal_mapping):
    """Umožní uživateli vybrat jídla ke sledování a objednání"""
    selected_meals = []

    print("\n🍽️ Vyberte jídla, která chcete objednat:")
    print("🔢 Zadejte čísla jídel oddělená čárkami (např. 1,3,5)")
    print("📦 Tato jídla budou sledována a automaticky objednána, jakmile budou dostupná.")

    while True:
        try:
            selections = input("Váš výběr: ").strip()
            if not selections:
                print("⚠️ Nebyla vybrána žádná jídla. ❌ Ukončuji.")
                sys.exit(0)

            selected_indices = [int(idx.strip()) for idx in selections.split(',')]
            for idx in selected_indices:
                if idx in meal_mapping:
                    selected_meals.append(meal_mapping[idx])
                else:
                    print(f"❌ Neplatný výběr: {idx}. Zkuste to znovu.")
                    selected_meals = []
                    break

            if selected_meals:
                # Vypočítá nejvyšší cenu jídla
                highest_price = max([float(meal['price']) for meal in selected_meals if meal['price'] != "N/A"])
                print(f"\n💰 Nejvyšší cena jídla: {highest_price} Kč")
                print("⚠️ Ujistěte se, že máte dostatečný zůstatek na účtu menzy.")
                return selected_meals

        except ValueError:
            print("Zadejte prosím platná čísla oddělená čárkami.")


def monitor_and_order(selected_meals, canteen_id, current_date):
    """Sleduje dostupnost jídel a objedná je, jakmile budou dostupná"""
    print("\nZahajuji sledování jídel...")
    print("Stiskněte Ctrl+C pro zastavení skriptu.")

    try:
        check_interval = 3  # sekund mezi kontrolami
        while True:
            all_ordered = True

            # Získá aktuální data o jídlech
            html_content = get_menza_page(current_date, canteen_id)
            if not html_content:
                print("Nepodařilo se načíst data z webových stránek menzy.")
                #time.sleep(check_interval)
                continue

            current_meals = parse_meals(html_content)

            # Zkontroluje, zda byla všechna vybraná jídla objednána
            for target_meal in selected_meals:
                if target_meal.get('ordered', False):
                    continue

                all_ordered = False

                # Najde aktuální stav tohoto jídla
                for current_meal in current_meals:
                    if (current_meal['menu_id'] == target_meal['menu_id'] and
                            current_meal['section'] == target_meal['section'] and
                            current_meal['number'] == target_meal['number']):

                        # Zkontroluje, zda je jídlo nyní dostupné
                        if current_meal['available']:
                            print(
                                f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Jídlo dostupné: {current_meal['name']}")

                            # Pokusí se objednat jídlo
                            success = order_meal(current_meal, canteen_id, current_date)
                            if success:
                                # Označí jako objednané
                                target_meal['ordered'] = True
                                print(f"✅ Úspěšně objednáno: {current_meal['name']}")
                                sys.exit(0);
                            else:
                                print(f"❌ Nepodařilo se objednat: {current_meal['name']}")
                        else:
                            # Vytiskne aktualizaci stavu každých několik kontrol
                            print(
                                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Čekám na: {target_meal['name']}")

            # Pokud byla všechna jídla objednána, ukončí
            if all_ordered:
                print("\nVšechna vybraná jídla byla úspěšně objednána!")
                break

            # Počká před další kontrolou
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\nSledování zastaveno uživatelem.")


def main():
    # Získá aktuální datum v požadovaném formátu
    current_date = get_current_date()
    #print(f"✅ Kontroluji jídla pro datum: {current_date}")

    # Zkontroluje, zda jsou nastaveny tokeny
    if MENZA_K8_TOKEN == "-" or SHIBSESSION_TOKEN == "-":
        print("CHYBA: Autentizační tokeny nejsou nastaveny.")
        print("Aktualizujte hodnoty tokenů v horní části skriptu. Viz README pro instrukce.")
        return

    # Umožní uživateli vybrat menzu
    canteen_id = select_canteen()

    # Načte data o jídlech
    html_content = get_menza_page(current_date, canteen_id)
    if not html_content:
        print("Nepodařilo se načíst data z webových stránek menzy.")
        return

    # Zkontroluje stav přihlášení
    if not check_login_status(html_content):
        print("\n" + "=" * 50)
        print("❌ CHYBA: Přihlášení selhalo!")
        print("🔹 Nejprve zkuste program spustit znovu.")
        print("🔹 Pokud problém přetrvává, aktualizujte své tokeny.")
        print("=" * 50 + "\n")
        return

    print("Přihlášení úspěšné!")

    # Parsuje a zobrazí všechna jídla
    meals = parse_meals(html_content)
    meal_mapping = display_meals(meals)

    # Vytiskne souhrn
    available_meals = sum(1 for meal in meals if meal['available'])
    print(f"\nSouhrn: Nalezeno {len(meals)} jídel, {available_meals} dostupných k zakoupení.")

    # Umožní uživateli vybrat jídla ke sledování
    selected_meals = select_meals(meal_mapping)

    # Sleduje a objednává jídla
    monitor_and_order(selected_meals, canteen_id,current_date)


if __name__ == "__main__":
    main()