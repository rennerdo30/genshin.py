# genshin.py

[![Downloads](https://pepy.tech/badge/genshin)](https://pepy.tech/project/genshin)
[![PyPI package](https://img.shields.io/pypi/v/genshin)](https://pypi.org/project/genshin/)
[![Last Commit](https://img.shields.io/github/last-commit/thesadru/genshin.py)](https://github.com/thesadru/genshin.py/commits/master)
[![Coverage](https://img.shields.io/codeclimate/coverage/thesadru/genshin.py)](https://codeclimate.com/github/thesadru/genshin.py)
[![Discord](https://img.shields.io/discord/570841314200125460?color=7289DA)](https://discord.gg/sMkSKRPuCR)

Modern API wrapper for Genshin Impact & Honkai Impact 3rd built on asyncio and pydantic.

---

Documentation: https://thesadru.github.io/genshin.py

API Reference: https://thesadru.github.io/genshin.py/pdoc/genshin

Source Code: https://github.com/thesadru/genshin.py

---

The primary focus of genshin.py is convenience. The entire project is fully type-hinted and abstracts a large amount of the api to be easier to use.

Key features:

- All data is in the form of Pydantic Models which means full autocompletion and linter support.
- Requests are significantly faster thanks to proper usage of asyncio.
- Chinese and Engrish names returned by the API are renamed to simpler English fields.
- Supports the majority of the popular endpoints.
- Cleanly integrates with frameworks like FastAPI out of the box.

> Note: This library is a successor to [genshinstats](https://github.com/thesadru/genshinstats) - an unofficial wrapper for the Genshin Impact api.

## Requirements

- Python 3.9+
- aiohttp
- Pydantic

```console
pip install genshin
```

## Example

A very simple example of how genshin.py would be used:

```py
import asyncio
import genshin

async def main():
    cookies = {"ltuid": 119480035, "ltoken": "cnF7TiZqHAAvYqgCBoSPx5EjwezOh1ZHoqSHf7dT"}
    client = genshin.Client(cookies)

    data = await client.get_genshin_user(710785423)
    print(f"User has a total of {data.stats.characters} characters")

asyncio.run(main())
```

## Contributing

Any kind of contribution is welcome.
Please read [CONTRIBUTING.md](./CONTRIBUTING.md) to see what you need to do to make a contribution.
