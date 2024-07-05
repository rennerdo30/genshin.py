import os
import typing

import pytest

import genshin


class LiteralCharacter(genshin.models.BaseCharacter): ...


LiteralCharacter.__pre_root_validators__ = LiteralCharacter.__pre_root_validators__[:-1]

lang = "en-us"  # initiate local scope


@pytest.mark.parametrize(
    ("data", "expected"),
    (
        # complete should give an identity
        (
            {
                "id": 10000002,
                "name": "Kamisato Ayaka",
                "element": "Cryo",
                "rarity": 5,
                "icon": "https://enka.network/ui/UI_AvatarIcon_Ayaka.png",
            },
            LiteralCharacter(
                id=10000002,
                name="Kamisato Ayaka",
                element="Cryo",
                rarity=5,
                icon="https://enka.network/ui/UI_AvatarIcon_Ayaka.png",
                lang="en-us",
            ),
        ),
        # partial should provide the proper name
        (
            {
                "id": 10000003,
                "icon": "https://upload-os-bbs.mihoyo.com/game_record/genshin/character_side_icon/UI_AvatarIcon_Side_Qin.png",
            },
            LiteralCharacter(
                id=10000003,
                name="Jean",
                element="Anemo",
                rarity=5,
                icon="https://enka.network/ui/UI_AvatarIcon_Qin.png",
                lang="en-us",
            ),
        ),
        # partial for an unknown character should return the icon name
        (
            {
                "id": 10000001,
                "icon": "https://upload-os-bbs.mihoyo.com/game_record/genshin/character_icon/UI_AvatarIcon_Signora.png",
                "rarity": 6,
            },
            LiteralCharacter(
                id=10000001,
                name="Signora",
                element="Anemo",  # Anemo is the arbitrary fallback
                rarity=6,  # 5 is the arbitrary fallback
                icon="https://enka.network/ui/UI_AvatarIcon_Signora.png",
                lang="en-us",
            ),
        ),
        # traveler element should be kept
        (
            {
                "id": 10000005,
                "name": "Traveler",
                "element": "Light",
                "rarity": 5,
            },
            LiteralCharacter(
                id=10000005,
                name="Traveler",
                element="Light",
                rarity=5,
                icon="https://enka.network/ui/UI_AvatarIcon_PlayerBoy.png",
                lang="en-us",
            ),
        ),
        # messed up icon should be replaced
        (
            {
                "id": 10000041,
                "name": "Mona",
                "element": "Hydro",
                "rarity": 5,
                "icon": "https://uploadstatic-sea.hoyoverse.com/hk4e/e20200928calculate/item_icon_ud09dc/9a8c420feda33f36680839c8b8dc1d83.png",
            },
            LiteralCharacter(
                id=10000041,
                name="Mona",
                element="Hydro",
                rarity=5,
                icon="https://enka.network/ui/UI_AvatarIcon_Mona.png",
                lang="en-us",
            ),
        ),
        # messed up icon for unknown character should be kept
        (
            {
                "id": 10000000,
                "name": "Katherine",
                "element": "Geo",
                "rarity": 6,
                "icon": "https://uploadstatic-sea.hoyoverse.com/hk4e/e20200928calculate/item_icon_ud09dc/1dbbc3a2852c11033e1754314d9b292d.png",
            },
            LiteralCharacter(
                id=10000000,
                name="Katherine",
                element="Geo",
                rarity=6,
                icon="https://uploadstatic-sea.hoyoverse.com/hk4e/e20200928calculate/item_icon_ud09dc/1dbbc3a2852c11033e1754314d9b292d.png",
                lang="en-us",
            ),
        ),
        # foreign languages should be kept
        (
            {
                "id": 10000046,
                "name": "胡桃",
                "element": "Pyro",
                "rarity": 5,
                "icon": "https://enka.network/ui/UI_AvatarIcon_Hutao.png",
            },
            LiteralCharacter(
                id=10000046,
                name="胡桃",
                element="Pyro",
                rarity=5,
                icon="https://enka.network/ui/UI_AvatarIcon_Hutao.png",
                lang="en-us",
            ),
        ),
    ),
)
def test_genshin_base_character_model(data: typing.Dict[str, typing.Any], expected: genshin.models.BaseCharacter):
    assert genshin.models.BaseCharacter(**data, lang="en-us") == expected


# reserialization stuff

all_models: typing.Dict[typing.Type[genshin.models.APIModel], genshin.models.APIModel] = {}


def APIModel___new__(cls: typing.Type[genshin.models.APIModel], *args: typing.Any, **kwargs: typing.Any):
    self = object.__new__(cls)
    all_models[cls] = self
    return self


genshin.models.APIModel.__new__ = APIModel___new__


def test_model_reserialization():
    for cls, model in sorted(all_models.items(), key=lambda pair: pair[0].__name__):
        cls(**model.dict())

        if hasattr(model, "as_dict"):
            getattr(model, "as_dict")()

    # dump all parsed models
    data = ",\n".join(
        f'"{cls.__name__}": {model.json(indent=4, ensure_ascii=False, models_as_dict=True)}'
        for cls, model in all_models.items()
    )
    data = "{" + data + "}"
    os.makedirs(".pytest_cache", exist_ok=True)
    with open(".pytest_cache/hoyo_parsed.json", "w", encoding="utf-8") as file:
        file.write(data)
