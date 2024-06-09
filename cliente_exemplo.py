import grpc
import forca_pb2
import forca_pb2_grpc

class ForcaClient:
    def __init__(self, channel):
        self.stub = forca_pb2_grpc.ForcaStub(channel)

    def join_game(self, player_name):
        response = self.stub.JoinGame(forca_pb2.JoinGameRequest(player_name=player_name))
        print(response.message)
        return response.player_id

    def start_game(self, player_id):
        response = self.stub.StartGame(forca_pb2.StartGameRequest(player_id=player_id))
        if response.success:
            print(response.message)
        else:
            print(response.message)

    def guess_letter(self, player_id, letter):
        response = self.stub.GuessLetter(forca_pb2.GuessLetterRequest(player_id=player_id, letter=letter))
        print(response.message)
        if response.correct:
            print("Correct guess!")
        else:
            print("Incorrect guess.")
        if response.game_over:
            print("Game over!")

    def get_game_state(self, player_id):
        response = self.stub.GetGameState(forca_pb2.GetGameStateRequest(player_id=player_id))
        print("Current Word:", response.current_word)
        print("Attempts Left:", response.attempts_left)
        print("Guessed Letters:", ', '.join(response.guessed_letters))
        print("Current Player:", response.current_player)
        print("Scores:")
        for player_score in response.scores:
            print(f"{player_score.player_name}: {player_score.score}")
        if response.game_over:
            print("Game over!")
        print(response.message)

def run():
    # Conectando ao servidor gRPC
    with grpc.insecure_channel('localhost:50051') as channel:
        client = ForcaClient(channel)

        # Entrando no jogo
        player_name = input("Digite seu nome: ")
        player_id = client.join_game(player_name)

        # Iniciando o jogo
        input("Pressione Enter para iniciar o jogo...")
        client.start_game(player_id)

        # Loop principal do jogo
        while True:
            client.get_game_state(player_id)
            if input("Deseja fazer um chute? (S/N): ").lower() == 's':
                letter = input("Digite a letra: ").lower()
                client.guess_letter(player_id, letter)
            else:
                break

if __name__ == '__main__':
    run()
