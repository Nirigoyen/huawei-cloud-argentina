import re
from collections import defaultdict

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider

SPANISH_INDICATORS = re.compile(
    r"[áéíóúñü¿¡]|"
    r"\b(el|la|los|las|de|del|en|es|un|una|por|con|para|que|su|se|al|lo|como|más|"
    r"pero|sus|le|ya|o|fue|este|ha|sí|porque|cada|cé|est|está|todo|esta|son|"
    r"entre|esta|cuando|muy|sin|sobre|ser|también|me|hasta|hay|donde|quien|"
    r"desde|todo|nos|ni|tal|ellos|ellas|nosotros|usted|ustedes|yo|tú|él|ella|"
    r"nosotras|vosotras|vosotros|ellos|mío|mía|tuyo|tuya|suyo|suya|nuestro|"
    r"nuestra|vuestro|vuestra)\b",
    re.IGNORECASE,
)

FALSE_POSITIVES_ALLOWLIST = frozenset(
    {
        "Estamos",
        "IA",
        "Discovery",
        "Cloud",
        "estamos",
        "están",
        "estás",
        "estoy",
        "estaba",
        "estará",
        "tienen",
        "tenemos",
        "tengo",
        "puede",
        "pueden",
        "hacer",
        "hacemos",
        "sabemos",
        "saben",
        "queremos",
        "quieren",
        "debemos",
        "deben",
        "vamos",
        "vienen",
        "dicen",
        "dijo",
        "ai",
        "llm",
        "api",
        "sql",
        "html",
        "css",
        "json",
        "ok",
        "si",
        "no",
        "ya",
        "yo",
        "tu",
        "el",
    }
)

LANGS = ["en", "es"]


def detect_language(text: str) -> str:
    matches = len(SPANISH_INDICATORS.findall(text))
    return "es" if matches >= 2 else "en"


def _add_recognizer_per_lang(registry, entity, patterns, lang_list, context=None):
    for lang in lang_list:
        kwargs = {
            "supported_entity": entity,
            "supported_language": lang,
            "patterns": patterns,
        }
        if context:
            kwargs["context"] = context
        registry.add_recognizer(PatternRecognizer(**kwargs))


def _create_analyzer() -> AnalyzerEngine:
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [
            {"lang_code": "es", "model_name": "es_core_news_md"},
            {"lang_code": "en", "model_name": "en_core_web_lg"},
        ],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(languages=LANGS, nlp_engine=nlp_engine)

    cc_termination = Pattern(
        name="cc_termination",
        regex=r"(?i)(?:terminada en\s*)(\d{4})",
        score=0.95,
    )
    cc_grouped = Pattern(
        name="cc_grouped",
        regex=r"\b(\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}(?:[\s\-]\d{3})?)\b",
        score=0.85,
    )
    cc_full = Pattern(
        name="cc_full",
        regex=r"\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?:[\s\-]?\d{3})?)\b",
        score=0.75,
    )
    cc_last4 = Pattern(
        name="cc_last4",
        regex=(
            r"(?i)(?:(?:tarjeta|visa|mastercard|amex|crédito|débito|"
            r"card|credit|debit)[^\d]{0,20})(\d{4})\b"
        ),
        score=0.85,
    )
    _add_recognizer_per_lang(
        registry,
        "CREDIT_CARD",
        [cc_termination, cc_grouped, cc_full, cc_last4],
        LANGS,
    )

    address_full = Pattern(
        name="address_full",
        regex=(
            r"(?i)(?:Avenida|Av\.|Calle|Paseo|Pasaje|Boulevard|Blvd\.|"
            r"Camino|Ruta|Diagonal|Plaza|Edificio)\s+"
            r"[a-zA-ZáéíóúñÁÉÍÓÚÑ\s]+?\s+\d{1,5}"
        ),
        score=0.95,
    )
    _add_recognizer_per_lang(registry, "LOCATION", [address_full], LANGS)

    brand_pattern = Pattern(
        name="financial_brand",
        regex=(
            r"(?i)\b(Visa|Mastercard|Amex|American Express|Maestro|"
            r"Diners Club|Discover|Naranja|Cabal|Argencard)\b"
        ),
        score=0.95,
    )
    _add_recognizer_per_lang(registry, "ORGANIZATION", [brand_pattern], LANGS)

    dni_pattern = Pattern(
        name="dni_ar",
        regex=r"(?i)(?:(?:DNI|documento|cedula|cédula|identidad)[^\d]{0,15})(\d{7,8})\b",
        score=0.95,
    )
    _add_recognizer_per_lang(registry, "DNI", [dni_pattern], LANGS)

    phone_pattern = Pattern(
        name="phone_es",
        regex=r"(?:(?:\+34|\+54)\s?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b",
        score=0.5,
    )
    _add_recognizer_per_lang(
        registry,
        "PHONE_NUMBER",
        [phone_pattern],
        LANGS,
        context=["teléfono", "telefono", "celular", "móvil", "movil", "phone", "cell"],
    )

    return AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=LANGS,
    )


_analyzer: AnalyzerEngine | None = None


def _get_analyzer() -> AnalyzerEngine:
    global _analyzer
    if _analyzer is None:
        _analyzer = _create_analyzer()
    return _analyzer


def _analyze_and_filter(text: str, language: str):
    raw_results = _get_analyzer().analyze(
        text=text,
        language=language,
        score_threshold=0.6,
    )
    filtered = []
    for result in raw_results:
        entity_text = text[result.start : result.end]
        if entity_text not in FALSE_POSITIVES_ALLOWLIST:
            filtered.append(result)
    return filtered


def _remove_overlapping(results):
    filtered = []
    for result in results:
        if not filtered:
            filtered.append(result)
            continue
        prev = filtered[-1]
        if result.start < prev.end:
            if result.score > prev.score:
                filtered[-1] = result
        else:
            filtered.append(result)
    return filtered


def anonymize_text(text: str) -> tuple[str, dict[str, str]]:
    language = detect_language(text)

    analyzer_results = _analyze_and_filter(text, language)

    if not analyzer_results:
        return text, {}

    sorted_results = sorted(analyzer_results, key=lambda r: r.start)
    sorted_results = _remove_overlapping(sorted_results)

    entity_counters: dict[str, int] = defaultdict(int)
    mapping: dict[str, str] = {}
    replacements: list[tuple[int, int, str]] = []

    for result in sorted_results:
        entity_type = result.entity_type
        entity_counters[entity_type] += 1
        placeholder = f"<{entity_type}_{entity_counters[entity_type]}>"
        original_value = text[result.start : result.end]
        mapping[placeholder] = original_value
        replacements.append((result.start, result.end, placeholder))

    anonymized_text = text
    offset = 0
    for start, end, placeholder in replacements:
        adjusted_start = start + offset
        adjusted_end = end + offset
        anonymized_text = (
            anonymized_text[:adjusted_start] + placeholder + anonymized_text[adjusted_end:]
        )
        offset += len(placeholder) - (end - start)

    return anonymized_text, mapping


def deanonymize_text(text: str, mapping: dict[str, str]) -> str:
    result = text
    sorted_mapping = sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True)
    for placeholder, original in sorted_mapping:
        result = result.replace(placeholder, original)
    return result
