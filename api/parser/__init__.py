from api.models import ClassTypeEnum


DAY_LETTERS = {"M": 1, "T": 2, "W": 3, "R": 4, "F": 5, "S": 6}

PERIOD_TYPES = {
    "SEM": ClassTypeEnum.SEMINAR,
    "TES": ClassTypeEnum.TEST,
    "LEC": ClassTypeEnum.LECTURE,
    "REC": ClassTypeEnum.RECITATION,
    "LAB": ClassTypeEnum.LAB,
    "STU": ClassTypeEnum.STUDIO,
}