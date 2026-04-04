from enum import StrEnum


class LrstDiagnosis(StrEnum):
    """Diagnosen im Zusammenhang mit LRSt."""

    LRST = "lrst"
    ILST = "iLst"
    IRST = "iRst"

    @property
    def long_name(self) -> str:
        """Ausgeschriebene Form der Diagnose."""
        match self:
            case LrstDiagnosis.LRST:
                return "Lese-Rechtschreib-Störung"
            case LrstDiagnosis.ILST:
                return "isolierte Lesestörung"
            case LrstDiagnosis.IRST:
                return "isolierte Rechtschreibstörung"


class LrstTesterType(StrEnum):
    """Fachpersonen, die LRSt-Tests durchführen."""

    SCHPSY = "schpsy"
    PSYCHIA = "psychia"
    PSYCHOTH = "psychoth"
    SPZ = "spz"
    ANDERE = "andere"

    @property
    def numerical_value(self) -> int:
        """Numerischer Wert für PDF-Formulare."""
        match self:
            case LrstTesterType.SCHPSY:
                return 1
            case LrstTesterType.PSYCHIA:
                return 2
            case LrstTesterType.PSYCHOTH:
                return 3
            case LrstTesterType.SPZ:
                return 4
            case LrstTesterType.ANDERE:
                return 5


class Gender(StrEnum):
    """Geschlecht des Klienten."""

    MALE = "m"
    FEMALE = "f"
    DIVERSE = "x"
