from api.models import ClassTypeEnum
from api.parser.registrar import Registrar

def test_parse_period_types():
    types = Registrar.parse_period_types("202101")
    assert types[('40432', 3, '21:05')] == ClassTypeEnum.TEST
    assert types[('44040', 4, '12:20')] == ClassTypeEnum.LECTURE
    assert types[('41340', 1, '12:20')] == ClassTypeEnum.LECTURE
    assert types[('41340', 4, '12:20')] == ClassTypeEnum.LECTURE
    assert types[('41536', 1, '09:05')] == ClassTypeEnum.TEST
    assert types[('41536', 3, '12:20')] == ClassTypeEnum.LAB