from enum import Enum, unique


@unique
class SOPNParsingBackends(Enum):
    TEXTRACT = "AWS Textract"
    CAMELOT = "Camelot"


SOPN_PARSING_BACKENDS = SOPNParsingBackends
DEFAULT_PARSING_BACKEND = SOPNParsingBackends.TEXTRACT
