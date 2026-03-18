# Ezviz DL03 Pro Integration for Home Assistant 🚪🔓

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Maintainer](https://img.shields.io/badge/maintainer-Piotrek-blue.svg)](https://github.com/TWOJA_NAZWA_UZYTKOWNIKA)

Nieoficjalna integracja dla zamka inteligentnego **Ezviz DL03 Pro**, stworzona specjalnie dla modeli, które nie są poprawnie obsługiwane przez oficjalną integrację Ezviz w Home Assistant.

## ✨ Funkcje
Integracja wyciąga z chmury Ezviz dane, które zazwyczaj są ukryte dla standardowych sensorów:
- **Stan Rygla** (Zablokowany / Odblokowany) - Klasa urządzenia: `lock`.
- **Stan Drzwi** (Zamknięte / Otwarte) - Klasa urządzenia: `door`.
- **Poziom Baterii** (%) - Z dokładnym śledzeniem zużycia.
- **Status Online** - Informacja o połączeniu zamka z siecią Wi-Fi.

## 🚀 Instalacja

### Metoda 1: HACS (Zalecana)
1. Upewnij się, że masz zainstalowany [HACS](https://hacs.xyz/).
2. W Home Assistant przejdź do **HACS** -> **Integracje**.
3. Kliknij trzy kropki w prawym górnym rogu i wybierz **Niestandardowe repozytoria** (Custom Repositories).
4. Wklej URL tego repozytorium: `https://github.com/TWOJA_NAZWA_UZYTKOWNIKA/ha-ezviz-dl03-pro`.
5. Jako kategorię wybierz **Integracja**.
6. Kliknij **Dodaj**, a następnie **Pobierz** w oknie integracji.
7. **Zrestartuj Home Assistant.**

### Metoda 2: Ręczna
1. Pobierz zawartość folderu `custom_components/ezviz_dl03/`.
2. Wklej ją do folderu `/config/custom_components/ezviz_dl03/` w Twojej instalacji HA.
3. **Zrestartuj Home Assistant.**

## ⚙️ Konfiguracja
Integracja posiada pełny **Config Flow**, co oznacza brak konieczności edycji plików YAML:
1. Przejdź do **Ustawienia** -> **Urządzenia oraz usługi**.
2. Kliknij **Dodaj integrację**.
3. Wyszukaj na liście **Ezviz DL03 Pro**.
4. Wypełnij formularz:
   - **Email/Użytkownik**: Twój login do aplikacji Ezviz.
   - **Hasło**: Twoje hasło do aplikacji Ezviz.
   - **Numer Seryjny**: Numer seryjny Twojego zamka (9 cyfr).
   - **Region**: Domyślnie `eu`.

## 📊 Przykładowa Karta (Lovelace)
Aby uzyskać wygląd z czerwono-zielonymi statusami, zalecamy użycie karty `tile` lub dodatku `Mushroom Cards`.

```yaml
type: entities
title: Zamek Wejściowy
entities:
  - entity: binary_sensor.ezviz_lock_status
    name: Stan Rygla
  - entity: binary_sensor.ezviz_door_status
    name: Skrzydło Drzwi
  - entity: sensor.ezviz_battery_level
