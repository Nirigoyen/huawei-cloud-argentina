import json
import os

import pytest


def load_spec():
    assert os.path.exists("openapi.json"), "openapi.json not found"
    with open("openapi.json") as f:
        return json.load(f)


def test_spec_exists():
    load_spec()


def test_openapi_version():
    spec = load_spec()
    version = spec.get("openapi", "")
    assert version.startswith("3.0"), f"OpenAPI version must be 3.0.x, got {version}"


def test_info_section():
    spec = load_spec()
    info = spec.get("info", {})
    assert "title" in info, "Missing info.title"
    assert "version" in info, "Missing info.version"


def test_has_paths():
    spec = load_spec()
    paths = spec.get("paths", {})
    assert "/books" in paths, "Missing /books path"
    assert "/books/{book_id}" in paths, "Missing /books/{book_id} path"


def test_get_books_endpoint():
    spec = load_spec()
    path = spec["paths"]["/books"]
    assert "get" in path, "Missing GET /books"
    get_op = path["get"]
    assert "responses" in get_op
    assert "200" in get_op["responses"], "Missing 200 response for GET /books"


def test_post_books_endpoint():
    spec = load_spec()
    path = spec["paths"]["/books"]
    assert "post" in path, "Missing POST /books"
    post_op = path["post"]
    assert "requestBody" in post_op, "Missing request body for POST /books"
    assert "201" in post_op["responses"], "Missing 201 response for POST /books"


def test_get_book_by_id():
    spec = load_spec()
    path = spec["paths"]["/books/{book_id}"]
    assert "get" in path, "Missing GET /books/{book_id}"
    assert "put" in path, "Missing PUT /books/{book_id}"
    assert "delete" in path, "Missing DELETE /books/{book_id}"


def test_has_components_schemas():
    spec = load_spec()
    components = spec.get("components", {})
    schemas = components.get("schemas", {})
    assert "Book" in schemas, "Missing Book schema"
    assert "BookCreate" in schemas, "Missing BookCreate schema"


def test_book_schema_properties():
    spec = load_spec()
    book_schema = spec["components"]["schemas"]["Book"]
    properties = book_schema.get("properties", {})
    for prop in ["id", "title", "author", "isbn", "available"]:
        assert prop in properties, f"Missing {prop} in Book schema"


def test_delete_response_204():
    spec = load_spec()
    delete_op = spec["paths"]["/books/{book_id}"]["delete"]
    assert "204" in delete_op["responses"], "Missing 204 response for DELETE"


def test_query_parameters():
    spec = load_spec()
    get_op = spec["paths"]["/books"]["get"]
    params = get_op.get("parameters", [])
    param_names = [p.get("name") for p in params]
    assert "author" in param_names, "Missing author query parameter"
    assert "available" in param_names, "Missing available query parameter"
