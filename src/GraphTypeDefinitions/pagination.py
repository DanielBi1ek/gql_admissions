import typing

import strawberry


async def resolve_page(
    info: strawberry.Info,
    model_cls: typing.Any,
    where: typing.Optional[typing.Any],
    skip: typing.Optional[int],
    limit: typing.Optional[int],
    orderby: typing.Optional[str],
    desc: typing.Optional[bool],
    offset: typing.Optional[int],
    *,
    extendedfilter: typing.Optional[dict] = None,
) -> typing.List[typing.Any]:
    if offset is not None:
        skip = offset
    loader = model_cls.getLoader(info=info)
    wheredict = None if where is None else strawberry.asdict(where)
    kwargs = {
        "where": wheredict,
        "skip": skip or 0,
        "limit": limit,
        "orderby": orderby,
        "desc": desc,
    }
    if extendedfilter is not None:
        kwargs["extendedfilter"] = extendedfilter
    rows = await loader.page(**kwargs)
    return [model_cls.from_dataclass(row) for row in rows]
