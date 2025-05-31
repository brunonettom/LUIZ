"""
Tarefa de Indicação Contextual (Contextual Cueing Task)

Este programa implementa uma Tarefa de Indicação Contextual (CCT), onde participantes
devem encontrar um alvo (letra T rotacionada) entre vários distratores (letras L rotacionadas).
Algumas configurações são repetidas ao longo do experimento, enquanto outras são aleatórias.
O experimento mede o tempo de reação dos participantes para avaliar o aprendizado implícito
das configurações espaciais repetidas.

Controles:
- Mouse: Clique no alvo (letra T) quando encontrá-lo
- Esc: Encerra o experimento
"""

import pygame
import sys
import random
import time
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Inicializar pygame
pygame.init()

# Configurações da tela
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tarefa de Indicação Contextual")

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Fontes
font = pygame.font.SysFont('Arial', 24)
small_font = pygame.font.SysFont('Arial', 16)

# Configurações do experimento
GRID_SIZE = 6  # Grade 6x6
CELL_SIZE = 80  # Tamanho de cada célula em pixels
NUM_REPEATED_CONFIGS = 12  # Número de configurações repetidas
NUM_NOVEL_CONFIGS = 12  # Número de configurações novas por bloco
NUM_BLOCKS = 5  # Número de blocos de treinamento
NUM_ITEMS = 12  # Número de itens (1 alvo + 11 distratores)

# Posição inicial da grade (centralizada)
GRID_START_X = (WIDTH - GRID_SIZE * CELL_SIZE) // 2
GRID_START_Y = (HEIGHT - GRID_SIZE * CELL_SIZE) // 2

# Configurações de estímulos
STIM_SIZE = 30  # Tamanho dos estímulos (T e L)
TARGET_COLOR = BLACK  # Cor do alvo (T)
DISTRACTOR_COLOR = BLACK  # Cor dos distratores (L)

