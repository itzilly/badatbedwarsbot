from __future__ import annotations

import sqlite3

from dataclasses import dataclass
from enum import Enum
from typing import List

import dat

db = sqlite3.Connection("link.db")
cursor = db.cursor()
# Links
cursor.execute("""CREATE TABLE IF NOT EXISTS link (
    uuid TEXT,
    ign TEXT,
    nickname TEXT,
    discordid TEXT UNIQUE
);""")
# Roles
cursor.execute("""CREATE TABLE IF NOT EXISTS roleinfo (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL,
    roleid TEXT
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


@dataclass
class StarRole:
    roleid: str
    color: str
    prestige: str


@dataclass
class StonePrestige(StarRole):
    roleid = None
    color = "#AAAAAA"
    prestige = "✫ Stone"


@dataclass
class IronPrestige(StarRole):
    roleid = None
    color = "#FFFFFF"
    prestige = "✫ Iron"


@dataclass
class GoldPrestige(StarRole):
    roleid = None
    color = "#FFAA00"
    prestige = "✫ Gold"


@dataclass
class DiamondPrestige(StarRole):
    roleid = None
    color = "#55FFFF"
    prestige = "✫ Diamond"


@dataclass
class EmeraldPrestige(StarRole):
    roleid = None
    color = "#00AA00"
    prestige = "✫ Emerald"


@dataclass
class SapphirePrestige(StarRole):
    roleid = None
    color = "#00AAAA"
    prestige = "✫ Sapphire"


@dataclass
class RubyPrestige(StarRole):
    roleid = None
    color = "#AA0000"
    prestige = "✫ Ruby"


@dataclass
class CrystalPrestige(StarRole):
    roleid = None
    color = "#FF55FF"
    prestige = "✫ Crystal"


@dataclass
class OpalPrestige(StarRole):
    roleid = None
    color = "#5555FF"
    prestige = "✫ Opal"


@dataclass
class AmethystPrestige(StarRole):
    roleid = None
    color = "#AA00AA"
    prestige = "✫ Amethyst"


StarPrestiges = [
    StonePrestige,
    IronPrestige,
    GoldPrestige,
    DiamondPrestige,
    EmeraldPrestige,
    SapphirePrestige,
    RubyPrestige,
    CrystalPrestige,
    OpalPrestige,
    AmethystPrestige
    ]


def update_star_role_id(prestige: StarRole, roleid: int):
    cmd = """
    INSERT INTO roleinfo (name, roleid, color) 
    VALUES (?, ?, ?) 
    ON CONFLICT(name) DO UPDATE SET 
    roleid = excluded.roleid, 
    color = excluded.color
    """
    req = cursor.execute(cmd, (prestige.prestige, str(roleid), prestige.color))
    db.commit()


def fetch_role_id(prestige_role: StarRole) -> int:
    cmd = "SELECT roleid FROM roleinfo WHERE name = ?"
    req = cursor.execute(cmd, (prestige_role.prestige,))
    result = req.fetchone()
    if result is None:
        return -1
    role_id = int(result[0])
    return role_id
