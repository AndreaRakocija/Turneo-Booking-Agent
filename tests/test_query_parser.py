from app.query_parser import RuleBasedQueryParser


def test_rule_based_parser_parses_month_and_year_with_currency():
    parser = RuleBasedQueryParser()

    parsed = parser.parse_booking_query("Show me bookings in November 2024 in USD")

    assert parsed["start_date"] == "2024-11-01"
    assert parsed["end_date"] == "2024-11-30"
    assert parsed["currency"] == "USD"


def test_rule_based_parser_defaults_to_eur_when_no_currency():
    parser = RuleBasedQueryParser()

    parsed = parser.parse_booking_query("Show me bookings in March 2023")

    assert parsed["start_date"] == "2023-03-01"
    assert parsed["end_date"] == "2023-03-31"
    # default
    assert parsed["currency"] == "EUR"


def test_rule_based_parser_raises_on_unparseable_query():
    parser = RuleBasedQueryParser()

    try:
        parser.parse_booking_query("just some random text")
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "Could not parse query" in str(e)
