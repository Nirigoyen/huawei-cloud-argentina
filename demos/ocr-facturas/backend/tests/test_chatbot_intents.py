"""Tests for chatbot intent definitions and query templates.

Covers:
- INTENT_DEFINITIONS structure and completeness
- IntentDefinition model validation
- ALLOWED_TABLES and DENIED_TABLES
- get_intent_names() and get_intent_descriptions_for_prompt()
"""

from app.services.chatbot.intents import (
    ALLOWED_TABLES,
    DENIED_TABLES,
    INTENT_DEFINITIONS,
    IntentDefinition,
    get_intent_descriptions_for_prompt,
    get_intent_names,
)

# =============================================================================
# IntentDefinition model tests
# =============================================================================


class TestIntentDefinition:
    """Tests for the IntentDefinition Pydantic model."""

    def test_valid_intent(self):
        intent = IntentDefinition(
            name="test_intent",
            description="Test description",
            parameter_names=["param1", "param2"],
            sql_template="SELECT * FROM invoices WHERE id = :param1",
            response_template="Result: {param1}",
            example_questions=["What is param1?"],
        )
        assert intent.name == "test_intent"
        assert len(intent.parameter_names) == 2

    def test_empty_parameters(self):
        intent = IntentDefinition(
            name="no_params",
            description="No parameters",
            parameter_names=[],
            sql_template="SELECT COUNT(*) FROM invoices",
            response_template="Count: {count}",
            example_questions=["How many?"],
        )
        assert intent.parameter_names == []


# =============================================================================
# INTENT_DEFINITIONS tests
# =============================================================================


class TestIntentDefinitions:
    """Tests for the INTENT_DEFINITIONS dictionary."""

    def test_not_empty(self):
        assert len(INTENT_DEFINITIONS) > 0

    def test_expected_intents_exist(self):
        expected = [
            "total_spending",
            "top_suppliers",
            "supplier_spending",
            "invoices_above_amount",
            "most_recent_invoice",
            "iva_total",
            "spending_by_month",
            "invoice_count",
        ]
        for name in expected:
            assert name in INTENT_DEFINITIONS, f"Intent '{name}' not found"

    def test_all_intents_are_intent_definition_instances(self):
        for name, intent in INTENT_DEFINITIONS.items():
            assert isinstance(intent, IntentDefinition), f"Intent '{name}' is not an IntentDefinition"

    def test_all_intents_have_names(self):
        for name, intent in INTENT_DEFINITIONS.items():
            assert intent.name == name

    def test_all_intents_have_descriptions(self):
        for name, intent in INTENT_DEFINITIONS.items():
            assert intent.description, f"Intent '{name}' has empty description"

    def test_all_intents_have_sql_templates(self):
        for name, intent in INTENT_DEFINITIONS.items():
            assert intent.sql_template, f"Intent '{name}' has empty SQL template"

    def test_all_intents_have_response_templates(self):
        for name, intent in INTENT_DEFINITIONS.items():
            assert intent.response_template, f"Intent '{name}' has empty response template"

    def test_all_intents_have_example_questions(self):
        for name, intent in INTENT_DEFINITIONS.items():
            assert len(intent.example_questions) > 0, f"Intent '{name}' has no example questions"

    def test_sql_templates_use_parameterized_syntax(self):
        """All SQL templates should use :param_name syntax for parameters."""
        # Some parameters are derived at runtime (e.g., supplier_name -> supplier_pattern)
        derived_params = {"supplier_name": "supplier_pattern"}
        for name, intent in INTENT_DEFINITIONS.items():
            if intent.parameter_names:
                for param in intent.parameter_names:
                    sql_param = derived_params.get(param, param)
                    assert f":{sql_param}" in intent.sql_template, (
                        f"Intent '{name}' SQL template missing parameter ':{sql_param}'"
                    )

    def test_sql_templates_are_select_only(self):
        """All SQL templates should be SELECT queries."""
        for name, intent in INTENT_DEFINITIONS.items():
            upper_sql = intent.sql_template.strip().upper()
            assert upper_sql.startswith("SELECT"), f"Intent '{name}' SQL template is not a SELECT query"


# =============================================================================
# Specific intent tests
# =============================================================================


class TestTotalSpendingIntent:
    """Tests for the total_spending intent."""

    def test_has_date_parameters(self):
        intent = INTENT_DEFINITIONS["total_spending"]
        assert "start_date" in intent.parameter_names
        assert "end_date" in intent.parameter_names

    def test_sql_joins_totals(self):
        intent = INTENT_DEFINITIONS["total_spending"]
        assert "invoice_totals" in intent.sql_template


class TestTopSuppliersIntent:
    """Tests for the top_suppliers intent."""

    def test_has_limit_parameter(self):
        intent = INTENT_DEFINITIONS["top_suppliers"]
        assert "limit" in intent.parameter_names

    def test_sql_has_limit_clause(self):
        intent = INTENT_DEFINITIONS["top_suppliers"]
        assert "LIMIT" in intent.sql_template.upper()


class TestSupplierSpendingIntent:
    """Tests for the supplier_spending intent."""

    def test_has_supplier_name_parameter(self):
        intent = INTENT_DEFINITIONS["supplier_spending"]
        assert "supplier_name" in intent.parameter_names

    def test_sql_uses_ilike(self):
        intent = INTENT_DEFINITIONS["supplier_spending"]
        assert "ILIKE" in intent.sql_template


# =============================================================================
# Table whitelist tests
# =============================================================================


class TestTableWhitelist:
    """Tests for ALLOWED_TABLES and DENIED_TABLES."""

    def test_allowed_tables_not_empty(self):
        assert len(ALLOWED_TABLES) > 0

    def test_denied_tables_not_empty(self):
        assert len(DENIED_TABLES) > 0

    def test_no_overlap(self):
        """Allowed and denied tables must not overlap."""
        overlap = ALLOWED_TABLES & DENIED_TABLES
        assert overlap == set(), f"Tables in both allowed and denied: {overlap}"

    def test_invoices_in_allowed(self):
        assert "invoices" in ALLOWED_TABLES

    def test_chatbot_logs_in_denied(self):
        assert "chatbot_query_logs" in DENIED_TABLES

    def test_app_settings_in_denied(self):
        assert "app_settings" in DENIED_TABLES

    def test_alembic_in_denied(self):
        assert "alembic_version" in DENIED_TABLES


# =============================================================================
# Helper function tests
# =============================================================================


class TestGetIntentNames:
    """Tests for get_intent_names()."""

    def test_returns_list(self):
        names = get_intent_names()
        assert isinstance(names, list)

    def test_contains_expected_intents(self):
        names = get_intent_names()
        assert "total_spending" in names
        assert "top_suppliers" in names
        assert "invoice_count" in names

    def test_count_matches_definitions(self):
        names = get_intent_names()
        assert len(names) == len(INTENT_DEFINITIONS)


class TestGetIntentDescriptionsForPrompt:
    """Tests for get_intent_descriptions_for_prompt()."""

    def test_returns_string(self):
        result = get_intent_descriptions_for_prompt()
        assert isinstance(result, str)

    def test_contains_intent_names(self):
        result = get_intent_descriptions_for_prompt()
        assert "total_spending" in result
        assert "top_suppliers" in result

    def test_contains_parameters(self):
        result = get_intent_descriptions_for_prompt()
        assert "start_date" in result
        assert "end_date" in result
