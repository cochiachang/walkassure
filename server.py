import os
import base64
import json
import cv2
import numpy as np
import Main
from aiohttp import web, WSMsgType

ROOT = os.path.dirname(__file__)

async def download_sound(request):
    file_path = os.path.join(ROOT, "./web/sound.mp3")
    
    if not os.path.exists(file_path):
        return web.Response(status=404, text="File not found")

    with open(file_path, 'rb') as f:
        file_content = f.read()

    return web.Response(body=file_content, content_type='audio/mpeg')

async def javascript(request):
    content = open(os.path.join(ROOT, "./web/client.js"), "r", encoding="utf-8").read()
    return web.Response(content_type="application/javascript", text=content)

async def howler(request):
    content = open(os.path.join(ROOT, "./web/howler.core.min.js"), "r", encoding="utf-8").read()
    return web.Response(content_type="application/javascript", text=content)

async def index(request):
    content = open(os.path.join(ROOT, "./web/index.html"), "r", encoding="utf-8").read()
    return web.Response(content_type="text/html", text=content)

async def icon(request):
    with open(os.path.join(ROOT, "./web/icon.png"), "rb") as f:
        content = f.read()
    return web.Response(content_type="image/png", body=content)

async def setting(request):
    with open(os.path.join(ROOT, "./web/setting.png"), "rb") as f:
        content = f.read()
    return web.Response(content_type="image/png", body=content)

async def line(request):
    with open(os.path.join(ROOT, "./web/line.png"), "rb") as f:
        content = f.read()
    return web.Response(content_type="image/png", body=content)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            data = json.loads(msg.data)
            event = data.get('event')

            if event == 'sned_image':
                data_url = data.get('data')
                start_no_cross = data.get('start_no_cross')
                is_in_crosswalk = data.get('is_in_crosswalk') == 1
                previous_direction = data.get('previous_direction')
                remaining_crossings = data.get('remaining_crossings')
                detect_traffic = data.get('detect_traffic')
                _, encoded = data_url.split(",", 1)
                binary_data = base64.b64decode(encoded)
                image_np = np.frombuffer(binary_data, dtype=np.uint8)
                image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
                # 偵測
                data, start_no_cross, is_in_crosswalk, previous_direction, remaining_crossings = Main.main(image, start_no_cross, is_in_crosswalk, previous_direction , remaining_crossings, detect_traffic)
                response_data = {
                    "event": "detect_result",
                    "data": json.dumps(data),
                    "start_no_cross": start_no_cross,
                    "is_in_crosswalk": 1 if is_in_crosswalk is True else 0,
                    "previous_direction": previous_direction,
                    "remaining_crossings": remaining_crossings
                }
                await ws.send_json(response_data)
    return ws

if __name__ == "__main__":
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_get("/howler.core.min.js", howler)
    app.router.add_get("/icon.png", icon)
    app.router.add_get("/setting.png", setting)
    app.router.add_get("/line.png", line)
    app.router.add_get('/ws', websocket_handler)
    app.router.add_get('/sound.mp3', download_sound)
    web.run_app(
        app, access_log=None, host="0.0.0.0", port=8080
    )
