import os
import time
import asyncio
from threading import Thread
from init import app, PATH
import db_conn as db
from api_schema import ChatRequest, MsgModelRequest, ConfigRequest
from agent import Engine
import json
from fastapi import HTTPException, status, WebSocket, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

engine = None

def check_cfg_file():
    data_path = PATH[0] if PATH[0] else PATH[1]

    cfg_path = data_path + '/Config'
    if not os.path.exists(cfg_path):
        os.makedirs(cfg_path, exist_ok=True)

    with open(cfg_path + '/config.json', 'r', encoding='UTF-8') as cfg_file:
        return json.loads(cfg_file.read())

def generator(eng, prompt, model):
    for line in eng.generate_txt(prompt, model, max_tokens=2048, stream=True):
        yield line['choices'][-1]['text']

@app.get("/health")
async def health():
    return {"detail": "System is healthy"}

@app.websocket('/ws')
async def websocket(ws: WebSocket):
    global engine
    if engine is None:
        engine = Engine()

    await ws.accept()

    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def producer(context, model_name):
        data_path = PATH[0] if PATH[0] else PATH[1]

        model_path = data_path + '/Models/' + model_name
        print(f'files: {os.listdir(model_path)}') # To remove
        for file in os.listdir(model_path):
            name = file.lower()

            if 'mtp' not in name and 'mmproj' not in name and name.endswith('.gguf'):
                model_path += f'/{file}'
                break

        print(f'model path -> {model_path}') # To remove

        cfg = check_cfg_file()

        stream = engine.generate_txt(
            context,
            model_path,
            cfg,
            stream=True
        )

        for chunk in stream:
            piece = chunk['choices'][-1]['delta']

            asyncio.run_coroutine_threadsafe(
                queue.put(piece),
                loop
            )

        asyncio.run_coroutine_threadsafe(
            queue.put(None),
            loop
        )

    while True:
        request = await ws.receive_json()
        if type(request) is dict:
            chat = db.get_chat(request['chat_id'])
            if chat is None:
                chat = db.add_chat()
                await ws.send_json({
                    'chat_id': 0,
                    'new_id': chat['id']
                })

            db.add_message(
                chat['id'],
                {
                    'id': None,
                    'role': 'user',
                    'content': request['content'],
                    'timestamp': None
                }
            )

            cfg = check_cfg_file()

            context = [{
                'role': 'system',
                'content': cfg['sys_prt']
            }]

            msgs = db.get_messages(chat['id'])
            if msgs is not None and len(msgs) > 0:
                for m in msgs:
                    context.append({
                        'role': m['role'],
                        'content': m['content']
                    })

            Thread(
                target=producer,
                args=(context, request['model'],)
            ).start()

            msg = db.add_message(
                chat['id'],
                {
                    'id': None,
                    'role': 'assistant',
                    'content': '',
                    'timestamp': None
                }
            )

            if msg is not None:
                await ws.send_json(msg)
            else:
                await ws.send_json({'error': f'Unable to create message on chat {chat['id']}'})
                continue

            resp = ''
            token = 0
            start = time.perf_counter()

            while True:
                piece = await queue.get()

                if piece is None:
                    break

                if isinstance(piece, dict) and 'content' in piece:
                    resp += piece['content']
                    token += 1
                    delta = time.perf_counter() - start

                    await ws.send_json({
                        'id': msg['id'],
                        'chat_id': chat['id'],
                        'role': 'assistant',
                        'status': 'generating',
                        'content': piece['content'],
                        'metrics': {
                            'generated': token,
                            'time': round(delta, 2),
                            'tps': round(token / delta, 2)
                        }
                    })

            elapsed = time.perf_counter() - start
            tokens = len(engine.tokenize(resp))

            db.update_message(
                chat['id'],
                {
                    'id': msg['id'],
                    'role': 'assistant',
                    'content': resp,
                    'timestamp': None,
                }
            )

            await ws.send_json({
                'id': msg['id'],
                'chat_id': chat['id'],
                'role': 'assistant',
                'status': 'completed',
                'metrics': {
                    'generated': tokens,
                    'time': round(elapsed, 2),
                    'tps': round(tokens / elapsed, 2)
                }
            })

