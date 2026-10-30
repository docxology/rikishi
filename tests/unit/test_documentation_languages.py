import pytest

from rikishi.ontology import OntologyIndex


@pytest.mark.parametrize("languages,expected", [
    (["ChineseLanguage", "EnglishLanguage", "EnglishWrittenLanguage"],
     "EnglishWrittenLanguage definition"),
    (["ChineseLanguage", "EnglishLanguage"], "EnglishLanguage definition"),
    (["ZuluLanguage", "ChineseLanguage"], "ChineseLanguage definition"),
])
def test_search_prefers_current_english_with_deterministic_fallback(tmp_path, languages, expected):
    source = tmp_path / "sources"
    source.mkdir()
    (source / "terms.kif").write_text("\n".join(
        f'(documentation Human {language} "{language} definition")'
        for language in languages
    ))
    index = OntologyIndex(tmp_path / "ontology.sqlite")
    index.build(source)
    result = index.search("Human")
    assert len(result) == 1
    assert result[0]["documentation"] == expected
