import os
import time
import json
import shutil
import asyncio
import traceback
from platform import system
from threading import Thread
from fastapi import APIRouter, HTTPException, status, WebSocket, Body, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from config import PATH, check_cfg_file
import database as db
from agent import AgentExcutor
from providers import LlamacppProvider
from .api_schema import ChatRequest, MsgModelRequest, ConfigRequest, FileRequest

router = APIRouter()

@router.get("/health")
async def health():
    return {"detail": "System is healthy"}

@router.websocket('/ws')
async def websocket(ws: WebSocket):
    await ws.accept()

    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def producer(context, model_name):
        try:
            cfg = check_cfg_file()

            stream = AgentExcutor().process(
                cfg.get('llm_model', ''),
                context,
                **cfg
            )

            for chunk in stream:
                asyncio.run_coroutine_threadsafe(
                    queue.put(chunk),
                    loop
                )

            asyncio.run_coroutine_threadsafe(
                queue.put(None),
                loop
            )
        except Exception:
            traceback.print_exc()

            asyncio.run_coroutine_threadsafe(
                queue.put(None),
                loop
            )

    while True:
        request = await ws.receive_json()

        if isinstance(request, dict):
            chat = db.get_chat(request['chat_id'])
            if chat is None:
                chat = db.add_chat(title=request['content'])
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
                    'attachments': request['attachments'],
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
                        'content': m['content'],
                        'attachments': [att['name'] for att in m['attachments']]
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
                    'attachments': [],
                    'timestamp': None
                }
            )

            if msg is not None:
                await ws.send_json(msg)
            else:
                await ws.send_json({'error': f'Unable to create message on chat {chat['id']}'})
                continue

            resp = ''
            atts = []
            token = 0
            start = time.perf_counter()

            while True:
                piece = await queue.get()

                if piece is None:
                    break

                if piece.content:
                    if len(atts) == 0 and len(piece.attachments) > 0:
                        atts.extend(piece.attachments)

                    resp += piece.content
                    token += 1
                    delta = time.perf_counter() - start

                    await ws.send_json({
                        'id': msg['id'],
                        'chat_id': chat['id'],
                        'role': 'assistant',
                        'status': 'generating',
                        'content': piece.content,
                        'attachments': piece.attachments,
                        'metrics': {
                            'generated': token,
                            'time': round(delta, 2),
                            'tps': round(token / delta, 2)
                        }
                    })

            elapsed = time.perf_counter() - start
            tokens = len(LlamacppProvider().tokenize(resp))

            db.update_message(
                chat['id'],
                {
                    'id': msg['id'],
                    'role': 'assistant',
                    'content': resp,
                    'attachments': atts,
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

@router.get("/uploads/{file_name}")
async def get_file(file_name: str):
    file = db.get_document_by_name(file_name)

    if file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find file {file_name}"
        )

    return FileResponse(
        path=file['uri'],
        headers={
            'Attachment-Id': str(file['id']),
            'File-Name': file['name']
        }
    )

@router.get("/uploads")
async def get_docs():
    return db.get_documents()


@router.post("/uploads")
async def upload_files(
    data: list[UploadFile] = File(...)
):
    uploads_path = ''
    for d in PATH:
        if not d or not os.path.exists(d):
            continue

        uploads_path = os.path.join(d, 'Upload')

    if uploads_path == '':
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not find a DATA path"
        )

    for file in data:
        os.makedirs(uploads_path, exist_ok=True)

        print(f"File name: {file.filename}")
        print(f"File mime: {file.content_type}")
        print(f"Save into: {uploads_path}")

        try:
            with open(
                os.path.join(uploads_path, file.filename),
                'wb'
            ) as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as err:
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error while handle file {file.filename} -> {err}"
            )

        db.create_document({
            'id': None,
            'hash': None, # Make file hash here
            'name': file.filename,
            'size': file.size,
            'uri': os.path.join(uploads_path, file.filename),
            'timestamp': None # Create timestamp here
        })

    return {'detail': "Data received"}

