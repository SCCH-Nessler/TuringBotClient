#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A very basic demo implementation of a bot for the turing game (play.turinggame.ai), using the API client
"""
__author__ = "Simon Schmid"


from turing_bot_client import TuringBotClient
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()



class ExampleBot(TuringBotClient):

    def __init__(self,api_key: str,bot_name: str,languages: str,openai_api_key: str):

        super().__init__(api_key=api_key,bot_name=bot_name,languages=languages)
        self.client = OpenAI(api_key=openai_api_key)
        self.model_name = "gpt-4o"
        self.chat_store = {}
        self.active_games = set()
        self.language_store = {}
        self.system_prompt = '''you are a human communicating with two other parties in a chat where one of the other two is an ai chatbot.
                                It is a mafia-like game called turing game where the goal is to find out which of the three players is the AI.
                                All responses should follow this format:
                                Only provide the "Message" without including the "Player Name" or any other tags or labels.
                                Do not include any additional commentary or context.
                                Example:
                                If the input is "Player Name: How are you today?" the output should be "How are you today?"
                                If the input is "Player Name: What's the next step?" the output should be "What's the next step?"
                                '''

    def start_game(self,game_id: int,bot: str,player_list: list,language: str) -> bool:
        print(f"Starting game {game_id}")
        self.active_games.add(game_id)
        self.chat_store[game_id] = [{"role":"system",
                                    "content": self.system_prompt}]
        self.language_store[game_id] = language
        return True


    def end_game(self, game_id: int) -> None:
        print(f"Ending Game {game_id}")
        self.active_games.discard(game_id)
        del self.chat_store[game_id]
        del self.language_store[game_id]
    
    def on_gamemaster_message(self, game_id: int, message: str, player: str, bot: str) -> None:
        print(f"Game Master Message for game {game_id}: {message}")

    
    def on_message(self, game_id: int, message: str, player: str, bot: str) -> str:
        
        if player == bot:
            self.chat_store[game_id].append({"role":"assistant",
                                             "content": f"{player}: {message}"})
        else:
            self.chat_store[game_id].append({"role":"user",
                                             "content": f"{player}: {message}"})

        if player != bot:
            answer = self.client.chat.completions.create(
                            messages=self.chat_store[game_id] +
                            [{"role":"user",
                            "content":"Only provide the message without including your player name any other tags or labels at the front"}],
                            model = self.model_name).choices[0].message.content
            return answer
        
    
    def on_shutdown(self):
        print("\nshutting down now...")


bot = ExampleBot(api_key = os.getenv('api_key'),bot_name = "DemoBot",languages = "en",openai_api_key=os.getenv('openai_api_key'))

bot.start()



