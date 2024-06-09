import grpc
from concurrent import futures
import random
import time

import forca_pb2
import forca_pb2_grpc

# Lista de palavras para o jogo
WORDS = ["python", "grpc", "programming", "hangman", "server", "client", "network", "communication", "protocol", "game"]

# Estado do jogo
class GameState:
    def __init__(self):
        self.players = []
        self.current_word = ""
        self.guessed_letters = []
        self.attempts_left = 6
        self.current_player_index = 0
        self.rounds_played = 0
        self.scores = {}

    def reset(self):
        self.current_word = random.choice(WORDS)
        self.guessed_letters = []
        self.attempts_left = 6
        self.current_player_index = 0
        self.rounds_played += 1

# Serviço gRPC para o jogo de forca
class ForcaServicer(forca_pb2_grpc.ForcaServicer):
    def __init__(self):
        self.game_state = GameState()

    def JoinGame(self, request, context):
        player_id = len(self.game_state.players) + 1
        player_name = request.player_name
        self.game_state.players.append(player_name)
        self.game_state.scores[player_name] = 0
        return forca_pb2.JoinGameResponse(player_id=str(player_id), message=f"Player {player_name} joined the game.")

    def StartGame(self, request, context):
        if len(self.game_state.players) < 2:
            return forca_pb2.StartGameResponse(message="Not enough players to start the game.", success=False)
        
        self.game_state.reset()
        return forca_pb2.StartGameResponse(message="Game started!", success=True)

    def GuessLetter(self, request, context):
        letter = request.letter.lower()
        player_id = int(request.player_id) - 1

        if player_id != self.game_state.current_player_index:
            return forca_pb2.GuessLetterResponse(message="It's not your turn!", correct=False, game_over=False, points=self.game_state.scores[self.game_state.players[player_id]])
        
        if letter in self.game_state.guessed_letters:
            return forca_pb2.GuessLetterResponse(message="Letter already guessed.", correct=False, game_over=False, points=self.game_state.scores[self.game_state.players[player_id]])
        
        self.game_state.guessed_letters.append(letter)
        if letter in self.game_state.current_word:
            if all(c in self.game_state.guessed_letters for c in self.game_state.current_word):
                self.game_state.scores[self.game_state.players[player_id]] += 1
                self.game_state.reset()
                game_over = self.game_state.rounds_played >= 10
                return forca_pb2.GuessLetterResponse(message="Correct! You guessed the word.", correct=True, game_over=game_over, points=self.game_state.scores[self.game_state.players[player_id]])
            return forca_pb2.GuessLetterResponse(message="Correct!", correct=True, game_over=False, points=self.game_state.scores[self.game_state.players[player_id]])
        else:
            self.game_state.attempts_left -= 1
            if self.game_state.attempts_left == 0:
                self.game_state.scores[self.game_state.players[player_id]] -= 1
                self.game_state.reset()
                game_over = self.game_state.rounds_played >= 10
                return forca_pb2.GuessLetterResponse(message="Incorrect! The hangman is complete.", correct=False, game_over=game_over, points=self.game_state.scores[self.game_state.players[player_id]])
            self.game_state.current_player_index = (self.game_state.current_player_index + 1) % len(self.game_state.players)
            return forca_pb2.GuessLetterResponse(message="Incorrect!", correct=False, game_over=False, points=self.game_state.scores[self.game_state.players[player_id]])

    def GetGameState(self, request, context):
        current_word_display = ''.join(c if c in self.game_state.guessed_letters else '_' for c in self.game_state.current_word)
        response = forca_pb2.GetGameStateResponse(
            current_word=current_word_display,
            attempts_left=self.game_state.attempts_left,
            guessed_letters=self.game_state.guessed_letters,
            current_player=self.game_state.players[self.game_state.current_player_index],
            scores=[forca_pb2.PlayerScore(player_name=player, score=score) for player, score in self.game_state.scores.items()],
            game_over=self.game_state.rounds_played >= 10,
            message="Game state retrieved."
        )
        return response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    forca_pb2_grpc.add_ForcaServicer_to_server(ForcaServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Server is running on port 50051...")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
