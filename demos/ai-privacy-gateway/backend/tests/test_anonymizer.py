"""Tests para las funciones puras del anonimizador.

Estos tests no requieren modelos de spaCy porque testean funciones
que no usan el analyzer (detect_language usa regex, deanonymize_text
hace reemplazo de strings). El analyzer es lazy, así que importar
el módulo no descarga modelos.
"""

from app.services.anonymizer import deanonymize_text, detect_language


class TestDetectLanguage:
    def test_detects_spanish(self):
        text = "Mi nombre es Juan García y vivo en Buenos Aires."
        assert detect_language(text) == "es"

    def test_detects_english(self):
        text = "My name is John Smith and I live in New York."
        assert detect_language(text) == "en"

    def test_empty_string_defaults_to_english(self):
        assert detect_language("") == "en"

    def test_single_spanish_word_defaults_to_english(self):
        # Necesita 2+ indicadores para detectar español
        assert detect_language("hola") == "en"

    def test_mixed_text_detects_spanish(self):
        text = "Hola, my name is Carlos y vivo en Madrid con su familia."
        assert detect_language(text) == "es"


class TestDeanonymizeText:
    def test_replaces_single_placeholder(self):
        mapping = {"<PERSON_1>": "Juan García"}
        result = deanonymize_text("Hola, <PERSON_1> cómo estás?", mapping)
        assert result == "Hola, Juan García cómo estás?"

    def test_replaces_multiple_placeholders(self):
        mapping = {"<PERSON_1>": "Juan", "<PHONE_NUMBER_1>": "+54 11 1234-5678"}
        result = deanonymize_text("<PERSON_1> llama al <PHONE_NUMBER_1>", mapping)
        assert result == "Juan llama al +54 11 1234-5678"

    def test_no_placeholders_returns_unchanged(self):
        mapping = {"<PERSON_1>": "Juan"}
        result = deanonymize_text("Texto sin placeholders", mapping)
        assert result == "Texto sin placeholders"

    def test_empty_mapping_returns_unchanged(self):
        result = deanonymize_text("Hola <PERSON_1>", {})
        assert result == "Hola <PERSON_1>"

    def test_placeholder_appears_multiple_times(self):
        mapping = {"<PERSON_1>": "Juan"}
        result = deanonymize_text("<PERSON_1> y <PERSON_1> son la misma persona", mapping)
        assert result == "Juan y Juan son la misma persona"

    def test_overlapping_placeholders_longest_first(self):
        # Los placeholders más largos se reemplazan primero para evitar
        # reemplazos parciales incorrectos
        mapping = {"<CREDIT_CARD_1>": "1234-5678-9012-3456", "<CREDIT_CARD_1_2>": "extra"}
        result = deanonymize_text("Card: <CREDIT_CARD_1>", mapping)
        assert result == "Card: 1234-5678-9012-3456"
