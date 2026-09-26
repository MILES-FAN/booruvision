from booruvision.formatting import TagFormat, format_tag, join_tags


def test_parse_is_case_insensitive_and_defaults_to_booru():
    assert TagFormat.parse("booru") is TagFormat.BOORU
    assert TagFormat.parse("Stable Diffusion") is TagFormat.STABLE_DIFFUSION
    assert TagFormat.parse("stable diffusion") is TagFormat.STABLE_DIFFUSION
    assert TagFormat.parse("nonsense") is TagFormat.BOORU


def test_stable_diffusion_format_escapes_parentheses():
    assert format_tag("hatsune_miku_(cosplay)", TagFormat.STABLE_DIFFUSION) == r"hatsune miku \(cosplay\)"
    assert format_tag("hatsune_miku_(cosplay)", TagFormat.BOORU) == "hatsune_miku_(cosplay)"


def test_join_tags_keeps_order_and_separator():
    tags = {"1girl": 0.99, "long_hair": 0.8}
    assert join_tags(tags, TagFormat.BOORU, comma_separated=False) == "1girl long_hair"
    assert join_tags(tags, TagFormat.STABLE_DIFFUSION, comma_separated=True) == "1girl, long hair"
