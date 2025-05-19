import pytest
from app.models.table import Table, ListTablesResponse, Pagination

def test_table_model_required_fields():
    table = Table(
        name="person",
        data_model={"type": "object", "properties": {"id": {"type": "integer"}}},
        description="foo"
    )
    assert table.name == "person"
    assert table.data_model["type"] == "object"

def test_table_model_optional_fields():
    table = Table(
        name="person",
        description="A table of people",
        data_model={},
        errors=[{"title": "example error", "detail": "something went wrong"}]
    )
    assert table.description == "A table of people"
    assert table.errors[0]["title"] == "example error"

def test_list_tables_response_basic():
    response = ListTablesResponse(
        tables=[
            Table(
                name="sample",
                data_model={},
                description="foo"
            )
        ]
    )
    assert len(response.tables) == 1
    assert response.tables[0].name == "sample"

def test_list_tables_response_with_pagination_and_errors():
    response = ListTablesResponse(
        tables=[],
        pagination=Pagination(next_page_url="http://example.com/next"),
        errors=[{"title": "db error", "detail": "connection lost"}]
    )
    assert response.pagination.next_page_url == "http://example.com/next"
    assert response.errors[0]["title"] == "db error"

def test_table_model_validation_error():
    with pytest.raises(ValueError):
        Table(data_model={})
