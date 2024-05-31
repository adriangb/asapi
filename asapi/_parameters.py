from typing import TypeVar
from typing_extensions import Annotated
from fastapi import Header, Query, Path, Cookie, Form, File


T = TypeVar("T")

FromHeader = Annotated[T, Header()]
FromQuery = Annotated[T, Query()]
FromPath = Annotated[T, Path()]
FromCookie = Annotated[T, Cookie()]
FromForm = Annotated[T, Form()]
FromFile = Annotated[T, File()]
