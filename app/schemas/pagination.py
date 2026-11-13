from enum import Enum
from math import ceil

from fastapi import Query
from pydantic import BaseModel

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class PageParams:
    """Parâmetros de paginação aprovados em D05/D06."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Pagination(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


def build_pagination(params: PageParams, total_items: int) -> Pagination:
    return Pagination(
        page=params.page,
        page_size=params.page_size,
        total_items=total_items,
        total_pages=ceil(total_items / params.page_size),
    )