class Stimulus:
    def __init__(self, stim_type, position, rotation):
        self.stim_type = stim_type  # 'T' para alvo, 'L' para distrator
        self.position = position    # Tupla (x, y) na grade
        self.rotation = rotation    # 0, 90, 180, 270 graus
        self.screen_pos = (
            GRID_START_X + position[0] * CELL_SIZE + CELL_SIZE // 2,
            GRID_START_Y + position[1] * CELL_SIZE + CELL_SIZE // 2
        )
        
    def draw(self):
        if self.stim_type == 'T':
            self.draw_t()
        else:  # 'L'
            self.draw_l()
            
    def draw_t(self):
        # Criar superfície para o estímulo
        surf = pygame.Surface((STIM_SIZE, STIM_SIZE), pygame.SRCALPHA)
        
        # Desenhar T
        pygame.draw.rect(surf, TARGET_COLOR, (STIM_SIZE//4, 0, STIM_SIZE//2, STIM_SIZE//4))
        pygame.draw.rect(surf, TARGET_COLOR, (STIM_SIZE//3, STIM_SIZE//4, STIM_SIZE//3, STIM_SIZE*3//4))
        
        # Rotacionar
        surf = pygame.transform.rotate(surf, self.rotation)
        
        # Desenhar na tela
        rect = surf.get_rect(center=self.screen_pos)
        screen.blit(surf, rect)
        
    def draw_l(self):
        # Criar superfície para o estímulo
        surf = pygame.Surface((STIM_SIZE, STIM_SIZE), pygame.SRCALPHA)
        
        # Desenhar L
        pygame.draw.rect(surf, DISTRACTOR_COLOR, (STIM_SIZE//4, 0, STIM_SIZE//2, STIM_SIZE*3//4))
        pygame.draw.rect(surf, DISTRACTOR_COLOR, (STIM_SIZE//4, STIM_SIZE*3//4, STIM_SIZE*3//4, STIM_SIZE//4))
        
        # Rotacionar
        surf = pygame.transform.rotate(surf, self.rotation)
        
        # Desenhar na tela
        rect = surf.get_rect(center=self.screen_pos)
        screen.blit(surf, rect)
        
    def contains_point(self, point):
        # Verifica se um ponto está contido no estímulo (para detecção de cliques)
        x, y = point
        center_x, center_y = self.screen_pos
        radius = STIM_SIZE // 2
        return (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2

class Configuration:
    def __init__(self, config_id, is_repeated):
        self.config_id = config_id
        self.is_repeated = is_repeated
        self.stimuli = []
        self.target = None
        self.generate()
        
    def generate(self):
        # Limpar configuração anterior
        self.stimuli = []
        
        # Criar grade 6x6
        grid_positions = [(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE)]
        
        # Selecionar posições aleatórias para os estímulos
        selected_positions = random.sample(grid_positions, NUM_ITEMS)
        
        # Primeira posição para o alvo
        target_pos = selected_positions[0]
        target_rotation = random.choice([0, 90, 180, 270])
        self.target = Stimulus('T', target_pos, target_rotation)
        self.stimuli.append(self.target)
        
        # Restante para distratores
        for i in range(1, NUM_ITEMS):
            distractor_pos = selected_positions[i]
            distractor_rotation = random.choice([0, 90, 180, 270])
            distractor = Stimulus('L', distractor_pos, distractor_rotation)
            self.stimuli.append(distractor)
            
    def draw(self):
        # Desenhar todos os estímulos
        for stimulus in self.stimuli:
            stimulus.draw()
            
class Experiment:
    def __init__(self):
        self.participant_id = ""
        self.repeated_configs = []
        self.trial_results = []
        self.current_block = 0
        self.current_trial = 0
        self.total_trials = 0
        self.state = "welcome"  # Estados: welcome, instructions, fixation, trial, break, end
        self.current_config = None
        self.trial_start_time = 0
        self.fixation_start_time = 0
        self.fixation_duration = 0.5  # segundos
        
    def setup_experiment(self):
        # Gerar configurações repetidas
        self.repeated_configs = [
            Configuration(i, True) for i in range(NUM_REPEATED_CONFIGS)
        ]
        
        # Calcular total de trials
        self.total_trials = (NUM_REPEATED_CONFIGS + NUM_NOVEL_CONFIGS) * NUM_BLOCKS
        
    def get_participant_info(self):
        pygame.key.set_repeat(500, 50)  # Configurar repetição de teclas
        input_text = ""
        input_active = True
        
        while input_active:
            screen.fill(WHITE)
            
            # Desenhar texto
            text_surface = font.render("Digite seu nome ou identificador:", True, BLACK)
            text_rect = text_surface.get_rect(center=(WIDTH//2, HEIGHT//3))
            screen.blit(text_surface, text_rect)
            
            # Desenhar caixa de entrada
            input_box = pygame.Rect(WIDTH//4, HEIGHT//2 - 20, WIDTH//2, 40)
            pygame.draw.rect(screen, BLACK, input_box, 2)
            
            # Renderizar texto de entrada
            input_surface = font.render(input_text, True, BLACK)
            screen.blit(input_surface, (input_box.x + 5, input_box.y + 5))
            
            # Instruções
            inst = small_font.render("Pressione ENTER para confirmar", True, BLACK)
            screen.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT*2//3))
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and input_text:
                        input_active = False
                        self.participant_id = input_text
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif len(input_text) < 20:  # Limitar tamanho
                        if event.unicode.isalnum() or event.unicode.isspace():
                            input_text += event.unicode
        
        pygame.key.set_repeat()  # Desativar repetição de teclas
    
    def show_welcome(self):
        screen.fill(WHITE)
        
        # Título
        title = font.render("Tarefa de Indicação Contextual", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
        
        # Instruções
        instructions = [
            "Neste experimento, você deve encontrar e clicar na letra T",
            "entre várias letras L que aparecem na tela.",
            "",
            "Clique com o botão esquerdo do mouse sobre a letra T",
            "o mais rápido possível assim que a encontrar.",
            "",
            "Pressione ESPAÇO para continuar."
        ]
        
        for i, line in enumerate(instructions):
            text = small_font.render(line, True, BLACK)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + i*25))
            
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
        
        self.state = "fixation"
        
    def show_fixation(self):
        screen.fill(WHITE)
        
        # Desenhar cruz de fixação
        pygame.draw.line(screen, BLACK, (WIDTH//2 - 10, HEIGHT//2), (WIDTH//2 + 10, HEIGHT//2), 3)
        pygame.draw.line(screen, BLACK, (WIDTH//2, HEIGHT//2 - 10), (WIDTH//2, HEIGHT//2 + 10), 3)
        
        pygame.display.flip()
        
        if self.fixation_start_time == 0:
            self.fixation_start_time = time.time()
            
        if time.time() - self.fixation_start_time >= self.fixation_duration:
            self.fixation_start_time = 0
            self.state = "trial"
            self.prepare_trial()
            
    def prepare_trial(self):
        # Determinar se este é um trial repetido ou novo
        if random.random() < 0.5 or self.current_trial >= NUM_REPEATED_CONFIGS:
            # Trial novo
            self.current_config = Configuration(-1, False)
        else:
            # Trial repetido - usar uma configuração existente
            config_idx = self.current_trial % NUM_REPEATED_CONFIGS
            self.current_config = self.repeated_configs[config_idx]
            
        self.trial_start_time = time.time()
        
    def run_trial(self):
        screen.fill(WHITE)
        
        # Desenhar grade (opcional, para depuração)
        for i in range(GRID_SIZE + 1):
            pygame.draw.line(screen, (200, 200, 200), 
                (GRID_START_X, GRID_START_Y + i * CELL_SIZE),
                (GRID_START_X + GRID_SIZE * CELL_SIZE, GRID_START_Y + i * CELL_SIZE))
            pygame.draw.line(screen, (200, 200, 200), 
                (GRID_START_X + i * CELL_SIZE, GRID_START_Y),
                (GRID_START_X + i * CELL_SIZE, GRID_START_Y + GRID_SIZE * CELL_SIZE))
        
        # Desenhar configuração atual
        self.current_config.draw()
        
        # Informações de progresso
        progress = f"Bloco: {self.current_block+1}/{NUM_BLOCKS}, Trial: {self.current_trial+1}/{(NUM_REPEATED_CONFIGS + NUM_NOVEL_CONFIGS)}"
        prog_text = small_font.render(progress, True, BLACK)
        screen.blit(prog_text, (10, 10))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "end"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Botão esquerdo
                    # Verificar se clicou no alvo
                    if self.current_config.target.contains_point(event.pos):
                        response_time = time.time() - self.trial_start_time
                        self.record_trial(response_time, True)
                        self.next_trial()
                    else:
                        # Clicou em outro lugar
                        for stim in self.current_config.stimuli:
                            if stim.contains_point(event.pos):
                                response_time = time.time() - self.trial_start_time
                                self.record_trial(response_time, False)
                                self.next_trial()
                                break
                            
    def record_trial(self, response_time, is_correct):
        trial_data = {
            'participant': self.participant_id,
            'block': self.current_block + 1,
            'trial': self.current_trial + 1,
            'configuration_id': self.current_config.config_id,
            'is_repeated': self.current_config.is_repeated,
            'response_time': round(response_time, 3),
            'is_correct': is_correct,
            'target_position': self.current_config.target.position
        }
        
        self.trial_results.append(trial_data)
        
    def next_trial(self):
        self.current_trial += 1
        
        if self.current_trial >= NUM_REPEATED_CONFIGS + NUM_NOVEL_CONFIGS:
            self.current_trial = 0
            self.current_block += 1
            
            if self.current_block < NUM_BLOCKS:
                self.state = "break"
            else:
                self.state = "end"
        else:
            self.state = "fixation"
            
    def show_break(self):
        screen.fill(WHITE)
        
        # Texto de pausa
        text = font.render(f"Bloco {self.current_block} de {NUM_BLOCKS} concluído", True, BLACK)
        text2 = font.render("Descanse um pouco e pressione ESPAÇO para continuar", True, BLACK)
        
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))
        screen.blit(text2, (WIDTH//2 - text2.get_width()//2, HEIGHT//2))
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "end"
                        waiting = False
        
        self.state = "fixation"
        
    def show_end(self):
        screen.fill(WHITE)
        
        # Texto de finalização
        text = font.render("Experimento concluído!", True, BLACK)
        text2 = font.render("Obrigado pela sua participação.", True, BLACK)
        text3 = font.render("Pressione ESPAÇO para sair", True, BLACK)
        
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))
        screen.blit(text2, (WIDTH//2 - text2.get_width()//2, HEIGHT//2))
        screen.blit(text3, (WIDTH//2 - text3.get_width()//2, HEIGHT//2 + 50))
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                        waiting = False
                        
        self.save_results()
        pygame.quit()
        sys.exit()
        
    def save_results(self):
        # Criar diretório de resultados se não existir
        results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados")
        os.makedirs(results_dir, exist_ok=True)
        
        # Criar dataframe
        results_df = pd.DataFrame(self.trial_results)
        
        # Timestamp para nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cct_participant_{self.participant_id}_{timestamp}"
        
        # Salvar CSV
        csv_path = os.path.join(results_dir, f"{filename}.csv")
        results_df.to_csv(csv_path, index=False)
        
        # Análise básica
        try:
            # Tempos médios por bloco e tipo de configuração
            analysis = results_df[results_df['is_correct']].groupby(['block', 'is_repeated'])['response_time'].mean().reset_index()
            
            # Salvar análise em TXT
            txt_path = os.path.join(results_dir, f"{filename}_analysis.txt")
            with open(txt_path, 'w') as f:
                f.write(f"ANÁLISE DA TAREFA DE INDICAÇÃO CONTEXTUAL - Participante: {self.participant_id}\n")
                f.write("="*80 + "\n\n")
                f.write("Tempos médios de resposta (segundos):\n")
                
                repeated_data = analysis[analysis['is_repeated']].reset_index()
                novel_data = analysis[~analysis['is_repeated']].reset_index()
                
                f.write("\nBloco\tRepetidas\tNovas\tDiferença\n")
                
                for i in range(1, NUM_BLOCKS + 1):
                    rep_time = repeated_data[repeated_data['block'] == i]['response_time'].values[0] if i in repeated_data['block'].values else 0
                    nov_time = novel_data[novel_data['block'] == i]['response_time'].values[0] if i in novel_data['block'].values else 0
                    diff = nov_time - rep_time
                    f.write(f"{i}\t{rep_time:.3f}s\t{nov_time:.3f}s\t{diff:.3f}s\n")
                
                # Taxa de acertos
                accuracy = len(results_df[results_df['is_correct']]) / len(results_df) * 100
                f.write(f"\nTaxa de acertos: {accuracy:.1f}%\n")
                
                # Efeito de indicação contextual
                mean_repeated = results_df[results_df['is_repeated'] & results_df['is_correct']]['response_time'].mean()
                mean_novel = results_df[~results_df['is_repeated'] & results_df['is_correct']]['response_time'].mean()
                contextual_effect = mean_novel - mean_repeated
                
                f.write(f"\nEfeito de indicação contextual: {contextual_effect:.3f}s\n")
                f.write(f"(Tempo médio em configurações novas - Tempo médio em configurações repetidas)\n")
                
        except Exception as e:
            print(f"Erro na análise: {e}")
            
        print(f"Resultados salvos em: {csv_path}")
            
    def run(self):
        self.get_participant_info()
        self.setup_experiment()
        
        clock = pygame.time.Clock()
        
        # Loop principal
        running = True
        while running:
            if self.state == "welcome":
                self.show_welcome()
            elif self.state == "fixation":
                self.show_fixation()
            elif self.state == "trial":
                self.run_trial()
            elif self.state == "break":
                self.show_break()
            elif self.state == "end":
                self.show_end()
                running = False
                
            clock.tick(60)
            
# Iniciar experimento
if __name__ == "__main__":
    experiment = Experiment()
    experiment.run()