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
import random
from typing import List,Optional
from base64 import b64encode

import websockets.exceptions
from pydantic import BaseModel, Field, model_serializer, constr



class APIKeyMessage(BaseModel):
    api_key: str = Field(description="Your API key. This is required to ensure that you are allowed to access this game",
                         min_length=36,max_length=36)
    bot_name: str = Field(description= "The Bot Name as it is stored in the Game Database", min_length=1,max_length=255)
    languages: str = Field(description= "A string with Two Character Language Indicators. Example: 'EN DE'")
    accuse_ready: Optional[bool] = Field(default=False, description="Flag if the bot is capable of accusing other players. This flag is optional, if it is not provided, it defaults to False.")


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

class AccuseMessage(BaseModel):
    type: str = Field(default="accuse_message")
    game_id: int = Field(description="The game id of the game for which this message is supposed")
    accusation: str = Field(description="The accusation message",min_length=1,max_length=255)
    api_key: str = Field(description="Your API key. This is required to ensure that you are allowed to access this game",
                         min_length=36,max_length=36)
    


class TuringBotClient:

    def __init__(self, api_key: str, bot_name: str, languages: str, endpoint: str = "wss://play.turinggame.ai", port = None, accuse_ready: bool = False) -> None:
        self.api_key = api_key
        self.languages = languages
        self.bot_name = bot_name
        self.accuse_ready = accuse_ready

        if port is None:
            self.api_endpoint = endpoint+"/bot/"
        else:
            self.api_endpoint = endpoint+":"+str(port)+"/bot/"

        self._websocket = None
        self.__event_loop = None
        self._shutdown_flag = False
        self._shutdown_already_running = False
        self.__player_list = {}
        self.__player = {}
        self.__accusation_sent = {}



    async def send_game_message(self,game_id: int,message: str):
        if message is not None:
            if len(message) > 0:
                await self._websocket.send(GameMessage(type="game_message",game_id = game_id, message = message,api_key = self.api_key).model_dump_json())

    
    async def send_accusation(self,game_id: int, accusation: str):
        if game_id in self.__accusation_sent and not self.__accusation_sent[game_id]:
            if accusation is not None:
                if len(accusation) > 0:
                    #send only if accusation is in list of players
                    if accusation in self.__player_list[game_id] and accusation != self.__player[game_id]:  # Check if the accused player is in the game's player list
                        await self._websocket.send(AccuseMessage(type="accuse_message",game_id = game_id, accusation = accusation,api_key = self.api_key).model_dump_json())
                        self.__accusation_sent[game_id] = True
        else:
            print(f"<WARNING> Accusation already sent for this bot in game {game_id}.",flush=True)
    
    async def on_accusation_request(self, game_id: int, bot: str, players: List[str]):
        players.remove(bot)
        accusation = random.choice(players)
        await self.send_accusation(game_id, accusation)
        raise NotImplementedError("on_accusation_request is not implemented yet. To ensure proper functionality, a random accusation is sent")
        
    async def _receive(self):
        messages = await self._websocket.recv()
        return json.loads(messages)
    
    async def _bot_ready_check(self,game_id: int,bot: str, players_list: List[str], language: str):
        #store player list in self._players dictionary
        self.__player_list[game_id] = players_list
        self.__player[game_id] = bot
        self.__accusation_sent[game_id] = False
        bot_state = await self.async_start_game(game_id,bot,players_list,language)
        await self._websocket.send(BotReadyMessage(type = "bot_ready", ready_state = bot_state, game_id = game_id, api_key = self.api_key).model_dump_json())
    
    async def _bot_ready_check_old(self,game_id: int,bot: str,pl1: str,pl2: str, language: str):
        bot_state = await self.async_start_game(game_id,bot,pl1,pl2,language)
        await self._websocket.send(BotReadyMessage(type = "bot_ready", ready_state = bot_state, game_id = game_id, api_key = self.api_key).model_dump_json())
    

    async def async_start_game_old(self,game_id: int,bot: str,pl1: str,pl2: str, language: str) -> bool:
        return self.start_game(game_id,bot,pl1,pl2,language)
    
    async def async_start_game(self,game_id: int,bot: str, players_list: List[str], language: str) -> bool:
        return self.start_game(game_id,bot,players_list,language)
   
                                 
    def start_game_old(self,game_id: int,bot: str,pl1: str,pl2: str,language:str) -> bool:
        raise NotImplementedError("start_game is not implemented yet.")

    def start_game(self,game_id: int,bot: str,players_list: List[str],language:str) -> bool:
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

        self._shutdown_flag = True
        
        if send_shutdown and not self._shutdown_already_running:
            try:
                await self._websocket.send(ShutdownMessage(type="shutdown",api_key = self.api_key, bot_name = self.bot_name).model_dump_json())
            except:
                pass
            #await self._websocket.send(json.dumps({"type":"shutdown", "api_key":self.api_key}))
            await self._websocket.close()
            self.on_shutdown()

        self._shutdown_already_running = True

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

        while not self._shutdown_flag:
            try:
                async with websockets.connect(self.api_endpoint) as _websocket:
                    print("connected, checking api key...")
                    if hasattr(self, 'accuse_ready'):
                        print("<DEBUG> accuse_ready", self.accuse_ready)
                        await _websocket.send(APIKeyMessage(api_key = self.api_key, bot_name = self.bot_name, languages = self.languages, accuse_ready = self.accuse_ready).model_dump_json())
                    else:
                        await _websocket.send(APIKeyMessage(api_key = self.api_key, bot_name = self.bot_name, languages = self.languages).model_dump_json())
                    #await _websocket.send(json.dumps({"api_key":self.api_key}))
                    self._websocket = _websocket
                    response = await self._receive()
                    if response['type'] == 'info':
                        print(f"Server Response: {response['message']}")
                    await self._main_loop()
            
            except websockets.exceptions.ConnectionClosedOK as e:
                print("websockets Connection closed ok")
                print(f"Connection closed with code: {e.code}")
                if e.reason:
                    print(f"Reason: {e.reason}")

            except websockets.exceptions.ConnectionClosedError as e:
                print("websockets Connection closed with error")
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
        while not self._shutdown_flag:
            message = await self._receive()

            #print("Received message:", message, flush=True)

            if message['type'] == 'game_message':
                asyncio.create_task(self._game_message_sender(message['game_id'],
                                                            message['message'],
                                                            message['player'],
                                                            message['bot']))
            elif message['type'] == 'start_game':
                asyncio.create_task(self._bot_ready_check(message['game_id'],
                                                    message['bot'],
                                                    message['players'],
                                                    message['language']))
                
            elif message['type'] == 'end_game':
                try:
                    self.__player_list.pop(message['game_id'], None)                
                    self.__player.pop(message['game_id'], None)
                    self.__accusation_sent.pop(message['game_id'], None)
                except Exception as e:
                    print(f"<ERROR> Exception occurred while removing entries from dictionaries for game_id {message['game_id']}: {str(e)}")
                
                try:
                    asyncio.create_task(self.async_end_game(message['game_id']))
                except Exception as e:
                    print(f"<ERROR> Exception occurred while ending game {message['game_id']}: {str(e)}")

            elif message['type'] == 'game_master':
                #print(f"Game Master Message for Game ID {message['game_id']}: {message['message']}")
                asyncio.create_task(self.async_on_gamemaster_message(message['game_id'],
                                                                    message['message'],
                                                                    message['player'],
                                                                    message['bot']))
            
            elif message['type'] == 'request_accusation':
                asyncio.create_task(self.on_accusation_request(message['game_id'],
                                                                     message['bot'],
                                                                     message['players']))


            