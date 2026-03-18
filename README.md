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
![Version](https://img.shields.io/badge/version-v2.6.0-blue.svg)
![Maintainer](https://img.shields.io/badge/maintainer-iwanstudio-blue.svg)

---

### [PL] Opis projektu
Nieoficjalna, zaawansowana integracja dla zamka inteligentnego **Ezviz DL03 Pro**. Stworzona specjalnie dla modeli, które nie są poprawnie obsługiwane przez standardowe rozwiązania. Dzięki mechanizmowi **Fast Listener**, integracja reaguje na zdarzenia (dzwonek, rygiel, otwarcie) niemal w czasie rzeczywistym.

### [EN] Project Description
Unofficial, advanced integration for the **Ezviz DL03 Pro** smart lock. Specifically designed for models not fully supported by standard integrations. Featuring a **Fast Listener** mechanism for near real-time response to events like doorbell rings, lock status, and door opening.

---

## ✨ Funkcje / Features

* **Real-time Status:** Szybka aktualizacja stanu rygla i drzwi / Near instant lock and door status updates.
* **Doorbell:** Natychmiastowe powiadomienia o naciśnięciu dzwonka / Immediate doorbell ring notifications.
* **Event Log:** Sensor rozpoznający osoby (zgodnie z aplikacją EZVIZ) / User identification (as defined in EZVIZ app).
* **Battery:** Precyzyjny poziom baterii (%) / Accurate battery level monitoring.
* **Dynamic Icons:** Ikony zmieniające się w zależności od stanu / State-dependent dynamic icons.

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
Wymagane dane: **Email, Hasło, Numer seryjny urządzenia.**

### [EN] Adding the device
Go to **Settings -> Devices & Services -> Add Integration** and search for: `Ezviz DL03 Pro Lock`.
Required data: **Email, Password, Device Serial Number.**

---

## ⚠️ Disclaimer
[PL] Ten projekt jest nieoficjalny i nie jest powiązany z firmą Ezviz. Używasz go na własną odpowiedzialność.
[EN] This project is unofficial and not affiliated with Ezviz. Use it at your own risk.

---

## 🛠 Autor / Author
Stworzone przez **iwanstudio**. Jeśli Ci się podoba, zostaw ⭐!
Created by **iwanstudio**. If you like it, leave a ⭐!
