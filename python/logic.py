# /////////////////////////////////////////////////////////////////////////////////////////////
# ////---- Importovanie potrebných knižníc, cesty k súborom a nastavenia ----////
# /////////////////////////////////////////////////////////////////////////////////////////////
import sqlite3
import time
import math
import configparser
import os
import json
import platform
from datetime import datetime

# import main  # Importovanie hlavného modulu pre prístup k MODLOADER_VERSION nefunguje ak je binárny.
# from main import MODLOADER_VERSION  # Importovanie verzie modloadera nefunguje ak je binárny.

# ////---- Cesty k súborom ----////
module_root = os.path.dirname(os.path.dirname(__file__))
config_path = os.path.join(module_root, 'config', 'config.json')
data_path = os.path.join(module_root, 'data', 'data.ini')
log_path = os.path.join(module_root, 'data', 'log.txt')
path_ini_path = os.path.join(module_root, 'config' ,'path.ini')
# ////-----------------------------------------------------------------------------------------

# ////---- Logovanie do log.txt ktorý si načíta GUI widget console ----////
def log_to_console(message, color=None):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}\n"
    try:
        with open(log_path, 'a') as f:
            f.write(line)
    except Exception as e:
        print(f"[LOGIC] Chyba pri zápise do log.txt: {e}")
# ////-----------------------------------------------------------------------------------------

# ////---- Automatická detekcia cesty k SCUM.db ----////
def detect_db_path():
    # 1. Ak existuje path.ini a obsahuje db_path
    if os.path.exists(path_ini_path):
        config = configparser.ConfigParser()
        config.read(path_ini_path)
        if 'paths' in config and 'db_path' in config['paths']:
            db_path = config['paths']['db_path']
            if os.path.exists(db_path):
                return db_path

    # 2. Pokus o automatickú detekciu
    system = platform.system()
    if system == 'Windows': # Detekcia pre Windows
        default_win = os.path.expandvars(r"%LOCALAPPDATA%\SCUM\Saved\SaveFiles\SCUM.db")
        if os.path.exists(default_win):
            return default_win
    elif system == 'Linux': # Detekcia pre Linux
        candidates = [
            os.path.expanduser("~/Steam/steamapps/compatdata/513710/pfx/drive_c/users/steamuser/AppData/Local/SCUM/Saved/SaveFiles/SCUM.db"),
            os.path.expanduser("~/.var/app/com.valvesoftware.Steam/.steam/steam/steamapps/compatdata/513710/pfx/drive_c/users/steamuser/AppData/Local/SCUM/Saved/SaveFiles/SCUM.db")
        ]
        for path in candidates:
            if os.path.exists(path):
                return path

    # Zápis do path.ini, ak nič nebolo nájdené, ale ak db_path neexistuje, vytvoríme nový
    config = configparser.ConfigParser()
    config.read(path_ini_path)

    # Skontrolujeme, či existuje sekcia 'paths' a kľúč 'db_path'
    if 'paths' not in config:
        config['paths'] = {}

    # Ak db_path neexistuje, vytvoríme ho, inak nič nemeníme môže ísť len o dočastne odpojený disk!
    if 'db_path' not in config['paths']:
        config['paths']['db_path'] = ''
        with open(path_ini_path, 'w') as configfile:
            config.write(configfile)
        log_to_console("[LOGIC] SCUM.db nebol nájdený. Prosím zadajte cestu ručne do path.ini v sekcii [paths], kľúč: db_path.")
    else:
        log_to_console("[LOGIC] Cesta k SCUM.db je neplatná, ale hodnota db_path sa nezmenila.")
    return None
# ////-----------------------------------------------------------------------------------------

# ////---- Načítanie alebo vytvorenie config.json ----////
# Ak config.json neexistuje, vytvorí sa s predvolenými hodnotami
def load_or_create_config():
    default_config = {
        "scan_interval": 1,
        "zones": [
            {
                "asset": "/Game/ConZ_Files/BaseBuilding/BaseElements/BP_Base_Flag.BP_Base_Flag_C",
                "radius": 5000,
                "shape": "square"
            },
            {
                "asset": "/Game/ConZ_Files/BaseBuilding/BaseElements/BP_Base_Flag_Supporter.BP_Base_Flag_Supporter_C",
                "radius": 5000,
                "shape": "square"
            }
        ]
    }

    if not os.path.exists(config_path):
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        return default_config

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        for key in default_config:
            if key not in user_config:
                user_config[key] = default_config[key]
        return user_config
    except Exception as e:
        log_to_console(f"[LOGIC] Chyba pri načítaní config.json: {e}")
        return default_config
