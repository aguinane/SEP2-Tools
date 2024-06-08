import hashlib
import logging
from itertools import zip_longest
from uuid import uuid4

log = logging.getLogger(__name__)

# When generatating IDs, the PEN should always be used at the end
# to ensure that there are no conflicts between entities


def group_hex(item: str, group_size: int = 4) -> str:
    """Group into groups of four"""

    def grouper(iterable, n, fillvalue=None):
        args = [iter(iterable)] * n
        return zip_longest(*args, fillvalue=fillvalue)

    return "-".join("".join(x) for x in grouper(item, n=group_size))


def generate_mrid(pen: int, group: bool = True) -> str:
    """Generate an random mRID"""
    random_hex = uuid4().hex
    mrid = f"{random_hex[0:24]}{pen:08}".upper()
    if not group:
        return mrid
    return group_hex(mrid)


def proxy_device_lfdi(pen: int, con_id: str, group: bool = True) -> str:
    """Generate a LFDI for use by a cloud proxy"""
    id_hash = hashlib.sha256(con_id.encode("utf-8")).hexdigest().upper()
    lfdi = f"{id_hash[0:32]}{pen:08}"
    if not group:
        return lfdi
    return group_hex(lfdi)
