import argparse
from pathlib import Path
import re


def extract_type_and_key(block: str) -> tuple[str, str]:
    """Extract entry type (e.g., 'book') and citation key (e.g., 'akao1990')."""
    type_match = re.search(r'@([a-zA-Z0-9_-]+)', block)
    key_match = re.search(r'@[a-zA-Z0-9_-]+\s*\{\s*([^,\s]+)', block)

    entry_type = type_match.group(1).lower() if type_match else ''
    citation_key = key_match.group(1).lower() if key_match else ''

    return entry_type, citation_key


def parse_blocks(content: str):
    header_lines = []
    entries = []
    i = 0
    n = len(content)

    while i < n:
        if content[i] == '@':
            start_idx = i
            brace_count = 0
            found_open_brace = False

            while i < n:
                char = content[i]
                if char == '{':
                    brace_count += 1
                    found_open_brace = True
                elif char == '}':
                    brace_count -= 1

                i += 1

                if found_open_brace and brace_count == 0:
                    break

            while i < n and content[i] in ' \t':
                i += 1
            if i < n and content[i] == '\n':
                i += 1

            block = content[start_idx:i]
            entry_type, key = extract_type_and_key(block)

            if entry_type in ('comment', 'preamble', 'string'):
                if not entries:
                    header_lines.append(block)
            else:
                entries.append((entry_type, key, block))
        else:
            if not entries:
                header_lines.append(content[i])
            i += 1

    header = ''.join(header_lines)
    return header, entries


def sort_bib(input_path: Path, output_path: Path) -> None:
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    header, entries = parse_blocks(content)

    # Primary sort: Entry Type (@book, @software)
    # Secondary sort: Citation Key
    entries.sort(key=lambda x: (x[0], x[1]))

    with open(output_path, 'w', encoding='utf-8') as f:
        if header:
            f.write(header.strip() + '\n\n')

        current_type = None
        for entry_type, key, block in entries:
            if current_type and current_type != entry_type:
                f.write(
                    f'% ==========================================\n%  '
                    f'{entry_type.upper()}\n%'
                    ' ==========================================\n\n'
                )
            current_type = entry_type

            f.write(block.strip() + '\n\n')

    print(
        f"✓ Processed {len(entries)} entries -> Saved to '{output_path.name}'"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            'Sort BibTeX file entries strictly by type, then by key within'
            ' each type.'
        )
    )
    parser.add_argument('input', type=Path, help='Path to input .bib file')
    parser.add_argument(
        'output',
        type=Path,
        nargs='?',
        default=None,
        help='Path to output .bib file (defaults to input_sorted.bib)',
    )

    args = parser.parse_args()
    input_file = args.input.resolve()

    if not input_file.is_file():
        raise FileNotFoundError(f"Input file not found: '{input_file}'")

    # If no output path is given, create input_sorted.bib to avoid overwriting
    if args.output:
        output_file = args.output.resolve()
    else:
        output_file = input_file.with_name(
            f'{input_file.stem}_sorted{input_file.suffix}'
        )

    sort_bib(input_file, output_file)


if __name__ == '__main__':
    main()
