import enum
import json
from dataclasses import dataclass
from typing import Optional, Self
import sqlite3

from aiogram.types import Document, Message

class OnAddTrack(enum.Enum):
    NoDocument = -1
    NotGPX = -2
    TooMany = -3
    Success = 1

@dataclass
class Track:
    file_name: str 
    document_id: str 
    unique_id: str

    def serialize(self) -> str:
        return json.dumps({"file_name": self.file_name, "document_id": self.document_id, "unique_id": self.unique_id})

    @classmethod
    def load(cls, data: str) -> Optional[Self]:
        try:
            d = json.loads(data)
            return cls(file_name=d["file_name"], document_id=d["document_id"], unique_id=d["unique_id"])
        except:
            return None

class TracksStorage:
    @classmethod
    def start(cls) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
        connection = sqlite3.connect("./db.sql")
        cursor = connection.cursor()
        
        cursor.execute("create table if not exists chats (id integer primary key, username text)")
        cursor.execute("create table if not exists tracks (id integer primary key autoincrement, chat_id integer, data text, foreign key(chat_id) references chats(id))")

        return connection, cursor
    
    @staticmethod
    def stop(connection: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
        connection.commit()
        cursor.close()
        connection.close()

    @classmethod
    def try_add_track(cls, message: Message) -> tuple[OnAddTrack, str]:
        connection, cursor = cls.start()
        cursor.execute("insert into chats(id, username) values(?, ?) on conflict(id) do update set username=excluded.username", (message.chat.id, message.chat.username or "-"))
        if not message.document:
            cls.stop(connection, cursor)
            return OnAddTrack.NoDocument, ""
        if message.document.mime_type not in ("application/gpx+xml", "application/octet-stream"):
            cls.stop(connection, cursor)
            return OnAddTrack.NotGPX, message.document.mime_type or "Unknown"
        cursor.execute("select count(*) as count from tracks where chat_id = ?", [message.chat.id])
        count = cursor.fetchone()[0]
        if count > 10:
            cls.stop(connection, cursor)
            return OnAddTrack.TooMany, str(count)
        track = Track(
            file_name=message.document.file_name or "unnamed.gpx",
            document_id=message.document.file_id,
            unique_id=message.document.file_unique_id
        )
        cursor.execute("insert into tracks(chat_id, data) values(?, ?)", [ 
            message.chat.id, track.serialize() 
        ])
        cls.stop(connection, cursor)
        return OnAddTrack.Success, track.file_name
    
    @classmethod
    def list_tracks(cls, message: Message) -> list[Track]:
        connection, cursor = cls.start()
        cursor.execute("select data from tracks where chat_id = ?", [message.chat.id])
        result = [x for x in [
            Track.load(x[0]) for x in cursor.fetchall()
        ] if x]
        cls.stop(connection, cursor)
        return result
    
    @classmethod
    def clear_tracks(cls, message: Message) -> None:
        connection, cursor = cls.start()
        cursor.execute("delete from tracks where chat_id = ?", [message.chat.id])
        cls.stop(connection, cursor)

