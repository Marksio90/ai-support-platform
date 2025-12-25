# Contributing to E-commerce Support AI

Dziękujemy za zainteresowanie projektem! 🎉

## To jest projekt pilotażowy (PoC)

Ten projekt to **komercyjny PoC** (Proof of Concept) dla klientów e-commerce.
Nie jest to projekt open-source.

## Dostosowanie do własnych potrzeb

Jeśli chcesz dostosować ten system do swojej firmy:

### 1. Dane i Treningi

**Zamień dane syntetyczne na własne:**

```bash
# Twoje FAQ
data/public/faq.json

# Twoje regulaminy
data/public/regulations.json

# Prawdziwe dialogi supportowe
data/synthetic/support_dialogs.json
```

### 2. Kategorie

**Dostosuj kategorie w backend:**

```python
# backend/app/main.py

categories = {
    "zwrot": [...],
    "dostawa": [...],
    # Dodaj swoje kategorie
    "gwarancja": ["gwarancja", "serwis"],
}
```

### 3. System Prompt

**Zmień ton odpowiedzi:**

```yaml
# llm/model_config.yaml

system_prompt: |
  Jesteś asystentem [NAZWA TWOJEJ FIRMY].
  Zachowuj [TON MARKI: profesjonalny/przyjazny/casual].
  ...
```

### 4. Trening LoRA

**Fine-tune na własnych danych:**

```bash
# 1. Przygotuj dialogi w formacie JSON
# 2. Uruchom trening
cd llm
python train.py --data ../data/your_dialogs.json
```

## Wdrożenie komercyjne

Dla pełnego wdrożenia produkcyjnego, skontaktuj się z nami:

📧 **Email:** sales@ecommerce-support-ai.com
📞 **Telefon:** +48 XXX XXX XXX

Oferujemy:
- ✅ Dedykowany model na Twoich danych
- ✅ Integrację z CRM/ERP
- ✅ Hosting i utrzymanie
- ✅ Support 24/7
- ✅ Continuous learning

## Zgłaszanie problemów

Jeśli znalazłeś bug w projekcie pilotażowym:

1. Sprawdź [Issues](https://github.com/your-repo/issues)
2. Jeśli nie ma podobnego zgłoszenia, utwórz nowe
3. Opisz:
   - Kroki do reprodukcji
   - Oczekiwane zachowanie
   - Aktualne zachowanie
   - Środowisko (OS, Python version, etc.)

## Pull Requests

Ze względu na komercyjny charakter projektu, **nie przyjmujemy pull requestów**
od zewnętrznych kontrybutorów.

Jeśli chcesz współpracować przy rozwoju produktu, skontaktuj się z nami mailowo.

## Licencja

Ten projekt jest objęty licencją proprietary. Zobacz [LICENSE](LICENSE).

---

Dziękujemy za zrozumienie! 🙏