@router.delete("/uploads")
async def delete_file(file_name: str = Body(..., embed=True)):
    file_path = ''
    for d in PATH:
        if not d or not os.path.exists(d):
            continue

        file_path = os.path.join(
            d,
            'Upload',
            file_name.replace(
                '\\' if system().lower() == 'windows' else '/',
                ''
            )
        )

    if os.path.exists(file_path) and os.path.isfile(file_path):
        try:
            os.remove(file_path)

            db.delete_document({
                'name': file_name
            })

            return {'detail': f"File {file_name} deleted"}
        except PermissionError:
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File {file_name} has no deletion permission"
            )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Unable to reach the file {file_name}"
    )

@router.get("/models/{model_type}")
async def get_models(model_type: str):
    models = []
    for d in PATH:
        if not d or not os.path.exists(d):
            continue

        path = os.path.join(d, 'Models', model_type)
        if os.path.isdir(path):
            for i in os.listdir(path):
                dir_path = os.path.join(path, i)
                if os.path.isdir(dir_path) and len(os.listdir(dir_path)) > 0:
                    models.append(i)

    return {'models': models}

@router.get("/config")
async def get_cfg():
    fallback_cfg = {
        'sys_prt': 'You are an Artificial inteligence assistant built to answer in the question`s language.',
        'llm_model': '',
        'embedding_model': '',
        'diffusion_model': '',
        'temp': 0.8,
        'max_tokens': -1,
        'top_k': 40,
        'top_p': 0.95,
        'min_p': 0.05
    }

    cfg_path = ''
    if PATH[0]:
        cfg_path = os.path.join(PATH[0], 'Config')
    else:
        cfg_path = os.path.join(PATH[1], 'Config')

    if os.path.exists(cfg_path):
        with open(os.path.join(cfg_path, 'config.json'), 'r', encoding='UTF-8') as file:
            return json.loads(file.read())
    else:
        os.makedirs(
            cfg_path,
            exist_ok=True
        )

        with open(f'{cfg_path}/config.json', 'w', encoding='UTF-8') as save_file:
            json.dump(fallback_cfg, save_file)

        return fallback_cfg

@router.post("/config")
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

    with open(os.path.join(cfg_path, 'config.json'), 'w', encoding='UTF-8') as cfg_file:
        json.dump(new_cfg.model_dump(), cfg_file)

    return {"detail": "Config updated"}

@router.post("/chat", status_code=status.HTTP_201_CREATED)
async def create_chat():
    result = db.add_chat()
    if result is not None:
        return result

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Chat could not be saved"
    )

@router.patch("/chat/{chat_id}")
async def update_chat(chat_id: int, title: str = Body(..., embed=True)):
    if db.update_chat(chat_id, title) is not None:
        return {"detail": f"Chat {chat_id} tltle modified"}

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Chat could not be modified"
    )

@router.delete("/chat/{chat_id}")
async def delete_chat(chat_id: int):
    if db.delete_chat(chat_id=chat_id):
        return {"detail": "Chat successful deleted"}

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Chat could not be deleted"
    )

@router.get("/chat")
async def get_chats():
    return db.get_chats()

@router.get('/chat/{chat_id}')
async def get_chat(chat_id: int):
    chat = db.get_chat(chat_id)
    if chat is None:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find chat with id {chat_id}"
        )

    return chat

@router.post("/chat/{chat_id}/message", status_code=status.HTTP_201_CREATED)
async def save_message(chat_id: int, msg: MsgModelRequest):
    result = db.add_message(chat_id=chat_id, data=msg.model_dump())
    if result:
        return result

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Message could not be saved"
    )

@router.get("/chat/{chat_id}/message")
async def get_messages(chat_id: int):
    return db.get_messages(chat_id)
