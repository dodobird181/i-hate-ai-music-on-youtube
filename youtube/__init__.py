from typing import List


def fill_from(source: dict, template: dict) -> dict:
    """
    Traverse `template` and fill its values using matching keys from `source`.
    """
    result = {}

    for key, template_value in template.items():
        if isinstance(template_value, dict):
            # Recurse if both sides are dicts
            source_value = source.get(key, {})
            if isinstance(source_value, dict):
                result[key] = fill_from(source_value, template_value)
            else:
                result[key] = fill_from({}, template_value)
        else:
            # Leaf node
            result[key] = source.get(key, template.get(key, None))

    return result


def find_none_paths(obj: dict, _path: str = "") -> List[str]:
    """
    Find all paths leading to None. E.g. {"foo": {"bar": None}} -> ["foo.bar"]
    """

    paths: List[str] = []

    if obj is None:
        paths.append(_path)
        return paths

    if isinstance(obj, dict):
        for k, v in obj.items():
            paths.extend(find_none_paths(v, f"{_path}.{k}" if _path else k))

    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            paths.extend(find_none_paths(v, f"{_path}[{i}]"))

    return paths


from youtube.official_service import OfficialYouTubeService