# ////-----------------------------------------------------------------------------------------

# ////---- Funkcia na aktualizáciu data.ini ----////
def update_data_ini(prisoner_name=None, zones_count=None):
    if prisoner_name is not None:
        data_ini['prisoner'] = {'name': prisoner_name}
    if zones_count is not None:
        data_ini['all_zones'] = {'count': str(zones_count)}

    try:
        with open(data_path, 'w') as configfile:
            data_ini.write(configfile)
    except Exception as e:
        print(f"[LOGIC] Chyba pri zápise do data.ini: {e}")
# ////-----------------------------------------------------------------------------------------

# ////---- Načítanie config.json a nastavenie SCAN_INTERVAL ----////
# Ak config.json neexistuje, vytvorí sa s predvolenými hodnotami
config_json = load_or_create_config()
SCAN_INTERVAL = config_json.get("scan_interval", 8)
# ////-----------------------------------------------------------------------------------------

# ////---- Načítanie konfiguračného súboru pre data.ini ----////
# Tento súbor sa používa na ukladanie informácií o používateľovi a počte zón
data_ini = configparser.ConfigParser()
# ////-----------------------------------------------------------------------------------------

# ////---- Detekcia cesty k SCUM.db ----////
DB_PATH = detect_db_path()
# ////-----------------------------------------------------------------------------------------

# //////////////////////////////////////////////////////////////////////////////////////////////
# ////---- Funkcie na prácu s databázou ----////
# //////////////////////////////////////////////////////////////////////////////////////////////