@app.post("/v1/chat/completions")
async def chat_gen(r: ChatRequest):
    global engine
    if engine is None:
        engine = Engine()

    return StreamingResponse(
        generator(engine, r.prompt, r.model),
        media_type="text/event-stream"
    )

@app.post("/v1/image/generations")
async def img_gen(r: ChatRequest):
    global engine
    if engine is None:
        engine = Engine()

    # engine.generete_img()

    return {"response": "img"}

@app.get("/models")
async def get_models():
    models = []
    for d in PATH:
        print(f"get_models -> PATH -> {d}")
        if not d or not os.path.exists(d):
            continue

        path = os.path.join(d, 'Models')
        print(f"get_models -> Models dir -> {os.listdir(path)}")
        if os.path.isdir(path):
            for i in os.listdir(path):
                if os.path.isdir(f'{path}/{i}') and len(os.listdir(f'{path}/{i}')) > 0:
                    models.append(i)

    return {'models': models}

@app.get("/config")
async def get_cfg():
    fallback_cfg = {
        'sys_prt': 'You are an Artificial inteligence assistant built to answer in the question`s language.',
        'temp': 0.8,
        'max_tokens': -1,
        'top_k': 40,
        'top_p': 0.95,
        'min_p': 0.05
    }

    cfg_path = ''
    if PATH[0]:
        cfg_path = f'{PATH[0]}/Config'
    else:
        cfg_path = f'{PATH[1]}/Config'

    print(f'cfg_path used -> {cfg_path}')

    if os.path.exists(cfg_path):
        with open(f'{cfg_path}/config.json', 'r', encoding='UTF-8') as file:
            return json.loads(file.read())
    else:
        os.makedirs(
            cfg_path,
            exist_ok=True
        )

        with open(f'{cfg_path}/config.json', 'w', encoding='UTF-8') as save_file:
            json.dump(fallback_cfg, save_file)

        return fallback_cfg

@app.post("/config")
async def update_cfg(new_cfg: ConfigRequest):
    cfg_path = ''
    if PATH[0]:
        cfg_path = f'{PATH[0]}/Config'
    else:
        cfg_path = f'{PATH[1]}/Config'

    if not os.path.exists(cfg_path):
        os.makedirs(
            cfg_path,
            exist_ok=True
        )

    print(new_cfg.model_dump())

    with open(f'{cfg_path}/config.json', 'w', encoding='UTF-8') as cfg_file:
        json.dump(new_cfg.model_dump(), cfg_file)

    return {"detail": "Config updated"}

@app.post("/chat", status_code=status.HTTP_201_CREATED)
async def create_chat():
    result = db.add_chat()
    if result is not None:
        return result

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Chat could not be saved"
    )

@app.patch("/chat/{chat_id}")
async def update_chat(chat_id: int, title: str = Body(..., embed=True)):
    if db.update_chat(chat_id, title) is not None:
        return {"detail": f"Chat {chat_id} tltle modified"}

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Chat could not be modified"
    )

@app.delete("/chat/{chat_id}")
async def delete_chat(chat_id: int):
    if db.delete_chat(chat_id=chat_id):
        return {"detail": "Chat successful deleted"}

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Chat could not be deleted"
    )

@app.get("/chat")
async def get_chats():
    return db.get_chats()

@app.get('/chat/{chat_id}')
async def get_chat(chat_id: int):
    chat = db.get_chat(chat_id)
    if chat is None:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find chat with id {chat_id}"
        )

    return chat

@app.post("/chat/{chat_id}/message", status_code=status.HTTP_201_CREATED)
async def save_message(chat_id: int, msg: MsgModelRequest):
    result = db.add_message(chat_id=chat_id, data=msg.model_dump())
    if result:
        return result

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Message could not be saved"
    )

@app.get("/chat/{chat_id}/message")
async def get_messages(chat_id: int):
    return db.get_messages(chat_id)
