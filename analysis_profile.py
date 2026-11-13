"""Perfis reproduziveis para filtrar e priorizar achados tecnicos."""

from __future__ import annotations

from copy import copy
from dataclasses import dataclass
import hashlib
import json
from typing import Any


SCHEMA_VERSION = 1
PRESETS = {
    "conservador": "ALTA",
    "equilibrado": "MEDIA",
    "completo": "BAIXA",
}
# Regras ativas por padrao em cada preset. Cada preset ativa somente as regras
# capazes de produzir achados no seu limiar de confianca; o conjunto deve ficar
# sincronizado com PROFILE_PRESETS em vscode-extension/src/profileCatalog.ts.
PRESET_CATEGORIES = {
    "conservador": frozenset({
        "DADO_HARDCODED", "CRIPTOGRAFIA_FRACA", "DADO_EM_LOG",
        "TRANSFERENCIA_SEM_BASE_LEGAL", "AUSENCIA_EXCLUSAO", "CAMPO_SEM_HASH",
        "DADO_SENSIVEL_COMO_PK",
    }),
}
PRESET_CATEGORIES["equilibrado"] = PRESET_CATEGORIES["conservador"] | {
    "DADO_SEM_CRIPTOGRAFIA", "COLETA_EXCESSIVA", "AUSENCIA_SOFT_DELETE",
    "MISTURA_DADOS", "DADO_SENSIVEL_COMO_INDICE_UNICO",
}
CONFIANCA_ORDEM = {"BAIXA": 0, "MEDIA": 1, "ALTA": 2}
RISCOS = {"ALTO", "MEDIO", "BAIXO"}
CATEGORIES = {
    "DADO_HARDCODED", "DADO_SEM_CRIPTOGRAFIA", "CRIPTOGRAFIA_FRACA",
    "DADO_EM_LOG", "TRANSFERENCIA_SEM_BASE_LEGAL", "COLETA_EXCESSIVA",
    "AUSENCIA_EXCLUSAO", "CAMPO_SEM_HASH", "AUSENCIA_SOFT_DELETE",
    "AUSENCIA_RETENCAO", "MISTURA_DADOS", "AUSENCIA_CONSENTIMENTO",
    "DADO_SENSIVEL_COMO_PK", "DADO_SENSIVEL_COMO_INDICE_UNICO",
}
PRESET_CATEGORIES["completo"] = frozenset(CATEGORIES)


def preset_enables(preset: str, category: str) -> bool:
    """Indica se a regra esta ativa por padrao no preset informado."""
    return category in PRESET_CATEGORIES[preset]


class ProfileValidationError(ValueError):
    """Erro de configuracao que deve ser apresentado ao usuario."""


@dataclass(frozen=True)
class AnalysisProfile:
    preset: str
    categories: dict[str, dict[str, Any]]
    source: str = "padrao"

    def public_metadata(self) -> dict[str, str]:
        canonical = {
            "schemaVersion": SCHEMA_VERSION,
            "preset": self.preset,
            "categories": self.categories,
        }
        digest = hashlib.sha256(
            json.dumps(canonical, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        return {"preset": self.preset, "origem": self.source, "hash": digest}


def parse_profile(value: Any = None, *, source: str = "requisicao") -> AnalysisProfile:
    """Valida o contrato publico e retorna o perfil conservador por padrao."""
    if value is None:
        return AnalysisProfile("conservador", {}, "padrao")
    if not isinstance(value, dict):
        raise ProfileValidationError("O campo 'profile' deve ser um objeto JSON.")
    unknown_root = set(value) - {"schemaVersion", "preset", "categories"}
    if unknown_root:
        raise ProfileValidationError(
            f"Opcoes desconhecidas: {', '.join(sorted(unknown_root))}."
        )

    version = value.get("schemaVersion", SCHEMA_VERSION)
    if type(version) is not int or version != SCHEMA_VERSION:
        raise ProfileValidationError(
            f"schemaVersion deve ser {SCHEMA_VERSION}; recebido: {version!r}."
        )
    preset = value.get("preset", "conservador")
    if not isinstance(preset, str) or preset not in PRESETS:
        raise ProfileValidationError(
            "preset deve ser conservador, equilibrado ou completo."
        )
    categories = value.get("categories", {})
    if not isinstance(categories, dict):
        raise ProfileValidationError("categories deve ser um objeto.")

    normalized: dict[str, dict[str, Any]] = {}
    for raw_name, raw_options in categories.items():
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ProfileValidationError("Toda categoria deve possuir nome textual.")
        if raw_name not in CATEGORIES:
            raise ProfileValidationError(f"Categoria desconhecida: {raw_name}.")
        if not isinstance(raw_options, dict):
            raise ProfileValidationError(f"A categoria {raw_name!r} deve ser um objeto.")
        unknown = set(raw_options) - {"enabled", "minimumConfidence", "severity"}
        if unknown:
            raise ProfileValidationError(
                f"Opcoes desconhecidas em {raw_name}: {', '.join(sorted(unknown))}."
            )
        enabled = raw_options.get("enabled", preset_enables(preset, raw_name))
        confidence = raw_options.get("minimumConfidence", PRESETS[preset])
        severity = raw_options.get("severity")
        if not isinstance(enabled, bool):
            raise ProfileValidationError(f"enabled de {raw_name} deve ser booleano.")
        if not isinstance(confidence, str) or confidence not in CONFIANCA_ORDEM:
            raise ProfileValidationError(
                f"minimumConfidence de {raw_name} deve ser ALTA, MEDIA ou BAIXA."
            )
        if severity is not None and (
            not isinstance(severity, str) or severity not in RISCOS
        ):
            raise ProfileValidationError(
                f"severity de {raw_name} deve ser ALTO, MEDIO ou BAIXO."
            )
        normalized[raw_name] = {
            "enabled": enabled,
            "minimumConfidence": confidence,
            **({"severity": severity} if severity else {}),
        }
    return AnalysisProfile(preset, normalized, source)


def apply_profile(findings: list, profile: AnalysisProfile) -> list:
    """Filtra copias dos achados; nunca altera o resultado bruto do analisador."""
    selected = []
    preset_minimum = PRESETS[profile.preset]
    for finding in findings:
        category = str(finding.categoria)
        options = profile.categories.get(category, {})
        enabled = options.get(
            "enabled",
            preset_enables(profile.preset, category) if category in CATEGORIES else True,
        )
        if enabled is False:
            continue
        confidence = str(getattr(finding, "confianca", "ALTA"))
        if confidence not in CONFIANCA_ORDEM:
            confidence = "BAIXA"
        minimum = options.get("minimumConfidence", preset_minimum)
        if CONFIANCA_ORDEM[confidence] < CONFIANCA_ORDEM[minimum]:
            continue

        public_finding = copy(finding)
        public_finding.confianca = confidence
        public_finding.risco_base = str(
            getattr(finding, "risco_base", None) or finding.risco
        )
        if options.get("severity"):
            public_finding.risco = options["severity"]
        selected.append(public_finding)
    return selected
