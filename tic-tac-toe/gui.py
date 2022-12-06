import sys
import numpy as np
from random import random
from itertools import product

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QRadioButton, QLabel, QVBoxLayout, QHBoxLayout, QButtonGroup
from PyQt5.QtCore import pyqtSignal


def get_state_index(state):
    return np.argwhere((all_possible_states[:] == state).reshape((-1,9)).all(axis=-1)).flatten()[0]


def get_transitions_states(state, figure):
    next_states = []
    for plase in np.argwhere(state == EMPTY):
        s = state.copy()
        s[tuple(plase)] = figure
        next_states.append(s)
    return next_states


def get_transitions_dict(figure):
    return {
        i: [
            get_state_index(s) for s in get_transitions_states(state, figure)
        ]
        for i, state in enumerate(all_possible_states)
    }


class Actor():
    
    def __init__(self, is_circles, lr=None, random_possibility=None):
        self.is_circles = is_circles
        self.states = []
        self.figure = CIRCLE if self.is_circles else CROSS
        self.transitions = circles_transitions if self.is_circles else crosses_transitions
        self.set_default_costs()
        self.is_learning = True
        self.previous_selected_state = None
        self.lr = lr if lr is not None else ALPHA
        self.random_possibility = (
            random_possibility if random_possibility is not None else RANDOM_MOVE_POSSIBILITY
        )

    def reset_state(self):
        self.previous_selected_state = None
        
    def get_next_state(self, state_index, random_possible=True):
        next_states = self.transitions[state_index]
        if len(next_states) == 0:
            # Если все поле уже заполнено
            return None
        next_state = None
        if random_possible and random() < RANDOM_MOVE_POSSIBILITY:
            next_state = np.random.choice(next_states)
        else:
            states_cost = np.array([
                self.costs[s] for s in next_states
            ])
            next_state = next_states[np.random.choice(
                np.argwhere(states_cost == max(states_cost)).flatten()
            )]
        if self.is_learning and self.previous_selected_state is not None:
            self.costs[self.previous_selected_state] += (
                self.lr * (self.costs[next_state] - self.costs[self.previous_selected_state])
            )

        self.previous_selected_state = next_state
        return next_state

    def set_default_costs(self):
        self.costs = np.full((all_possible_states.shape[0]), 0.5)
        for i, state in enumerate(all_possible_states):
            if self.is_win(state):
                self.costs[i] = 1.
        self.win_states = np.argwhere(self.costs == 1.).flatten()

    def is_win(self, state_matrix):
        for row in state_matrix:
            if (row == self.figure).all():
                return True
        for column in state_matrix.transpose():
            if (column == self.figure).all():
                return True
        if ((state_matrix.diagonal() == self.figure).all() or
            (np.fliplr(state_matrix).diagonal() == self.figure).all()):
            return True


CIRCLE = 2
CROSS = 1
EMPTY = 0


all_possible_states = np.array(
    list(product(*([[EMPTY, CROSS, CIRCLE]] * 9)))
).reshape((-1, 3, 3))


with open('crosses_transitions.txt', 'r') as f:
    crosses_transitions = eval(f.read())

with open('circles_transitions.txt', 'r') as f:
    circles_transitions = eval(f.read())


ALPHA = 0.002
RANDOM_MOVE_POSSIBILITY = 0.1


crosses = Actor(False)
circles = Actor(True)

crosses.is_learning = False
circles.is_learning = False


crosses.costs = np.load('crosses_costs.npy')
circles.costs = np.load('circles_costs.npy')


app = QApplication(sys.argv)


class GridButton(QPushButton):
    clicked_signal = pyqtSignal(int, int)
    def __init__(self, i, j):
        super().__init__('')
        self.i = i
        self.j = j
        self.clicked.connect(self.clicked_slot)

    def clicked_slot(self):
        self.clicked_signal.emit(self.i, self.j)

    

