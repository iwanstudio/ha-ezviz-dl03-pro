# Ezviz DL03 Pro Integration for Home Assistant 🚪🔓
<p align="center">
  <img src="https://raw.githubusercontent.com/iwanstudio/ha-ezviz-dl03-pro/main/branding/logo.png" width="200">
</p>

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-v2.6.0-blue.svg)
![Maintainer](https://img.shields.io/badge/maintainer-iwanstudio-blue.svg)

[PL] Nieoficjalna, zaawansowana integracja dla zamka inteligentnego **Ezviz DL03 Pro**, stworzona specjalnie dla modeli, które nie są poprawnie obsługiwane przez standardowe rozwiązania. Dzięki zastosowaniu mechanizmu **Fast Listener**, integracja reaguje na zdarzenia niemal w czasie rzeczywistym.

[EN] Unofficial, advanced integration for the **Ezviz DL03 Pro** smart lock. Specifically designed for models not fully supported by standard integrations. Featuring a **Fast Listener** mechanism for near real-time event response.

---

## ✨ Funkcje / Features (PL / EN)

* **Real-time Status:** Szybka aktualizacja stanu rygla i drzwi (Listener) / Near instant lock and door status updates.
* **Doorbell:** Natychmiastowe powiadomienia o naciśnięciu dzwonka / Immediate doorbell ring notifications.
* **Event Log:** Sensor "Ostatnie zdarzenie" rozpoznający osoby (zgodnie z użytkownikami stworzonymi w aplikacji EZVIZ) / "Last Event" sensor identifying users (according to users created in the EZVIZ app)
* **Battery:** Precyzyjny poziom baterii (%) / Accurate battery level monitoring.
* **Dynamic Icons:** Ikony zmieniające się w zależności od stanu (otwarte/zamknięte) / Animated-ready icons (open/closed states).

---

## 🚀 Instalacja / Installation

### HACS
1. Otwórz **HACS** w Home Assistant.
2. Kliknij trzy kropki w prawym górnym rogu i wybierz **Niestandardowe repozytoria (Custom repositories)**.
3. Wklej link do tego repozytorium: `https://github.com/iwanstudio/ha-ezviz-dl03-pro`.
4. Wybierz kategorię **Integracja (Integration)**.
5. Kliknij **Pobierz (Download)**, a następnie zrestartuj Home Assistant.

---

## ⚙️ Konfiguracja / Configuration

Po restarcie przejdź do **Ustawienia -> Urządzenia oraz usługi -> Dodaj integrację** i wyszukaj:
`Ezviz DL03 Pro Lock`.

Będziesz potrzebować:
* Email/Login Ezviz
* Hasło
* Numer seryjny zamka (Serial Number)

---

## ⚠️ Disclaimer
[PL] Ten projekt jest nieoficjalny i nie jest powiązany z firmą Ezviz. Używasz go na własną odpowiedzialność.
[EN] This project is unofficial and not affiliated with Ezviz. Use it at your own risk.

---

## 🛠 Autor / Author
Stworzone przez **iwanstudio**. Jeśli Ci się podoba, zostaw ⭐!
Created by **iwanstudio**. If you like it, leave a ⭐!
