import datetime
import typing

import pydantic

from genshin.models.model import Aliased, APIModel, DateTimeField
from genshin.models.zzz.character import ZZZElementType

__all__ = (
    "ShiyuDefense",
    "ShiyuDefenseBangboo",
    "ShiyuDefenseBuff",
    "ShiyuDefenseCharacter",
    "ShiyuDefenseFloor",
    "ShiyuDefenseMonster",
    "ShiyuDefenseNode",
)


class ShiyuDefenseBangboo(APIModel):
    """Shiyu Defense bangboo model."""

    id: int
    rarity: typing.Literal["S", "A"]
    level: int

    @property
    def icon(self) -> str:
        return f"https://act-webstatic.hoyoverse.com/game_record/zzz/bangboo_square_avatar/bangboo_square_avatar_{self.id}.png"


class ShiyuDefenseCharacter(APIModel):
    """Shiyu Defense character model."""

    id: int
    level: int
    rarity: typing.Literal["S", "A"]
    element: ZZZElementType = Aliased("element_type")

    @property
    def icon(self) -> str:
        return (
            f"https://act-webstatic.hoyoverse.com/game_record/zzz/role_square_avatar/role_square_avatar_{self.id}.png"
        )


class ShiyuDefenseBuff(APIModel):
    """Shiyu Defense buff model."""

    name: str = Aliased("title")
    description: str = Aliased("text")


class ShiyuDefenseMonster(APIModel):
    """Shiyu Defense monster model."""

    id: int
    name: str
    weakness: typing.Union[ZZZElementType, int] = Aliased("weak_element_type")
    level: int

    @pydantic.field_validator("weakness", mode="before")
    def __convert_weakness(cls, v: int) -> typing.Union[ZZZElementType, int]:
        try:
            return ZZZElementType(v)
        except ValueError:
            return v


class ShiyuDefenseNode(APIModel):
    """Shiyu Defense node model."""

    characters: list[ShiyuDefenseCharacter] = Aliased("avatars")
    bangboo: ShiyuDefenseBangboo = Aliased("buddy")
    recommended_elements: list[ZZZElementType] = Aliased("element_type_list")
    enemies: list[ShiyuDefenseMonster] = Aliased("monster_info")

    @pydantic.field_validator("enemies", mode="before")
    @classmethod
    def __convert_enemies(cls, value: dict[typing.Literal["level", "list"], typing.Any]) -> list[ShiyuDefenseMonster]:
        level = value["level"]
        result: list[ShiyuDefenseMonster] = []
        for monster in value["list"]:
            monster["level"] = level
            result.append(ShiyuDefenseMonster(**monster))
        return result


class ShiyuDefenseFloor(APIModel):
    """Shiyu Defense floor model."""

    index: int = Aliased("layer_index")
    rating: typing.Literal["S", "A", "B"]
    id: int = Aliased("layer_id")
    buffs: list[ShiyuDefenseBuff]
    node_1: ShiyuDefenseNode
    node_2: ShiyuDefenseNode
    challenge_time: DateTimeField = Aliased("floor_challenge_time")
    name: str = Aliased("zone_name")

    @pydantic.field_validator("challenge_time", mode="before")
    @classmethod
    def __parse_datetime(cls, value: typing.Mapping[str, typing.Any]) -> typing.Optional[DateTimeField]:
        if value:
            return datetime.datetime(**value)
        return None


class ShiyuDefense(APIModel):
    """ZZZ Shiyu Defense model."""

    schedule_id: int
    begin_time: typing.Optional[DateTimeField] = Aliased("hadal_begin_time")
    end_time: typing.Optional[DateTimeField] = Aliased("hadal_end_time")
    has_data: bool
    ratings: typing.Mapping[typing.Literal["S", "A", "B"], int] = Aliased("rating_list")
    floors: list[ShiyuDefenseFloor] = Aliased("all_floor_detail")
    fastest_clear_time: int = Aliased("fast_layer_time")
    """Fastest clear time this season in seconds."""
    max_floor: int = Aliased("max_layer")

    @pydantic.field_validator("begin_time", "end_time", mode="before")
    @classmethod
    def __parse_datetime(cls, value: typing.Mapping[str, typing.Any]) -> typing.Optional[DateTimeField]:
        if value:
            return datetime.datetime(**value)
        return None

    @pydantic.field_validator("ratings", mode="before")
    @classmethod
    def __convert_ratings(
        cls, v: list[dict[typing.Literal["times", "rating"], typing.Any]]
    ) -> typing.Mapping[typing.Literal["S", "A", "B"], int]:
        return {d["rating"]: d["times"] for d in v}
