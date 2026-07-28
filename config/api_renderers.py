"""
Custom JSON renderers for converting between camelCase and snake_case
"""
import json
import re
from rest_framework.renderers import JSONRenderer


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def convert_dict_keys_to_camel(data):
    """Recursively convert all dict keys from snake_case to camelCase"""
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = to_camel_case(key) if isinstance(key, str) else key
            new_dict[new_key] = convert_dict_keys_to_camel(value)
        return new_dict
    elif isinstance(data, list):
        return [convert_dict_keys_to_camel(item) for item in data]
    else:
        return data


class CamelCaseJSONRenderer(JSONRenderer):
    """
    JSON renderer that converts all dictionary keys from snake_case to camelCase
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is not None:
            data = convert_dict_keys_to_camel(data)
        return super().render(data, accepted_media_type, renderer_context)
