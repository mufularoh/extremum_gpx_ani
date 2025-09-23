import dataclasses
from typing import Optional
from aiogram import Bot
from flask import Blueprint, render_template, request, send_file
from pathlib import Path
import dartsass
import gpxpy
import gpxpy.gpx
import utm

from .. import storage
from .. import bot
from .. import settings
from .. import download


bp = Blueprint("cropper", __name__, url_prefix="")
s = settings.Settings.load()

async def represent_track(track_obj: storage.Track, b: Bot) -> dict:
    track_ret = dataclasses.asdict(track_obj)
    track_ret["segments"] = []
    min_lat = 10000000000
    min_lng = 10000000000
    max_lat = 0
    max_lng = 0
    d = await download.load_file(b, track_obj.document_id, track_obj.unique_id)
    try:
        reader = gpxpy.parse(d.read_text())
    except gpxpy.gpx.GPXXMLSyntaxException:
        return track_ret
    for track in reader.tracks:
        for segment in track.segments:
            pseg = []
            for point in segment.points:
                utm_point = utm.from_latlon(point.latitude, point.longitude)
                lat = utm_point[0]
                lng = utm_point[1]
                
                if lat > max_lat:
                    max_lat = lat 
                if lat < min_lat:
                    min_lat = lat 
                if lng > max_lng:
                    max_lng = lng 
                if lng < min_lng:
                    min_lng = lng
                pseg.append([lat, lng])
            
            max_len = max((max_lat - min_lat), (max_lng - min_lng))
            lat_offset = (max_len - (max_lat - min_lat)) / (2 * max_len)
            lng_offset = (max_len - (max_lng - min_lng)) / (2 * max_len)

            if max_lat - min_lat != 0 and max_lng - min_lng != 0:
                track_ret["segments"].append([
                    [
                        5 + ((x[0] - min_lat) / (max_len) + lat_offset) * 90,
                        5 + ((x[1] - min_lng) / (max_len) + lng_offset) * 90
                    ] for x in pseg
                ])
    return track_ret

@bp.route("/")
def cropper_landing():
    root = Path(__file__).parent
    sass_p = root.parent / "static/cropper.sass"
    css_code = dartsass.compile(string=sass_p.read_text(), indented=True)
    assert css_code is not None

    return render_template("cropper.html", css_code=css_code)

@bp.route("/download/<int:track_id>/")
async def download_track(track_id):
    b = bot.get_bot(s.api_token)
    track = storage.TracksStorage.get_track(track_id)
    assert track is not None 
    d = await download.load_file(b, track.document_id, track.unique_id)

    return send_file(d, as_attachment=True)

@bp.route("/reset/<int:track_id>/")
async def clear_track(track_id):
    b = bot.get_bot(s.api_token)
    track = storage.TracksStorage.get_track(track_id)
    assert track is not None 
    p = download.get_file_path(track.unique_id)
    if p.exists():
        p.unlink()

    await download.load_file(b, track.document_id, track.unique_id)
    return await represent_track(track, b)


@bp.route("/crop/", methods=["POST"])
async def crop_track():
    assert request.json is not None
    track_id: Optional[int] = request.json.get("track_id", None)
    start_index: Optional[int] = request.json.get("start_index", None)
    end_index: Optional[int] = request.json.get("end_index", None)

    assert track_id is not None
    assert start_index is not None
    assert end_index is not None

    track_db = storage.TracksStorage.get_track(track_id)
    assert track_db is not None


    root = Path(__file__).parent.parent / "files"
    p = (root / f"{track_db.unique_id}.gpx").resolve()
    assert root in p.parents and p.exists()

    reader = gpxpy.parse(p.read_text())
    writer = gpxpy.gpx.GPX()

    b = bot.get_bot(s.api_token)

    i = 0
    for track in reader.tracks:
        w_track = gpxpy.gpx.GPXTrack()
        track_points_exist = False

        for segment in track.segments:
            w_segment = gpxpy.gpx.GPXTrackSegment()
            segment_points_exist = False 
            
            for point in segment.points:
                if i >= start_index and i <= end_index:
                    segment_points_exist = True
                    point.extensions = []  
                    w_segment.points.append(point)
                i += 1

            if segment_points_exist:
                w_track.segments.append(w_segment)
                track_points_exist = True

        if track_points_exist:
            writer.tracks.append(w_track)
    p.write_text(writer.to_xml())

    return await represent_track(track_db, b)




@bp.route("/tracks/<int:chat_id>/")
async def load_tracks(chat_id: int):
    tracks = storage.TracksStorage.list_tracks(chat_id)
    b = bot.get_bot(s.api_token)
    ret: list[dict] = []
    for t in tracks:
        track_ret = await represent_track(t, b)
        if track_ret["segments"]:
            ret.append(track_ret)

    return {
        "tracks": ret
    }

    
# waitress-serve --call 'flaskr:create_app'