# ////---- Zabezpečenie indexov v databáze ----////
def ensure_indexes(conn):
    try:
        cursor = conn.cursor()

        # entity
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_class ON entity(class);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_flags ON entity(flags);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_id ON entity(id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_entity_system_id ON entity(entity_system_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_location_xy ON entity(location_x, location_y);")

        # entity_system
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_system_id ON entity_system(id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_system_user_profile_id ON entity_system(user_profile_id);")

        # user_profile
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_profile_id ON user_profile(id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_profile_name ON user_profile(name);")

        # virtualized_item
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_virtualized_item_entity_id ON virtualized_item(item_entity_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_virtualized_item_can_expire ON virtualized_item(can_expire);")

        # base
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_base_user_profile_id ON base(user_profile_id);")

        conn.commit()
    except sqlite3.Error as e:
        log_to_console(f"[LOGIC] Chyba pri vytváraní indexov: {e}")
# ////-----------------------------------------------------------------------------------------

# ////---- Otvorenie spojenia s databázou ----////
def open_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=1)
        # Nastavenie režimu WAL pre lepší výkon
        conn.execute("PRAGMA journal_mode=WAL;")
        # Nastavenie režimu zamykania a synchronizácie
        conn.execute("PRAGMA locking_mode=NORMAL;")
        # Nastavenie režimu čítania bez zamykania
        conn.execute("PRAGMA synchronous=NORMAL;")
        # Povolenie čítania bez zamykania
        conn.execute("PRAGMA read_uncommitted = true;")
        # Umožní prístup k stĺpcom podľa názvu
        conn.row_factory = sqlite3.Row
        # Zabezpečenie indexov
        ensure_indexes(conn)
        return conn
    except sqlite3.Error as e:
        log_to_console(f"[LOGIC] Chyba pri otváraní databázy: {e}")
        return None
# ////-----------------------------------------------------------------------------------------

# ////---- Zatvorenie spojenia s databázou ----////    
def close_db_connection(conn):
    if conn:
        try:
            conn.close()
        except sqlite3.Error as e:
            log_to_console(f"[LOGIC] Chyba pri zatváraní databázy: {e}")
# ////-----------------------------------------------------------------------------------------

# ////---- Získanie ID používateľského profilu ----////
def get_user_profile_id_old(conn):
    # Výsledky budú ako slovník {názov_stĺpca: hodnota}
    cursor = conn.cursor()

    # Vyber entity typu FPrisonerEntity
    cursor.execute("""
        SELECT entity_system_id, flags
        FROM entity
        WHERE class = 'FPrisonerEntity'
    """)
    rows = cursor.fetchall()

    # Filtrovanie hráčov
    flagged = [row for row in rows if row['flags'] == 0]
    if len(flagged) != 1:
        return None
    entity_system_id = flagged[0]['entity_system_id']

    # Získanie user_profile_id z entity_system
    cursor.execute("""
        SELECT user_profile_id
        FROM entity_system
        WHERE id = ?
    """, (entity_system_id,))
    result = cursor.fetchone()

    return result['user_profile_id'] if result else None

def get_user_profile_id(conn):
    cursor = conn.cursor()
    
    # Skús najskôr v1.2 (BP_Prisoner_ES)
    cursor.execute("""
        SELECT entity_system_id
        FROM entity
        WHERE class = 'BP_Prisoner_ES' AND flags = 0
    """)
    row = cursor.fetchone()
    
    # Ak nenájdeš v1.2, skús v1.1 (FPrisonerEntity)
    if not row:
        cursor.execute("""
            SELECT entity_system_id
            FROM entity
            WHERE class = 'FPrisonerEntity' AND flags = 0
        """)
        row = cursor.fetchone()
    
    # Ak stále nič, vráť None
    if not row:
        return None
    
    entity_system_id = row['entity_system_id']
    
    cursor.execute("""
        SELECT user_profile_id
        FROM entity_system
        WHERE id = ?
    """, (entity_system_id,))
    result = cursor.fetchone()
    return result['user_profile_id'] if result else None
# ////-----------------------------------------------------------------------------------------

# ////---- Získanie mena používateľa ----////
# Vráti meno používateľa na základe ID používateľského profilu
def get_user_name(conn, user_profile_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name
        FROM user_profile
        WHERE id = ?
    """, (user_profile_id,))
    row = cursor.fetchone()
    return row['name'] if row else None
# ////-----------------------------------------------------------------------------------------

# ////---- Získanie položiek, ktoré môžu expirovať ----////
# Vráti zoznam ID položiek, ktoré majú nastavené can_expire
def get_expiring_items(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT item_entity_id
        FROM virtualized_item
        WHERE can_expire = 1
    """)
    rows = cursor.fetchall()
    return [row['item_entity_id'] for row in rows]
# ////-----------------------------------------------------------------------------------------

# ////---- Získanie pozícií položiek ----////
def get_item_positions(conn, item_ids):
    if not item_ids:
        return {}
    placeholders = ','.join(['?'] * len(item_ids))
    query = f"""
        SELECT id, location_x, location_y 
        FROM entity
        WHERE id IN ({placeholders})
    """
    cursor = conn.cursor()
    cursor.execute(query, item_ids)
    rows = cursor.fetchall()
    return {row['id']: (row['location_x'], row['location_y']) for row in rows}
# ////-----------------------------------------------------------------------------------------

# ////---- Získanie pozícií zón používateľa ----////
def get_all_zones_positions(conn, user_profile_id):
    # Načítame pravidlá z config.json
    config = load_or_create_config()
    asset_rules = {entry["asset"]: entry for entry in config.get("zones", [])}

    # Získame všetky zóny používateľa
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id
        FROM base
        WHERE user_profile_id = ?
    """, (user_profile_id,))
    player_zones_ids = set(row['id'] for row in cursor.fetchall())
    if not player_zones_ids:
        return []
    
    # Získame pozície a assety pre všetky zóny používateľa
    placeholders = ','.join(['?'] * len(player_zones_ids))
    query = f"""
        SELECT location_x, location_y, asset
        FROM base_element
        WHERE base_id IN ({placeholders})
    """
    cursor.execute(query, tuple(player_zones_ids))
    rows = cursor.fetchall()

    # Filterovanie zón podľa pravidiel
    filtered = []
    for x, y, asset in rows:
        if asset not in asset_rules:
            continue
        rule = asset_rules[asset]
        filtered.append({
            "x": x,
            "y": y,
            "asset": asset,
            "radius": rule.get("radius", 5000),
            "shape": rule.get("shape", "square")
        })
    return filtered
# ////-----------------------------------------------------------------------------------------

# ////---- Aktualizácia položiek, ktoré môžu expirovať ----////
def update_can_expire(conn, item_ids):
    if not item_ids:
        return
    placeholders = ','.join(['?'] * len(item_ids))
    query = f"""
        UPDATE virtualized_item
        SET can_expire = 0
        WHERE item_entity_id IN ({placeholders})
    """
    cursor = conn.cursor()
    cursor.execute(query, item_ids)
    conn.commit()
    log_to_console(f"[Save] {len(item_ids)} Items have been saved!")
# ////-----------------------------------------------------------------------------------------

# /////////////////////////////////////////////////////////////////////////////////////////////
# ////---- Hlavná logika modulu ----////
# /////////////////////////////////////////////////////////////////////////////////////////////
def main_loop(conn=None, stop_event=None):
    # Hlavná slučka pre kontrolu položiek a ich expiráciu
    while not (stop_event and stop_event.is_set()):
        try:
            # Získanie všetkých položiek, ktoré môžu expirovať
            # a ich pozícií
            # a pozícií všetkých zón používateľa
            # a mena používateľa
            expiring_ids = get_expiring_items(conn)
            item_positions = get_item_positions(conn, expiring_ids)
            user_profile_id = get_user_profile_id(conn)
            prisoner_name = get_user_name(conn, user_profile_id) if user_profile_id else "N/A"
            all_zones = get_all_zones_positions(conn, user_profile_id)

            # Určenie položiek, ktoré sú v dosahu zóny
            items_to_protect = []
            for item_id, (ix, iy) in item_positions.items():
                for base in all_zones:
                    bx, by = base["x"], base["y"]
                    radius = base["radius"]
                    shape = base["shape"]
                    dx = abs(ix - bx)
                    dy = abs(iy - by)
                    if shape == "square":
                        if dx <= radius and dy <= radius:
                            items_to_protect.append(item_id)
                            break
                    elif shape == "circle":
                        if math.sqrt(dx**2 + dy**2) <= radius:
                            items_to_protect.append(item_id)
                            break
            # Zrušenie despawnu položiek, ktoré sú v dosahu zóny
            update_can_expire(conn, items_to_protect)
            # Aktualizácia data.ini s informáciami o používateľovi a počte zón
            update_data_ini(prisoner_name=prisoner_name, zones_count=len(all_zones))
        except Exception as e:
            log_to_console(f"[CHYBA] {e}")
        # Počkáme SCAN_INTERVAL sekúnd pred ďalšou kontrolou
        if stop_event and stop_event.is_set():
            break  # Ukončí cyklus okamžite, ak bol stop_event nastavený
        else:
            time.sleep(SCAN_INTERVAL)
# ////-----------------------------------------------------------------------------------------

# ////---- Spustenie hlavnej funkcie z main.py ----////
def logic_main_init(stop_event=None):
    # Ak verzia modloadera je nižšia ako 0.1, ukončenie kódu po skompilovaní prestáva fungovať
    #if main.MODLOADER_VERSION < (0, 1):
    #    return

    # Vytvoríme log.txt ak neexistuje
    try:
        with open(log_path, 'w') as f:
            f.write("[SaveItems] Module Loaded...\n")
    except Exception as e:
        print(f"[LOGIC] Nepodarilo sa vytvoriť log.txt: {e}")

    # Ak DB_PATH neexistuje, vypíšeme správu a ukončíme logiku
    if not DB_PATH or not os.path.exists(DB_PATH):
        log_to_console("[SaveItems] SCUM.db file not found or disk is disconnected. Please enter the path manually in config/path.ini and restart the application.")
        return
    
    # Načítame databázu a spustíme hlavnú slučku
    try:
        # Otvoríme spojenie s databázou
        conn = open_db_connection()

        # Zaregistrujeme funkciu na zatvorenie spojenia pri ukončení programu (nefunguje lebo ide o iné vlákno)
        #if conn:
        #    atexit.register(lambda: close_db_connection(conn))
        
        main_loop(conn, stop_event)
    except Exception as e:
        log_to_console(f"[LOGIC] Chyba pri otváraní databázy: {e}")
        return
# ////-----------------------------------------------------------------------------------------

# ////---- Spustenie hlavnej funkcie priamo ----////
if __name__ == "__main__":
    logic_main_init()