from rikishi.corpus_query import FileQuery


def test_inventory_is_complete_beyond_display_limits(tmp_path, corpus_factory):
    index = corpus_factory(tmp_path, {"many.kif": "\n".join(
        f"(relation{n:02} A B)" for n in range(35)
    )})
    result = index.relation_inventory()
    assert result["total"] == 35
    assert result["assertion_count"] == result["unique_edges"] == 35
    assert all(row["node_count"] == 2 for row in result["items"])


def test_file_count_ties_keep_ascending_paths(tmp_path, corpus_factory):
    index = corpus_factory(tmp_path, {name: "(instance A B)" for name in
                                     ("z.kif", "a.kif", "m.kif")})
    for descending in (False, True):
        rows = [index.corpus_files(FileQuery(sort="formulas", descending=descending,
                                             limit=1, offset=n))["items"][0]["path"]
                for n in range(3)]
        assert rows == ["a.kif", "m.kif", "z.kif"]
