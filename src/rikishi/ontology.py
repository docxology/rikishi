import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
from contextlib import closing
from pathlib import Path

from rikishi.kif import KifError, String, parse, symbols

SCHEMA = """
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE files (path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, formulas INTEGER NOT NULL);
CREATE TABLE formulas (id INTEGER PRIMARY KEY, path TEXT NOT NULL, line INTEGER NOT NULL,
                       text TEXT NOT NULL, predicate TEXT NOT NULL);
CREATE TABLE terms (name TEXT PRIMARY KEY);
CREATE TABLE occurrences (formula_id INTEGER NOT NULL, term TEXT NOT NULL);
CREATE TABLE edges (subject TEXT NOT NULL, predicate TEXT NOT NULL, object TEXT NOT NULL,
                    formula_id INTEGER NOT NULL);
CREATE TABLE documentation (term TEXT NOT NULL, language TEXT NOT NULL, text TEXT NOT NULL,
                            formula_id INTEGER NOT NULL);
CREATE INDEX occurrence_term ON occurrences(term);
CREATE INDEX formula_predicate ON formulas(predicate);
CREATE INDEX edge_subject ON edges(subject);
CREATE INDEX edge_object ON edges(object);
CREATE INDEX doc_term ON documentation(term);
"""


class OntologyIndex:
    def __init__(self, path: Path | str):
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        if not self.path.is_file():
            raise FileNotFoundError(f"Ontology index missing: {self.path}. Run rikishi index.")
        connection = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        return connection

    def build(self, source_dir: Path | str) -> dict:
        source = Path(source_dir).resolve()
        paths = sorted(p for p in source.rglob("*.kif") if ".git" not in p.parts)
        if not paths:
            raise FileNotFoundError(f"No .kif files found in {source}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            prefix="index-", suffix=".sqlite", dir=self.path.parent
        )
        os.close(descriptor)
        errors = []
        try:
            with closing(sqlite3.connect(temporary)) as connection:
                connection.executescript(SCHEMA)
                for path in paths:
                    relative = path.relative_to(source).as_posix()
                    raw = path.read_bytes()
                    try:
                        formulas = list(parse(raw.decode("utf-8-sig"), relative))
                    except (UnicodeDecodeError, KifError) as error:
                        errors.append({"path": relative, "message": str(error)})
                        continue
                    connection.execute(
                        "INSERT INTO files VALUES (?,?,?)",
                        (relative, hashlib.sha256(raw).hexdigest(), len(formulas)),
                    )
                    for formula in formulas:
                        expression = formula.expression
                        predicate = (
                            expression[0] if isinstance(expression[0], str) else "<compound>"
                        )
                        cursor = connection.execute(
                            "INSERT INTO formulas(path,line,text,predicate) VALUES (?,?,?,?)",
                            (relative, formula.line, formula.text, predicate),
                        )
                        identity = cursor.lastrowid
                        names = symbols(expression)
                        connection.executemany(
                            "INSERT OR IGNORE INTO terms VALUES (?)", ((n,) for n in names)
                        )
                        connection.executemany(
                            "INSERT INTO occurrences VALUES (?,?)", ((identity, n) for n in names)
                        )
                        if len(expression) == 3 and all(isinstance(x, str) for x in expression):
                            _, subject, target = expression
                            if subject in names and target in names:
                                connection.execute(
                                    "INSERT INTO edges VALUES (?,?,?,?)",
                                    (subject, predicate, target, identity),
                                )
                        if (
                            predicate == "documentation"
                            and len(expression) == 4
                            and isinstance(expression[1], str)
                            and isinstance(expression[2], str)
                            and isinstance(expression[3], String)
                        ):
                            connection.execute(
                                "INSERT INTO documentation VALUES (?,?,?,?)",
                                (expression[1], expression[2], expression[3].value, identity),
                            )
                commit, clean = "unversioned", None
                if (source / ".git").exists():
                    revision = subprocess.run(
                        ["git", "-C", str(source), "rev-parse", "HEAD"],
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=10,
                    )
                    worktree = subprocess.run(
                        ["git", "-C", str(source), "status", "--porcelain"],
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=10,
                    )
                    commit, clean = revision.stdout.strip(), not bool(worktree.stdout)
                metadata = {
                    "source_root": str(source),
                    "source_commit": commit,
                    "source_clean": clean,
                    "parse_errors": errors,
                    "discovered_files": len(paths),
                    "schema_version": 1,
                }
                connection.executemany(
                    "INSERT INTO metadata VALUES (?,?)",
                    ((key, json.dumps(value)) for key, value in metadata.items()),
                )
                connection.commit()
                check = connection.execute("PRAGMA integrity_check").fetchone()[0]
                if check != "ok":
                    raise sqlite3.DatabaseError(check)
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return self.stats()

    def stats(self) -> dict:
        with closing(self._connect()) as connection:
            result = {
                row[0]: json.loads(row[1]) for row in connection.execute("SELECT * FROM metadata")
            }
            for table in ("files", "formulas", "terms", "edges"):
                result[table] = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            result["top_files"] = [
                dict(r)
                for r in connection.execute(
                    "SELECT path,formulas FROM files ORDER BY formulas DESC,path"
                )
            ]
            result["top_predicates"] = [
                dict(r)
                for r in connection.execute(
                    "SELECT predicate,COUNT(*) AS count FROM formulas GROUP BY predicate ORDER BY count DESC,predicate LIMIT 30"
                )
            ]
            result["relations"] = [
                dict(r)
                for r in connection.execute(
                    "SELECT predicate,COUNT(*) AS count FROM edges GROUP BY predicate ORDER BY count DESC,predicate LIMIT 30"
                )
            ]
            return result

    def search(self, query: str, limit: int = 30) -> list[dict]:
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        if not query.strip():
            return []
        pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        with closing(self._connect()) as connection:
            return [
                dict(row)
                for row in connection.execute(
                    """
                SELECT t.name,
                  COALESCE((SELECT d.text FROM documentation d WHERE d.term=t.name
                    ORDER BY d.language='EnglishLanguage' DESC,d.language LIMIT 1),'') AS documentation,
                  (SELECT COUNT(*) FROM occurrences o WHERE o.term=t.name) AS formula_count
                FROM terms t WHERE t.name LIKE ? ESCAPE '\\'
                ORDER BY t.name = ? COLLATE NOCASE DESC,LENGTH(t.name),t.name LIMIT ?
                """,
                    (pattern, query, limit),
                )
            ]

    def term(self, name: str) -> dict:
        with closing(self._connect()) as connection:
            if not connection.execute("SELECT 1 FROM terms WHERE name=?", (name,)).fetchone():
                raise KeyError(name)
            documentation = [
                dict(r)
                for r in connection.execute(
                    """
                SELECT d.text,d.language,f.path,f.line FROM documentation d
                JOIN formulas f ON f.id=d.formula_id WHERE d.term=? ORDER BY d.language,f.id
                """,
                    (name,),
                )
            ]
            formulas = [
                dict(r)
                for r in connection.execute(
                    """
                SELECT f.* FROM formulas f JOIN occurrences o ON o.formula_id=f.id
                WHERE o.term=? ORDER BY f.id LIMIT 100
                """,
                    (name,),
                )
            ]
            count = connection.execute(
                "SELECT COUNT(*) FROM occurrences WHERE term=?", (name,)
            ).fetchone()[0]
            parents = [
                dict(r)
                for r in connection.execute(
                    """
                SELECT DISTINCT object AS name,predicate AS relation FROM edges
                WHERE subject=? AND predicate IN ('subclass','instance','subrelation') ORDER BY relation,name
                """,
                    (name,),
                )
            ]
            children = [
                dict(r)
                for r in connection.execute(
                    """
                SELECT DISTINCT subject AS name,predicate AS relation FROM edges
                WHERE object=? AND predicate IN ('subclass','instance','subrelation') ORDER BY relation,name LIMIT 200
                """,
                    (name,),
                )
            ]
            return {
                "name": name,
                "documentation": documentation,
                "formulas": formulas,
                "formula_count": count,
                "parents": parents,
                "children": children,
            }

    def neighborhood(self, name: str, limit: int = 80) -> dict:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        with closing(self._connect()) as connection:
            if not connection.execute("SELECT 1 FROM terms WHERE name=?", (name,)).fetchone():
                raise KeyError(name)
            edges = [
                dict(r)
                for r in connection.execute(
                    """
                SELECT DISTINCT subject AS source,object AS target,predicate AS relation
                FROM edges WHERE subject=? OR object=? ORDER BY predicate,subject,object LIMIT ?
                """,
                    (name, name, limit),
                )
            ]
        names = {name}
        for edge in edges:
            names.update((edge["source"], edge["target"]))
        return {"nodes": [{"id": n, "label": n} for n in sorted(names)], "edges": edges}

    def export(self, directory: Path | str) -> dict:
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        stats = self.stats()
        stats.pop("source_root", None)
        (target / "corpus.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        (target / "source-manifest.json").write_text(
            json.dumps(self.source_manifest(), indent=2) + "\n", encoding="utf-8"
        )
        return stats

    def source_manifest(self) -> list[dict[str, str | int]]:
        with closing(self._connect()) as connection:
            return [{"path": row["path"], "sha256": row["sha256"], "formulas": row["formulas"]}
                    for row in connection.execute(
                        "SELECT path,sha256,formulas FROM files ORDER BY path"
                    )]

    def assertions(self, predicate: str, source: str = "Merge.kif") -> list[dict]:
        with closing(self._connect()) as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT e.subject,e.object,f.path,f.line,f.text,s.sha256 AS source_sha256 FROM edges e "
                    "JOIN formulas f ON f.id=e.formula_id JOIN files s ON s.path=f.path "
                    "WHERE e.predicate=? AND f.path=? "
                    "ORDER BY f.id",
                    (predicate, source),
                )
            ]