BOT_VS_BOT = 0
HUMAN_VS_BOT = 1
BOT_VS_HUMAN = 2

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.game_type_group = QButtonGroup()
        self.game_type_buttons = []

        self.game_type_buttons.append(
            QRadioButton('Бот (Х) против бота (О)')
        )
        self.game_type_buttons.append(
            QRadioButton('Человек (Х) против бота (О)')
        )
        self.game_type_buttons.append(
            QRadioButton('Бот (Х) против человека (О)')
        )
        game_type_layout = QVBoxLayout()
        for i, b in enumerate(self.game_type_buttons):
            game_type_layout.addWidget(b)
            self.game_type_group.addButton(b, i)

        self.game_type_group.button(BOT_VS_BOT).setChecked(True)

        self.btn_start = QPushButton('Начать игру')
        self.btn_start.clicked.connect(self.start_game)

        self.grid = []
        grid_layout = QVBoxLayout()
        for i in range(3):
            self.grid.append([])
            hlayout = QHBoxLayout()
            for j in range(3):
                self.grid[-1].append(GridButton(i, j))
                self.grid[-1][-1].clicked_signal.connect(self.button_clicked)
                self.grid[-1][-1].setFixedWidth(46)
                hlayout.addWidget(self.grid[-1][-1])
            grid_layout.addLayout(hlayout)

        self.move_btn = QPushButton('Следующий ход')
        self.move_btn.clicked.connect(self.move_btn_clicked)
        
        layout = QVBoxLayout()
        layout.addLayout(game_type_layout)
        layout.addWidget(self.btn_start)
        layout.addLayout(grid_layout)
        layout.addWidget(self.move_btn)

        self.setLayout(layout)
        
    def make_crosses_move(self):
        self.state = crosses.get_next_state(self.state)
        self.set_state(self.state)
        self.current_move = CIRCLE
        self.check_if_game_ended()

    def make_circles_move(self):
        self.state = circles.get_next_state(self.state)
        self.set_state(self.state)
        self.current_move = CROSS
        self.check_if_game_ended()

    def start_game(self):
        crosses.reset_state()
        circles.reset_state()
        self.game_type = self.game_type_group.checkedId()
        self.state = 0
        self.current_move = CROSS
        self.set_state(self.state)
        if self.game_type == BOT_VS_BOT or self.game_type == BOT_VS_HUMAN:
            self.make_crosses_move()

    def set_state(self, state_index):
        s = all_possible_states[state_index]
        for i, row in enumerate(s):
            for j, elem in enumerate(row):
                if elem == CROSS:
                    self.grid[i][j].setText('X')
                elif elem == CIRCLE:
                    self.grid[i][j].setText('O')
                else:
                    self.grid[i][j].setText('')

    def move_btn_clicked(self):
        if (self.current_move == CROSS and
            self.game_type in [BOT_VS_BOT, BOT_VS_HUMAN]):
            self.make_crosses_move()
        elif (self.current_move == CIRCLE and
            self.game_type in [BOT_VS_BOT, HUMAN_VS_BOT]):
            self.make_circles_move()

    def button_clicked(self, i, j):
        if ((self.current_move == CIRCLE and
             self.game_type == BOT_VS_HUMAN) or
            (self.current_move == CROSS and
             self.game_type == HUMAN_VS_BOT)):
            s = all_possible_states[self.state].copy()
            if s[i][j] == EMPTY:
                s[i][j] = self.current_move
                self.state = get_state_index(s)
                self.set_state(self.state)
                self.current_move = (
                    CROSS if self.current_move == CIRCLE else CIRCLE
                )
                self.check_if_game_ended()
                if self.current_move == CIRCLE:
                    self.make_circles_move()
                elif self.current_move == CROSS:
                    self.make_crosses_move()

    def check_if_game_ended(self):
        if (self.state in circles.win_states or
            self.state in crosses.win_states):
            self.current_move = EMPTY

        else:
            s = all_possible_states[self.state]
            if len(np.argwhere(s == EMPTY)) == 0:
                self.current_move = EMPTY




w = MainWidget()
w.show()

app.exec_()
