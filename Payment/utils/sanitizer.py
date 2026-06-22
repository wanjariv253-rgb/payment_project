import re
from rest_framework import serializers

def sanitize_input(value, field_name="field"):

    if value is None or value == "":
        return value

    if isinstance(value, str):
        value = value.strip()

        # HTML tags detect
        if re.search(r"<[^>]+>", value):
            raise serializers.ValidationError(
                f"{field_name} contains HTML tags."
            )

        # XSS keywords detect
        if re.search(
            r"(script|alert|onerror|onload|javascript:)",
            value,
            re.IGNORECASE
        ):
            raise serializers.ValidationError(
                f"{field_name} contains malicious content."
            )

        return value

    elif isinstance(value, list):
        return [sanitize_input(v, field_name) for v in value]

    elif isinstance(value, dict):
        return {
            k: sanitize_input(v, field_name)
            for k, v in value.items()
        }

    return value