import json
import re
from pathlib import Path

SEED_PATH = Path('seed.sql')
DESCRIPTIONS_PATH = Path('course_descriptions.json')
OUTPUT_JSON = Path('missing_courses.json')


def extract_codes_from_seed(seed_sql: str) -> set[str]:
    codes: set[str] = set()
    # Collect only values blocks for INSERT INTO courses ... VALUES (...), (...);
    insert_blocks: list[str] = []
    collecting = False
    current_block: list[str] = []

    for line in seed_sql.splitlines():
        if not collecting and line.strip().upper().startswith('INSERT INTO COURSES'):
            collecting = True
            current_block = []
            continue
        if collecting:
            current_block.append(line)
            if ';' in line:
                insert_blocks.append('\n'.join(current_block))
                collecting = False
                current_block = []

    # Regex to capture the 3rd quoted value in each tuple: ('id', 'name', 'CODE', ...)
    tuple_code_pattern = re.compile(r"\(\s*'[^']*'\s*,\s*'[^']*'\s*,\s*'([A-Z]{2,4}\d{4}[A-Z]?)'", re.IGNORECASE | re.DOTALL)

    for block in insert_blocks:
        for match in tuple_code_pattern.finditer(block):
            code = match.group(1).upper()
            codes.add(code)
    return codes


def read_codes_from_descriptions(json_text: str) -> set[str]:
    data = json.loads(json_text)
    return {entry['course_code'].upper() for entry in data if 'course_code' in entry and entry['course_code']}


def main():
    if not SEED_PATH.exists():
        print(f"❌ Missing file: {SEED_PATH}")
        return
    if not DESCRIPTIONS_PATH.exists():
        print(f"❌ Missing file: {DESCRIPTIONS_PATH}")
        return

    seed_sql = SEED_PATH.read_text(encoding='utf-8')
    desc_json = DESCRIPTIONS_PATH.read_text(encoding='utf-8')

    seed_codes = extract_codes_from_seed(seed_sql)
    desc_codes = read_codes_from_descriptions(desc_json)

    missing = sorted(seed_codes - desc_codes)

    OUTPUT_JSON.write_text(json.dumps(missing, indent=2), encoding='utf-8')

    print('============================================================')
    print(f"Total codes in courses table: {len(seed_codes)}")
    print(f"Total codes with descriptions: {len(desc_codes)}")
    print(f"Missing descriptions: {len(missing)}")
    print(f"Output: {OUTPUT_JSON}")
    print('============================================================')
    if missing:
        print('Sample missing:')
        for code in missing[:10]:
            print(f"- {code}")


if __name__ == '__main__':
    main()
