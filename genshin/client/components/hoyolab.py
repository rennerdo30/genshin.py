"""Hoyolab component."""

import asyncio
import typing
import warnings

import yarl

from genshin import types, utility
from genshin.client import cache as client_cache
from genshin.client import routes
from genshin.client.components import base
from genshin.client.manager import managers
from genshin.models import hoyolab as models

__all__ = ["HoyolabClient"]


class HoyolabClient(base.BaseClient):
    """Hoyolab component."""

    async def _get_server_region(self, uid: int, game: types.Game) -> str:
        """Fetch the server region of an account from the API."""
        data = await self.request(
            routes.GET_USER_REGION_URL.get_url(),
            params=dict(game_biz=utility.get_prod_game_biz(self.region, game)),
            cache=client_cache.cache_key("server_region", game=game, uid=uid, region=self.region),
        )
        for account in data["list"]:
            if account["game_uid"] == str(uid):
                return account["region"]

        raise ValueError(f"Failed to recognize server for game {game!r} and uid {uid!r}")

    async def _request_announcements(
        self,
        game: types.Game,
        uid: int,
        *,
        lang: typing.Optional[str] = None,
    ) -> typing.Sequence[models.Announcement]:
        """Get a list of game announcements."""
        if game is types.Game.GENSHIN:
            params = dict(
                game="hk4e",
                game_biz="hk4e_global",
                bundle_id="hk4e_global",
                platform="pc",
                region=utility.recognize_genshin_server(uid),
                uid=uid,
                level=8,
                lang=lang or self.lang,
            )
            url = routes.HK4E_URL.get_url()
        elif game is types.Game.ZZZ:
            params = dict(
                game="nap",
                game_biz="nap_global",
                bundle_id="nap_global",
                platform="pc",
                region=utility.recognize_zzz_server(uid),
                level=60,
                lang=lang or self.lang,
                uid=uid,
            )
            url = routes.NAP_URL.get_url()
        elif game is types.Game.STARRAIL:
            params = dict(
                game="hkrpg",
                game_biz="hkrpg_global",
                bundle_id="hkrpg_global",
                platform="pc",
                region=utility.recognize_starrail_server(uid),
                uid=uid,
                level=70,
                lang=lang or self.lang,
                channel_id=1,
            )
            url = routes.HKRPG_URL.get_url()
        else:
            msg = f"{game!r} is not supported yet."
            raise ValueError(msg)

        info, details = await asyncio.gather(
            self.request_hoyolab(
                url / "announcement/api/getAnnList",
                lang=lang,
                params=params,
            ),
            self.request_hoyolab(
                url / "announcement/api/getAnnContent",
                lang=lang,
                params=params,
            ),
        )

        announcements: list[typing.Mapping[str, typing.Any]] = []
        extra_list: list[typing.Mapping[str, typing.Any]] = (
            info["pic_list"][0]["type_list"] if "pic_list" in info and info["pic_list"] else []
        )
        for sublist in info["list"] + extra_list:
            for info in sublist["list"]:
                detail = next((i for i in details["list"] if i["ann_id"] == info["ann_id"]), None)
                announcements.append({**info, **(detail or {})})

        return [models.Announcement(**i) for i in announcements]

    async def search_users(
        self,
        keyword: str,
        *,
        lang: typing.Optional[str] = None,
    ) -> typing.Sequence[models.PartialHoyolabUser]:
        """Search hoyolab users."""
        data = await self.request_bbs(
            "community/search/wapi/search/user",
            lang=lang,
            params=dict(keyword=keyword, page_size=20),
            cache=client_cache.cache_key("search", keyword=keyword, lang=self.lang),
        )
        return [models.PartialHoyolabUser(**i["user"]) for i in data["list"]]

    async def get_hoyolab_user(
        self,
        hoyolab_id: typing.Optional[int] = None,
        *,
        lang: typing.Optional[str] = None,
    ) -> models.FullHoyolabUser:
        """Get a hoyolab user."""
        if self.region == types.Region.OVERSEAS:
            url = "/community/painter/wapi/user/full"
        elif self.region == types.Region.CHINESE:
            url = "/user/wapi/getUserFullInfo"
        else:
            raise TypeError(f"{self.region!r} is not a valid region.")

        data = await self.request_bbs(
            url=url,
            lang=lang,
            params=dict(uid=hoyolab_id) if hoyolab_id else None,
            cache=client_cache.cache_key("hoyolab", uid=hoyolab_id, lang=lang or self.lang),
        )
        return models.FullHoyolabUser(**data["user_info"])

    async def get_recommended_users(self, *, limit: int = 200) -> typing.Sequence[models.PartialHoyolabUser]:
        """Get a list of recommended active users."""
        data = await self.request_bbs(
            "community/user/wapi/recommendActive",
            params=dict(page_size=limit),
            cache=client_cache.cache_key("recommended"),
        )
        return [models.PartialHoyolabUser(**i["user"]) for i in data["list"]]

    async def get_genshin_announcements(
        self,
        *,
        uid: typing.Optional[int] = None,
        lang: typing.Optional[str] = None,
    ) -> typing.Sequence[models.Announcement]:
        """Get a list of Genshin Impact announcements."""
        if self.cookie_manager.multi:
            uid = uid or await self._get_uid(types.Game.GENSHIN)
        else:
            uid = uid or 900000005
        return await self._request_announcements(types.Game.GENSHIN, uid, lang=lang)

    async def get_zzz_announcements(
        self,
        *,
        uid: typing.Optional[int] = None,
        lang: typing.Optional[str] = None,
    ) -> typing.Sequence[models.Announcement]:
        """Get a list of Zenless Zone Zero announcements."""
        if self.cookie_manager.multi:
            uid = uid or await self._get_uid(types.Game.ZZZ)
        else:
            uid = uid or 1300000000
        return await self._request_announcements(types.Game.ZZZ, uid, lang=lang)

    async def get_starrail_announcements(
        self,
        *,
        uid: typing.Optional[int] = None,
        lang: typing.Optional[str] = None,
    ) -> typing.Sequence[models.Announcement]:
        """Get a list of Star Rail announcements."""
        if self.cookie_manager.multi:
            uid = uid or await self._get_uid(types.Game.STARRAIL)
        else:
            uid = uid or 809162009
        return await self._request_announcements(types.Game.STARRAIL, uid, lang=lang)

    @managers.requires_cookie_token
    async def redeem_code(
        self,
        code: str,
        uid: typing.Optional[int] = None,
        *,
        game: typing.Optional[types.Game] = None,
        lang: typing.Optional[str] = None,
        region: typing.Optional[str] = None,
    ) -> None:
        """Redeems a gift code for the current user."""
        if game is None:
            if self.default_game is None:
                raise RuntimeError("No default game set.")

            game = self.default_game

        if game not in {types.Game.GENSHIN, types.Game.ZZZ, types.Game.STARRAIL, types.Game.TOT}:
            raise ValueError(f"{game} does not support code redemption.")

        uid = uid or await self._get_uid(game)

        try:
            region = region or utility.recognize_server(uid, game)
        except Exception:
            warnings.warn(f"Failed to recognize server for game {game!r} and uid {uid!r}, fetching from API now.")
            region = await self._get_server_region(uid, game)

        await self.request(
            routes.CODE_URL.get_url(self.region, game),
            params=dict(
                uid=uid,
                region=region,
                cdkey=code,
                game_biz=utility.get_prod_game_biz(self.region, game),
                lang=utility.create_short_lang_code(lang or self.lang),
            ),
            method="POST" if game is types.Game.STARRAIL else "GET",
        )

    @managers.no_multi
    async def check_in_community(self) -> None:
        """Check in to the hoyolab community and claim your daily 5 community exp."""
        raise RuntimeError("This API is deprecated.")

    @base.region_specific(types.Region.OVERSEAS)
    async def fetch_mi18n(
        self, url: typing.Union[str, yarl.URL], filename: str, *, lang: typing.Optional[str] = None
    ) -> typing.Mapping[str, str]:
        """Fetch a mi18n file."""
        return await self.request(
            yarl.URL(url) / f"{filename}/{filename}-{lang or self.lang}.json",
            cache=client_cache.cache_key("mi18n", filename=filename, url=url, lang=lang or self.lang),
        )

    @base.region_specific(types.Region.OVERSEAS)
    async def get_mimo_games(self, *, lang: typing.Optional[str] = None) -> typing.Sequence[models.MimoGame]:
        """Get a list of Traveling Mimo games."""
        data = await self.request(
            routes.MIMO_URL.get_url() / "index",
            params=dict(lang=lang or self.lang),
        )
        return [models.MimoGame(**i) for i in data["list"]]

    @base.region_specific(types.Region.OVERSEAS)
    async def _get_mimo_game_data(
        self, game: typing.Union[typing.Literal["hoyolab"], types.Game]
    ) -> typing.Tuple[int, int]:
        games = await self.get_mimo_games()
        mimo_game = next((i for i in games if i.game == game), None)
        if mimo_game is None:
            raise ValueError(f"Game {game!r} not found in the list of Traveling Mimo games.")
        return mimo_game.id, mimo_game.version_id

    @base.region_specific(types.Region.OVERSEAS)
    async def _parse_mimo_args(
        self,
        game_id: typing.Optional[int] = None,
        version_id: typing.Optional[int] = None,
        game: typing.Optional[typing.Union[typing.Literal["hoyolab"], types.Game]] = None,
    ) -> typing.Tuple[int, int]:
        if game_id is None or version_id is None:
            if game is None:
                if self.default_game is None:
                    raise RuntimeError("No default game set.")
                game = self.default_game
            game_id, version_id = await self._get_mimo_game_data(game)
        return game_id, version_id

    @base.region_specific(types.Region.OVERSEAS)
    async def get_mimo_tasks(
        self,
        *,
        game_id: typing.Optional[int] = None,
        version_id: typing.Optional[int] = None,
        game: typing.Optional[typing.Union[typing.Literal["hoyolab"], types.Game]] = None,
        lang: typing.Optional[str] = None,
    ) -> typing.Sequence[models.MimoTask]:
        """Get a list of Traveling Mimo missions (tasks)."""
        game_id, version_id = await self._parse_mimo_args(game_id, version_id, game)
        data = await self.request(
            routes.MIMO_URL.get_url() / "task-list",
            params=dict(game_id=game_id, lang=lang or self.lang, version_id=version_id),
        )
        return [models.MimoTask(**i) for i in data["task_list"]]

    @base.region_specific(types.Region.OVERSEAS)
    async def claim_mimo_task_reward(
        self,
        task_id: int,
        *,
        game_id: typing.Optional[int] = None,
        version_id: typing.Optional[int] = None,
        game: typing.Optional[typing.Union[typing.Literal["hoyolab"], types.Game]] = None,
        lang: typing.Optional[str] = None,
    ) -> None:
        """Claim a Traveling Mimo mission (task) reward."""
        game_id, version_id = await self._parse_mimo_args(game_id, version_id, game)
        await self.request(
            routes.MIMO_URL.get_url() / "receive-point",
            params=dict(task_id=task_id, game_id=game_id, lang=lang or self.lang, version_id=version_id),
        )

    @base.region_specific(types.Region.OVERSEAS)
    async def finish_mimo_task(
        self,
        task_id: int,
        *,
        game_id: typing.Optional[int] = None,
        version_id: typing.Optional[int] = None,
        game: typing.Optional[typing.Union[typing.Literal["hoyolab"], types.Game]] = None,
        lang: typing.Optional[str] = None,
    ) -> None:
        """Finish a Traveling Mimo mission (task) reward."""
        game_id, version_id = await self._parse_mimo_args(game_id, version_id, game)
        await self.request(
            routes.MIMO_URL.get_url() / "finish-task",
            data=dict(task_id=task_id, game_id=game_id, lang=lang or self.lang, version_id=version_id),
            method="POST",
        )

    @base.region_specific(types.Region.OVERSEAS)
    async def get_mimo_shop_items(
        self,
        *,
        game_id: typing.Optional[int] = None,
        version_id: typing.Optional[int] = None,
        game: typing.Optional[typing.Union[typing.Literal["hoyolab"], types.Game]] = None,
        lang: typing.Optional[str] = None,
    ) -> typing.Sequence[models.MimoShopItem]:
        """Get a list of Traveling Mimo shop items."""
        game_id, version_id = await self._parse_mimo_args(game_id, version_id, game)
        data = await self.request(
            routes.MIMO_URL.get_url() / "exchange-list",
            params=dict(game_id=game_id, lang=lang or self.lang, version_id=version_id),
        )
        return [models.MimoShopItem(**i) for i in data["exchange_award_list"]]

    @base.region_specific(types.Region.OVERSEAS)
    async def buy_mimo_shop_item(
        self,
        item_id: int,
        *,
        game_id: typing.Optional[int] = None,
        version_id: typing.Optional[int] = None,
        game: typing.Optional[typing.Union[typing.Literal["hoyolab"], types.Game]] = None,
        lang: typing.Optional[str] = None,
    ) -> str:
        """Buy an item from the Traveling Mimo shop and return a gift code to redeem it."""
        game_id, version_id = await self._parse_mimo_args(game_id, version_id, game)
        data = await self.request(
            routes.MIMO_URL.get_url() / "exchange",
            data=dict(award_id=item_id, game_id=game_id, lang=lang or self.lang, version_id=version_id),
            method="POST",
        )
        return data["exchange_code"]

    @base.region_specific(types.Region.OVERSEAS)
    async def get_mimo_point_count(
        self,
        *,
        game: typing.Optional[typing.Union[typing.Literal["hoyolab"], types.Game]] = None,
    ) -> int:
        """Get the current Traveling Mimo point count."""
        game = game or self.default_game
        games = await self.get_mimo_games()
        mimo_game = next((i for i in games if i.game == game), None)
        if mimo_game is None:
            raise ValueError(f"Game {game!r} not found in the list of Traveling Mimo games.")
        return mimo_game.point
