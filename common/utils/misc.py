import json
import re

def extractJSON(text: str):
    # This pattern looks for ```json, captures everything until the closing ```
    pattern = re.compile(r'```json\n(.*?)```', re.DOTALL)
    match = pattern.search(text)
    if match:
        return match.group(1)
    else:
        json.loads(text)
        return text
    return None
