#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This library allows the development of bots for the turing game on play.turinggame.ai
"""
__author__ = "Simon Schmid"

import time
import websockets
import json
import asyncio
import signal
from base64 import b64encode

import websockets.exceptions
from pydantic import BaseModel, Field, model_serializer, constr



class APIKeyMessage(BaseModel):
    api_key: str = Field(description="Your API key. This is required to ensure that you are allowed to access this game",
                         min_length=36,max_length=36)
    bot_name: str = Field(description= "The Bot Name as it is stored in the Game Database", min_length=1,max_length=255)
    languages: str = Field(description= "A string with Two Character Language Indicators. Example: 'EN DE'")


class BotReadyMessage(BaseModel):
    type: str = Field(default="bot_ready")
    ready_state: bool = Field(default=False, description="Flag if a requested bot for a specific game is ready or not")
    game_id: int = Field(description="The game id of the game that requests a bot")
    api_key: str = Field(description="Your API key. This is required to ensure that you are allowed to access this game",
                         min_length=36,max_length=36)
    
class GameMessage(BaseModel):
    type: str = Field(default="game_message")
    game_id: int = Field(description="The game id of the game for which this message is supposed")
    message: str = Field(description="bot message",min_length=1,max_length=255)
    api_key: str = Field(description="Your API key. This is required to ensure that you are allowed to access this game",
                         min_length=36,max_length=36)

class ShutdownMessage(BaseModel):
    type: str = Field(default="shutdown_message")
    api_key: str = Field(description="Your API key. This is required to ensure that you are allowed to access this game",
                         min_length=36,max_length=36)
    bot_name: str = Field(description= "The Bot Name as it is stored in the Game Database", min_length=1,max_length=255)
    


class TuringBotClient:

    def __init__(self, api_key: str, bot_name: str, languages: str, endpoint: str = "wss://play.turinggame.ai", port = None) -> None:
        self.api_key = api_key
        self.languages = languages
        self.bot_name = bot_name

        if port is None:
            self.api_endpoint = endpoint+"/bot/"
        else:
            self.api_endpoint = endpoint+":"+str(port)+"/bot/"

        self.websocket = None
        self.__event_loop = None
        self.shutdown_flag = False
        self.shutdown_already_running = False



    async def send_game_message(self,game_id: int,message: str):
        if message is not None:
            if len(message) > 0:
                await self.websocket.send(GameMessage(type="game_message",game_id = game_id, message = message,api_key = self.api_key).model_dump_json())

    async def _receive(self):
        messages = await self.websocket.recv()
        return json.loads(messages)
    
    async def _bot_ready_check(self,game_id: int,bot: str,pl1: str,pl2: str, language: str):
        bot_state = await self.async_start_game(game_id,bot,pl1,pl2,language)
        await self.websocket.send(BotReadyMessage(type = "bot_ready", ready_state = bot_state, game_id = game_id, api_key = self.api_key).model_dump_json())
        
    async def async_start_game(self,game_id: int,bot: str,pl1: str,pl2: str, language: str) -> bool:
        return self.start_game(game_id,bot,pl1,pl2,language)

    
    def start_game(self,game_id: int,bot: str,pl1: str,pl2: str,language:str) -> bool:
        raise NotImplementedError("start_game is not implemented yet.")
    
    async def async_end_game(self,game_id: int) -> None:
        self.end_game(game_id)

    def end_game(self, game_id: int) -> None:
        raise NotImplementedError("end_game is not implemented yet.")


    async def _game_message_sender(self,game_id: int, message: str, player: str, bot: str):
        message = await self.async_on_message(game_id,message,player,bot)
        await self.send_game_message(game_id,message)

    async def async_on_message(self,game_id: int, message: str, player: str, bot: str) -> str:
        return self.on_message(game_id, message, player, bot)

    def on_message(self,game_id: int, message: str, player: str, bot: str) -> str:
        raise NotImplementedError("on_message is not implemented yet.")
    

    async def async_on_gamemaster_message(self,game_id: int, message: str, player: str, bot: str) -> None:
        return self.on_gamemaster_message(game_id, message, player, bot)
    
    def on_gamemaster_message(self,game_id: int, message: str, player: str, bot: str) -> None:
        raise NotImplementedError("on_gamemaster_message is not implemented yet.")

    def _on_shutdown_wrapper(self):
        asyncio.create_task(self._on_shutdown(send_shutdown=True), name="shutdown")



    async def _on_shutdown(self,send_shutdown: bool):

        self.shutdown_flag = True
        
        if send_shutdown and not self.shutdown_already_running:
            try:
                await self.websocket.send(ShutdownMessage(type="shutdown",api_key = self.api_key, bot_name = self.bot_name).model_dump_json())
            except:
                pass
            #await self.websocket.send(json.dumps({"type":"shutdown", "api_key":self.api_key}))
            await self.websocket.close()
            self.on_shutdown()

        self.shutdown_already_running = True

        all_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

        
        for task in all_tasks:
            if task.get_name() != "shutdown":
                task.cancel()
        
        await asyncio.gather(*all_tasks, return_exceptions=True)

    def on_shutdown(self):
        print("Warning: on_shutdown is not implemented yet")

    def start(self):
        self.__event_loop = asyncio.get_event_loop()

        try:
            self.__event_loop.run_until_complete(self.connect())
        except:
            pass

    
    def basic_auth_header(self, username, password):
        assert ':' not in username
        user_pass = f'{username}:{password}'
        basic_credentials = b64encode(user_pass.encode()).decode()
        return ('Authorization', f'Basic {basic_credentials}')

    async def connect(self):
        
        
        self.__event_loop.add_signal_handler(signal.SIGINT, self._on_shutdown_wrapper)
        self.__event_loop.add_signal_handler(signal.SIGTERM, self._on_shutdown_wrapper)

        print("Starting to connect now")

        while not self.shutdown_flag:
            try:
                async with websockets.connect(self.api_endpoint,extra_headers = [self.basic_auth_header('alan','alan1950')]) as websocket:
                    print("connected, checking api key...")
                    await websocket.send(APIKeyMessage(api_key = self.api_key, bot_name = self.bot_name, languages = self.languages).model_dump_json())
                    #await websocket.send(json.dumps({"api_key":self.api_key}))
                    self.websocket = websocket
                    response = await self._receive()
                    if response['type'] == 'info':
                        print(f"Server Response: {response['message']}")
                    await self._main_loop()
            
            except websockets.exceptions.ConnectionClosedOK as e:
                print("Websockets Connection closed ok")
                print(f"Connection closed with code: {e.code}")
                if e.reason:
                    print(f"Reason: {e.reason}")

            except websockets.exceptions.ConnectionClosedError as e:
                print("Websockets Connection closed with error")
                print(f"Connection closed with code: {e.code}")
                if e.code == 1008:
                    if e.reason == "invalid api key request":
                        print("Your API key was rejected. Please check your API Key")
                    elif e.reason == "invalid language codes":
                        print("Your language codes are not in the correct format or not accepted as allowed languages")
                    await self._on_shutdown(send_shutdown=False)
                else:
                    print("Game currently not reachable, waiting to reconnect...")
                    #time.sleep(5)
                    continue

            except ConnectionRefusedError:
                print("Connection refused, retry...")
                time.sleep(5)
                continue
            except websockets.exceptions.InvalidStatus:
                print("Connection refused, retry...")
                time.sleep(5)
                continue
            except websockets.exceptions.InvalidStatusCode:
                print("Connection refused, retry...")
                time.sleep(5)
                continue



    async def _main_loop(self):
        while not self.shutdown_flag:
            message = await self._receive()
            if message['type'] == 'game_message':
                asyncio.create_task(self._game_message_sender(message['game_id'],
                                                            message['message'],
                                                            message['player'],
                                                            message['bot']))
            elif message['type'] == 'start_game':
                asyncio.create_task(self._bot_ready_check(message['game_id'],
                                                        message['bot'],
                                                        message['pl1'],
                                                        message['pl2'],
                                                        message['language']))
                
            elif message['type'] == 'end_game':
                asyncio.create_task(self.async_end_game(message['game_id']))

            elif message['type'] == 'game_master':
                asyncio.create_task(self.async_on_gamemaster_message(message['game_id'],
                                                                    message['message'],
                                                                    message['player'],
                                                                    message['bot']))
                    


            