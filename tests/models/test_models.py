from typing import List

import pytest

from models import fill_from, find_none_paths


@pytest.mark.parametrize(
    "source, expected",
    (
        # Replacing None with a primitive value works
        (
            {"foo": 123},
            {
                "foo": 123,
                "foo2": {"bar2": None, "baz2": None},
                "foo3": {"bar3": {"baz3": None}},
            },
        ),
        # Replacing None with a dictionary works
        (
            {"foo": {"bar": 123}},
            {
                "foo": {"bar": 123},
                "foo2": {"bar2": None, "baz2": None},
                "foo3": {"bar3": {"baz3": None}},
            },
        ),
        # Replacing None with a list works
        (
            {"foo": [1, 2, 3]},
            {
                "foo": [1, 2, 3],
                "foo2": {"bar2": None, "baz2": None},
                "foo3": {"bar3": {"baz3": None}},
            },
        ),
        # Nested replacement works
        (
            {"foo2": {"bar2": 123, "baz2": 456}},
            {
                "foo": None,
                "foo2": {"bar2": 123, "baz2": 456},
                "foo3": {"bar3": {"baz3": None}},
            },
        ),
        # Double nested replacement works
        (
            {"foo3": {"bar3": {"baz3": 123}}},
            {
                "foo": None,
                "foo2": {"bar2": None, "baz2": None},
                "foo3": {"bar3": {"baz3": 123}},
            },
        ),
        # Extra source key is excluded
        (
            {"extra": {"bar3": {"baz3": 123}}},
            {
                "foo": None,
                "foo2": {"bar2": None, "baz2": None},
                "foo3": {"bar3": {"baz3": None}},
            },
        ),
    ),
)
def test_fill_from(source: dict, expected: dict):
    assert (
        fill_from(
            source,
            {
                "foo": None,
                "foo2": {"bar2": None, "baz2": None},
                "foo3": {"bar3": {"baz3": None}},
            },
        )
        == expected
    )


def test_fill_from_template_value_preserved():
    """
    Non-null template values should be preserved if they aren't populated by the source object.
    I want this behaviour because it lets me program default values really easily by just putting
    them in the template.
    """
    assert fill_from(
        source={"foo2": {"bar2": 123, "baz2": 456}},
        template={
            "foo": 123,
            "foo2": {"bar2": None, "baz2": None},
            "foo3": {"bar3": {"baz3": None}},
        },
    ) == {
        "foo": 123,
        "foo2": {"bar2": 123, "baz2": 456},
        "foo3": {"bar3": {"baz3": None}},
    }


@pytest.mark.parametrize(
    "obj, expected",
    (
        # Empty list when no None paths
        ({"foo": 123}, []),
        # Base None
        ({"foo": None}, ["foo"]),
        # Nested None
        ({"foo": {"bar": None}}, ["foo.bar"]),
        # Double nested None
        ({"foo": {"bar": {"baz": None}}}, ["foo.bar.baz"]),
        # None inside list
        ({"foo": [123, 456, None]}, ["foo[2]"]),
        # None inside nested list
        ({"foo": {"bar": [123, 456, None]}}, ["foo.bar[2]"]),
        # Nested None inside list
        ({"foo": [123, 456, {"bar": None}]}, ["foo[2].bar"]),
        # Nested None inside nested list
        ({"foo": {"bar": [123, 456, {"baz": None}]}}, ["foo.bar[2].baz"]),
        # Multiple paths returned
        ({"foo": None, "bar": None, "baz": {"aaa": None}}, ["foo", "bar", "baz.aaa"]),
    ),
)
def test_find_none_paths(obj: dict, expected: List[str]):
    assert find_none_paths(obj) == expected
