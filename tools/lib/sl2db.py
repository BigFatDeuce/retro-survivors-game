"""StarLoco SQL dumps (Dofus 1.29 emulator data) -> work/sl.db (sqlite): maps (with their keys), monsters, drops...
Only the tables we need are kept; the values are parsed from the MySQL INSERT lines."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, re, sqlite3, glob

SRC = f'{ROOT}/ext/emu/sl/docker/db-init'
OUT = f'{ROOT}/work/sl.db'
TABLES = {'maps', 'monsters', 'mobgroups_fix', 'drops', 'item_template', 'subarea_data', 'area_data', 'donjons', 'heroic_mobs_groups_fix'}


def parse_values(s, i):
    """parses '(...), (...);' from position i -> list of rows"""
    rows = []; n = len(s)
    while i < n:
        while i < n and s[i] in ' ,\n\r\t': i += 1
        if i >= n or s[i] != '(': break
        i += 1; row = []
        while True:
            while s[i] == ' ': i += 1
            if s[i] == "'":
                i += 1; buf = []
                while True:
                    c = s[i]
                    if c == '\\': buf.append({'n': '\n', 'r': '\r', 't': '\t', '0': '\0'}.get(s[i + 1], s[i + 1])); i += 2; continue
                    if c == "'":
                        if s[i + 1] == "'": buf.append("'"); i += 2; continue
                        i += 1; break
                    buf.append(c); i += 1
                row.append(''.join(buf))
            else:
                j = i
                while s[j] not in ',)': j += 1
                tok = s[i:j].strip(); i = j
                if tok.upper() == 'NULL': row.append(None)
                else:
                    try: row.append(int(tok))
                    except ValueError:
                        try: row.append(float(tok))
                        except ValueError: row.append(tok)
            while s[i] == ' ': i += 1
            if s[i] == ',': i += 1; continue
            if s[i] == ')': i += 1; break
        rows.append(row)
    return rows


def main():
    db = sqlite3.connect(OUT); cols = {}
    for f in sorted(glob.glob(f'{SRC}/*.sql')):
        cur_table = None; cur_cols = []
        for line in open(f, encoding='utf8', errors='replace'):
            m = re.match(r'CREATE TABLE `(\w+)`', line)
            if m: cur_table = m.group(1); cur_cols = []; continue
            if cur_table and line.startswith('  `'):
                cm = re.match(r'\s+`(\w+)`', line)
                if cm: cur_cols.append(cm.group(1))
                continue
            if cur_table and line.startswith(')') and cur_table in TABLES:
                db.execute(f'DROP TABLE IF EXISTS "{cur_table}"')
                db.execute(f'CREATE TABLE "{cur_table}" (' + ','.join(f'"{c}"' for c in cur_cols) + ')')
                cols[cur_table] = cur_cols; cur_table = None; continue
            m = re.match(r'(?:INSERT|REPLACE) INTO `(\w+)`(?: \(([^)]*)\))? VALUES ', line)
            if m and m.group(1) in TABLES and m.group(1) in cols:
                t = m.group(1); names = [x.strip(' `') for x in m.group(2).split(',')] if m.group(2) else cols[t]
                try: rows = parse_values(line, m.end())
                except Exception as e: print('bad line', t, str(e)[:80]); continue
                for r in rows:
                    if len(r) != len(names): continue
                    db.execute(f'INSERT OR REPLACE INTO "{t}" (' + ','.join(f'"{c}"' for c in names) + ') VALUES (' + ','.join('?' * len(r)) + ')', r)
    db.commit()
    for t in cols: print(t, db.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0])


if __name__ == '__main__':
    main()
