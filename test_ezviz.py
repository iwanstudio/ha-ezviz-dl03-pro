import json
from pyezvizapi import EzvizClient

# TWOJE DANE
USER = "TWOJ_EMAIL"
PASS = "TWOJE_HASLO"
REGION = "eu"
SERIAL = "TWÓJ_SERIAL"

def discover_lock():
    client = EzvizClient(USER, PASS, REGION)
    try:
        print("--- Logowanie ---")
        client.login()
        
        print("--- Pobieranie listy urządzeń ---")
        devices = client.get_device_infos()
        
        # Szukamy konkretnie Twojego zamka
        lock_data = next((d for d in devices if d.get("deviceSerial") == SERIAL), None)
        
        if lock_data:
            print("\n[STRUKTURA STATUSU ZAMKA]")
            # Wyświetlamy tylko to, co siedzi w statusach i opcjach
            status_info = lock_data.get("STATUS", {}).get("optionals", {})
            print(json.dumps(status_info, indent=2))
            
            print("\n--- Szukanie logów zdarzeń ---")
            # Próbujemy różnych metod dostępnych w pyezvizapi
            try:
                # W tej bibliotece metoda może nazywać się inaczej
                # Sprawdźmy co siedzi w ogólnym logu detekcji
                logs = client.get_detection_log(SERIAL)
                print("[LOGI DETEKCJI / ALARMY]")
                print(json.dumps(logs, indent=2))
            except Exception as e:
                print(f"Błąd przy pobieraniu logów: {e}")
                print("Dostępne metody klienta:", dir(client))
                
        else:
            print(f"Nie znaleziono urządzenia o serialu {SERIAL} na tym koncie.")
            print("Znalezione urządzenia:", [d.get("deviceSerial") for d in devices])

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    discover_lock()
