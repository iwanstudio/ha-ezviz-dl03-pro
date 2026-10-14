# Ezviz DL03 Pro Integration for Home Assistant 🚪🔓

<p align="center">
  <img src="https://raw.githubusercontent.com/iwanstudio/ha-ezviz-dl03-pro/main/branding/logo.png" width="300">
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=iwanstudio&repository=ha-ezviz-dl03-pro&category=integration">
    <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open HACS Repository" height="48">
  </a>
  
  <a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=ezviz_dl03_pro">
    <img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Add Integration" height="48">
  </a>
</p>

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/dynamic/json?color=blue&label=version&query=$.version&url=https://raw.githubusercontent.com/iwanstudio/ha-ezviz-dl03-pro/main/custom_components/ezviz_dl03_pro/manifest.json)
![Maintainer](https://img.shields.io/badge/maintainer-iwanstudio-blue.svg)

---

### [PL] Opis projektu
Nieoficjalna, zaawansowana integracja dla zamka inteligentnego **Ezviz DL03 Pro**. Stworzona specjalnie dla modeli, które nie są poprawnie obsługiwane przez standardowe rozwiązania. Dzięki mechanizmowi **Fast Listener**, integracja reaguje na zdarzenia (dzwonek, rygiel, otwarcie) niemal w czasie rzeczywistym.

### [EN] Project Description
Unofficial, advanced integration for the **Ezviz DL03 Pro** smart lock. Specifically designed for models not fully supported by standard integrations. Featuring a **Fast Listener** mechanism for near real-time response to events like doorbell rings, lock status, and door opening.

---

## ✨ Funkcje / Features

* **Push w czasie rzeczywistym (MQTT):** zdarzenia przychodzą natychmiast, bez odpytywania chmury co 2 s. Gdy push nie działa, integracja sama przełącza się na odpytywanie. / **Real-time push (MQTT)** with automatic polling fallback.
* **Stan rygla:** wyliczany ze zdarzeń, z konfigurowalnym czasem automatycznego „zamknięcia”. / Lock state derived from events, configurable auto-relock.
* **Dzwonek:** encja `event` typu doorbell + czujnik binarny. / Doorbell `event` entity + binary sensor.
* **Aktywność zamka:** encja `event` (otwarcie/zamknięcie/inne) z informacją **kto** i **czym** otworzył (np. Martyna, odcisk palca). / Lock activity `event` entity with **who** and **how**.
* **Zdarzenie na szynie HA** `ezviz_dl03_pro_event` dla automatyzacji. / HA bus event for automations.
* **Zdalne otwieranie (eksperymentalne):** encja `lock`, domyślnie wyłączona. ⚠️ DL03 Pro wymaga potwierdzenia na klawiaturze zamka, więc chmura odrzuca samo polecenie zdalne (`code 3, manage failed`). / Experimental remote unlock (off by default); the DL03 Pro requires keypad confirmation, so remote-only unlock is rejected.
* **Bateria, drzwi, Wi-Fi, błędne próby, diagnostyka.** / Battery, door, Wi-Fi, failed attempts, diagnostics.
* **Ponowne logowanie i kod weryfikacyjny (2FA)** obsługiwane w interfejsie. / Re-auth and verification code (2FA) supported in the UI.

---

## 🚀 Instalacja / Installation

### [PL] Przez HACS (Zalecane)
1. Kliknij niebieski przycisk **"Open Repo in HACS"** na górze tego pliku.
2. Jeśli przycisk nie działa, wejdź w **HACS -> Integracje -> Trzy kropki -> Niestandardowe repozytoria**.
3. Wklej link: `https://github.com/iwanstudio/ha-ezviz-dl03-pro` i wybierz kategorię **Integracja**.
4. Pobierz i zrestartuj Home Assistant.

### [EN] Via HACS (Recommended)
1. Click the blue **"Open Repo in HACS"** button at the top of this file.
2. If the button doesn't work, go to **HACS -> Integrations -> Three dots -> Custom repositories**.
3. Paste the link: `https://github.com/iwanstudio/ha-ezviz-dl03-pro` and select category **Integration**.
4. Download and restart Home Assistant.

---

## ⚙️ Konfiguracja / Configuration

### [PL] Dodawanie urządzenia
Przejdź do **Ustawienia -> Urządzenia oraz usługi -> Dodaj integrację** i wyszukaj: `Ezviz DL03 Pro Lock`.
Wymagane dane: **Email, Hasło, Numer seryjny urządzenia.** Dane są sprawdzane od razu; jeśli konto ma weryfikację dwuetapową, pojawi się pole na kod.

### [EN] Adding the device
Go to **Settings -> Devices & Services -> Add Integration** and search for: `Ezviz DL03 Pro Lock`.
Required data: **Email, Password, Device Serial Number.** Credentials are verified; accounts with 2FA get a code step.

### Opcje / Options (Konfiguruj / Configure)
| Opcja / Option | Domyślnie / Default | Opis / Description |
|---|---|---|
| Push (MQTT) | ✅ | Natychmiastowe zdarzenia / instant events |
| Odpytywanie bez push / Polling without push | 5 s | Tylko gdy push nie działa / only when push is unavailable |
| Auto „zamknięcie” / Auto relock | 25 s | 0 = nigdy / never |
| Zdalne sterowanie / Remote control | ❌ | Dodaje encję `lock` / adds a `lock` entity |

### Przykład automatyzacji / Automation example
```yaml
triggers:
  - trigger: state
    entity_id: event.zamek_dl03_pro_bf3639401_aktywnosc_zamka
conditions:
  - condition: state
    entity_id: event.zamek_dl03_pro_bf3639401_aktywnosc_zamka
    attribute: event_type
    state: unlocked
actions:
  - action: notify.notify
    data:
      message: "{{ trigger.to_state.attributes.user }} otworzył(a) drzwi ({{ trigger.to_state.attributes.method }})"
```

---

## ⚠️ Disclaimer
[PL] Ten projekt jest nieoficjalny i nie jest powiązany z firmą Ezviz. Używasz go na własną odpowiedzialność.
[EN] This project is unofficial and not affiliated with Ezviz. Use it at your own risk.

---
<img width="324" height="625" alt="image" src="https://github.com/user-attachments/assets/4d669524-f151-4cce-8219-72ae93dcabd9" />


## 🛠 Autor / Author
Stworzone przez **iwanstudio**. Jeśli Ci się podoba, zostaw ⭐!
Created by **iwanstudio**. If you like it, leave a ⭐!
