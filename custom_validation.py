# Class to make customs validations
# By Ed Scrimaglia

from typing import Any, Annotated
from pydantic import validate_call, Field, FieldSerializationInfo
import pytz
from datetime import datetime
from dateutil import parser


# Annotated types for function arguments validation
LitstAny = Annotated[list[Any], Field(title="list to validate uniqueness")]

class ValidateUniqueInList():
    @classmethod
    @validate_call
    def validate_unique_list_objects(cls, lista: LitstAny) -> list:
        if not lista is None:        
            unique_list = []
            for ele in lista:
                if ele in unique_list:
                    raise ValueError(f"list of {lista[0].__class__.__name__} has not unique objects")
                unique_list.append(ele)
        return lista

class ValidateDate():
    @classmethod
    def make_utc(cls, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        else:
            dt = dt.astimezone(pytz.utc)
        return dt
    
    @classmethod
    def parse_datetime(cls, value: Any):
        if isinstance(value, str):
            try:
                return parser(value)
            except Exception as ex:
                raise ValueError(str(ex))
        return value
    
    @classmethod
    def dt_serializer(cls, dt, info: FieldSerializationInfo) -> datetime | str:
        if info.mode_is_json():
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return dt
    
class ValidateListToStr():
    @classmethod
    @validate_call
    def convert_list_to_str(cls, lista: list) -> str:
        
        return str(lista)
        