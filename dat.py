from __future__ import annotations

import sqlite3

from dataclasses import dataclass

import dat

db = sqlite3.Connection("link.db")
cursor = db.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS link (
    uuid TEXT,
    ign TEXT,
    nickname TEXT,
    discordid TEXT UNIQUE
);""")


@dataclass
class Link:
    uuid: str
    ign: str
    nickname: str
    discordid: str


def get_link(search: str) -> Link | None:
    cmd = "SELECT uuid, ign, nickname, discordid FROM link WHERE discordid IS ? OR uuid is ? OR ign is ?"
    req = cursor.execute(cmd, (search, search, search))
    dat = cursor.fetchone()
    if dat is None:
        return None

    return Link(
        uuid=dat[0],
        ign=dat[1],
        nickname=dat[2],
        discordid=dat[3]
    )


def set_link(discid: str, uuid: str, ign: str, nickname: str) -> bool:
    if get_link(discid) is not None:
        return False

    cmd = """
    INSERT INTO link (uuid, ign, nickname, discordid)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(discordid) DO UPDATE SET
        uuid = excluded.uuid,
        ign = excluded.ign,
        nickname = excluded.nickname
    """
    req = cursor.execute(cmd, (uuid, ign, nickname, discid))
    dat.db.commit()
    return True
