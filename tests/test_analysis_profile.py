from types import SimpleNamespace

import pytest

from analysis_profile import (
    ProfileValidationError,
    apply_profile,
    parse_profile,
)
from server import app


def finding(category="DADO_EM_LOG", confidence="ALTA", risk="ALTO"):
    return SimpleNamespace(
        categoria=category,
        confianca=confidence,
        risco=risk,
        arquivo="fixture.py",
        linha=1,
    )


def test_default_profile_is_conservative_and_reproducible():
    profile = parse_profile()
    assert profile.preset == "conservador"
    assert profile.public_metadata()["origem"] == "padrao"
    assert len(profile.public_metadata()["hash"]) == 16


def test_conservative_filters_lower_confidence():
    selected = apply_profile(
        [finding(confidence="ALTA"), finding(confidence="MEDIA")],
        parse_profile(),
    )
    assert [item.confianca for item in selected] == ["ALTA"]


def test_category_can_override_threshold_and_severity_without_mutating_raw():
    raw = finding(confidence="MEDIA", risk="MEDIO")
    profile = parse_profile({
        "schemaVersion": 1,
        "preset": "conservador",
        "categories": {
            "DADO_EM_LOG": {
                "minimumConfidence": "MEDIA",
                "severity": "BAIXO",
            }
        },
    })
    selected = apply_profile([raw], profile)
    assert selected[0].risco == "BAIXO"
    assert selected[0].risco_base == "MEDIO"
    assert raw.risco == "MEDIO"


@pytest.mark.parametrize("value", [[], {"preset": "x"}, {"categories": []}])
def test_invalid_profile_is_rejected(value):
    with pytest.raises(ProfileValidationError):
        parse_profile(value)


@pytest.mark.parametrize("version", [True, 1.0, "1"])
def test_schema_version_requires_a_real_integer(version):
    with pytest.raises(ProfileValidationError):
        parse_profile({"schemaVersion": version})


@pytest.mark.parametrize("field", ["preset", "minimumConfidence", "severity"])
@pytest.mark.parametrize("value", [[], {}, True, 1, 1.5])
def test_profile_choices_reject_non_text_values(field, value):
    profile = (
        {"preset": value}
        if field == "preset"
        else {"categories": {"DADO_EM_LOG": {field: value}}}
    )
    with pytest.raises(ProfileValidationError):
        parse_profile(profile)


def test_null_severity_preserves_default_risk():
    profile = parse_profile({"categories": {"DADO_EM_LOG": {"severity": None}}})
    assert "severity" not in profile.categories["DADO_EM_LOG"]
    assert apply_profile([finding(risk="MEDIO")], profile)[0].risco == "MEDIO"


@pytest.mark.parametrize("profile", [
    {"preset": []},
    {"categories": {"DADO_EM_LOG": {"minimumConfidence": []}}},
    {"categories": {"DADO_EM_LOG": {"severity": {}}}},
])
def test_invalid_profile_types_return_structured_400(tmp_path, profile):
    response = app.test_client().post(
        "/api/analyze-directory",
        json={"directory": str(tmp_path), "profile": profile},
    )
    assert response.status_code == 400
    assert response.is_json
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["codigo"] == "PERFIL_INVALIDO"
