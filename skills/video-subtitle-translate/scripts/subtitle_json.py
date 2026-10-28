#!/usr/bin/env python3
"""Validate translated cue JSON; emit plain SRT and styled ASS. Python stdlib only."""
import argparse
import json
import math
import sys
from pathlib import Path


def number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{field} must be a number')
    if not math.isfinite(value):
        raise ValueError(f'{field} must be finite')
    return value


def load_cues(path):
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    rows = data.get('cues') if isinstance(data, dict) else data
    if not isinstance(rows, list) or not rows:
        raise ValueError('Expected a nonempty cues list')
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Each cue must be an object')
        key = row.get('id')
        if not isinstance(key, str) or not key.strip() or key in seen:
            raise ValueError(f'Empty, non-string or duplicate cue ID: {key!r}')
        seen.add(key)
        a, b = number(row.get('start'), key), number(row.get('end'), key)
        if not 0 <= a < b:
            raise ValueError(f'Invalid time range: {key}')
    return rows


def stamp(seconds, ass=False):
    unit = 100 if ass else 1000
    count = round(seconds * unit)
    hour, count = divmod(count, 3600 * unit)
    minute, count = divmod(count, 60 * unit)
    second, fraction = divmod(count, unit)
    if ass:
        return f'{hour}:{minute:02}:{second:02}.{fraction:02}'
    return f'{hour:02}:{minute:02}:{second:02},{fraction:03}'


def ass_plain(text):
    # No caller-supplied override tags or ASS escape sequences are executed.
    return text.replace('\\', '＼').replace('{', '｛').replace('}', '｝').replace('\n', r'\N')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('translated', type=Path)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--duration', type=float)
    parser.add_argument('--font', default='Source Han Sans CN')
    parser.add_argument('--width', type=int, default=1920)
    parser.add_argument('--height', type=int, default=1080)
    parser.add_argument('--font-size', type=float, default=56)
    parser.add_argument('--margin-v', type=int, default=40)
    args = parser.parse_args()
    if args.width <= 240 or args.height <= 0 or args.font_size <= 0 or args.margin_v < 0:
        raise ValueError('Invalid layout dimensions')
    if not math.isfinite(args.font_size):
        raise ValueError('Font size must be finite')
    if not args.font.strip() or any(c in args.font for c in ',\r\n'):
        raise ValueError('Invalid font family')
    if args.duration is not None and (not math.isfinite(args.duration) or args.duration <= 0):
        raise ValueError('Invalid video duration')
    cues = load_cues(args.translated)
    if args.source:
        originals = {c['id']: c for c in load_cues(args.source)}
        translated = {c['id']: c for c in cues}
        if originals.keys() != translated.keys():
            raise ValueError(f'ID mismatch: missing={sorted(originals.keys()-translated.keys())}, extra={sorted(translated.keys()-originals.keys())}')
        for key, row in translated.items():
            if any(abs(row[t] - originals[key][t]) > 1e-6 for t in ('start', 'end')):
                raise ValueError(f'Timing changed: {key}')
    visible, warnings = [], []
    for row in sorted(cues, key=lambda c: (c['start'], c['end'])):
        key = row['id']
        if args.duration is not None and row['end'] > args.duration + .05:
            raise ValueError(f'Cue extends beyond video: {key}')
        text = row.get('zh')
        if not isinstance(text, str):
            raise ValueError(f'Missing translation string: {key}')
        text = text.replace('\r\n', '\n').replace('\r', '\n').strip()
        if not text:
            reason = row.get('skip_reason')
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(f'Empty translation without skip_reason: {key}')
            continue
        if len(text.split('\n')) > 2:
            raise ValueError(f'More than two subtitle lines: {key}')
        if any(ord(c) < 32 and c != '\n' for c in text):
            raise ValueError(f'Control character in translation: {key}')
        if stamp(row['start'], True) == stamp(row['end'], True):
            raise ValueError(f'Cue too short for ASS precision: {key}')
        if len(text.replace('\n', '')) > 56:
            warnings.append(f'Long cue requires layout review: {key}')
        if visible and row['start'] < max(c['end'] for c in visible):
            warnings.append(f'Overlapping cue requires layout review: {key}')
        alignment = row.get('alignment', 2)
        if isinstance(alignment, bool) or not isinstance(alignment, int) or not 1 <= alignment <= 9:
            raise ValueError(f'Invalid alignment: {key}')
        pos = row.get('position')
        if pos is not None:
            if not isinstance(pos, list) or len(pos) != 2:
                raise ValueError(f'Invalid position: {key}')
            x, y = number(pos[0], key), number(pos[1], key)
            if not 0 <= x <= args.width or not 0 <= y <= args.height:
                raise ValueError(f'Position out of bounds: {key}')
        visible.append(dict(row, zh=text))
    print(json.dumps({'total': len(cues), 'translated': len(visible), 'skipped': len(cues)-len(visible), 'warnings': warnings}, ensure_ascii=False))
    if args.check_only:
        return
    if not args.output_dir:
        raise ValueError('--output-dir is required unless --check-only is used')
    if not visible:
        raise ValueError('No visible translated cues to export')
    ass_path, srt_path = args.output_dir/'chinese.ass', args.output_dir/'chinese.srt'
    if ass_path.exists() or srt_path.exists():
        raise FileExistsError('Subtitle outputs already exist; choose a new directory')
    ass = f'''[Script Info]
ScriptType: v4.00+
PlayResX: {args.width}
PlayResY: {args.height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{args.font},{args.font_size:g},&H00FFFFFF,&H00FFFFFF,&H00000000,&HFF000000,0,0,0,0,100,100,0,0,1,2.5,0,2,120,120,{args.margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    srt = []
    for i, row in enumerate(visible, 1):
        tags = ''
        if row.get('position') is not None or row.get('alignment', 2) != 2:
            tags = r'{\an' + str(row.get('alignment', 2))
            if row.get('position') is not None:
                x, y = row['position']
                tags += f'\\pos({x:g},{y:g})'
            tags += '}'
        ass += f"Dialogue: 0,{stamp(row['start'], True)},{stamp(row['end'], True)},Default,,0,0,0,,{tags}{ass_plain(row['zh'])}\n"
        srt.append(f"{i}\n{stamp(row['start'])} --> {stamp(row['end'])}\n{row['zh']}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with ass_path.open('x', encoding='utf-8-sig') as f:
        f.write(ass)
    with srt_path.open('x', encoding='utf-8-sig') as f:
        f.write('\n\n'.join(srt) + '\n')
    print(f'Created {ass_path} and {srt_path}')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
