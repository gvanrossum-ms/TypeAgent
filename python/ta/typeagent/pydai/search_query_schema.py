# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

# TODO: Move this file into knowpro.

from pydantic import BaseModel
from typing import Literal

from .date_time_schema import DateTimeRange


class FacetTerm(BaseModel):
    facet_name: str
    facet_value: str


class EntityTerm(BaseModel):
    name: str
    is_name_pronoun: bool | None
    type: list[str] | None = None
    facets: list[FacetTerm] | None = None


class VerbsTerm(BaseModel):
    words: list[str]
    tense: Literal["Past", "Present", "Future"]


class ActionTerm(BaseModel):
    action_verbs: VerbsTerm | None = None
    actor_entities: list[EntityTerm] | Literal["*"] = "*"
    target_entities: list[EntityTerm] | None = None
    additional_entities: list[EntityTerm] | None = None
    is_informational: bool = False


class SearchFilter(BaseModel):
    action_search_term: ActionTerm | None = None
    entity_search_terms: list[EntityTerm] | None = None
    search_terms: list[str] | None = None
    time_range: DateTimeRange | None = None


class SearchExpr(BaseModel):
    rewritten_query: str
    filters: list[SearchFilter]


class SearchQuery(BaseModel):
    search_expressions: list[SearchExpr]
