from langflow.template.field.base import TemplateField
from langflow.template.field.fields import RootField
from pydantic import BaseModel


from typing import Callable, Optional, Union


class Template(BaseModel):
    type_name: str
    fields: list[TemplateField]
    root_field: Optional[RootField] = None

    def process_fields(
        self,
        name: Optional[str] = None,
        format_field_func: Union[Callable, None] = None,
    ):
        if format_field_func:
            for field in self.fields:
                format_field_func(field, name)

    def to_dict(self, format_field_func=None):
        self.process_fields(self.type_name, format_field_func)
        result: dict = {field.name: field.to_dict() for field in self.fields}
        result["_type"] = self.type_name  # type: ignore
        if self.root_field:
            result["root_field"] = self.root_field.to_dict()
        return result