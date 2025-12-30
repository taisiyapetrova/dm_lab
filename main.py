import sys
import subprocess
import os

try:
    import graphviz
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "graphviz"])
    import graphviz

os.environ["PATH"] += os.pathsep + '/opt/homebrew/bin'

class DateDFA:
    S_IDLE = "IDLE"
    S_DAY = "DAY"
    S_SEP1_DOT = "SEP1_DOT"
    S_SEP1_SPC = "SEP1_SPC"
    S_MON_NUM = "MON_NUM"
    S_MON_WORD = "MON_WORD"
    S_SEP2_DOT = "SEP2_DOT"
    S_SEP2_SPC = "SEP2_SPC"
    S_YEAR = "YEAR"

    def __init__(self):
        self.reset()
        self.found_dates = []

    def reset(self):
        self.state = self.S_IDLE
        self.buffer_day = ""
        self.buffer_month = ""
        self.buffer_year = ""

    def process_text(self, text):
        self.found_dates = []
        self.reset()
        text_to_process = text + " "

        for char in text_to_process:
            self._step(char)

        return self.found_dates

    def _step(self, char):
        if self.state == self.S_IDLE:
            if char.isdigit():
                self.state = self.S_DAY
                self.buffer_day += char

        elif self.state == self.S_DAY:
            if char.isdigit():
                self.buffer_day += char
            elif char == '.':
                self.state = self.S_SEP1_DOT
            elif char == ' ':
                self.state = self.S_SEP1_SPC
            else:
                self.reset()

        elif self.state == self.S_SEP1_DOT:
            if char.isdigit():
                self.state = self.S_MON_NUM
                self.buffer_month += char
            else:
                self.reset()

        elif self.state == self.S_SEP1_SPC:
            if char.isalpha():
                self.state = self.S_MON_WORD
                self.buffer_month += char
            else:
                self.reset()

        elif self.state == self.S_MON_NUM:
            if char.isdigit():
                self.buffer_month += char
            elif char == '.':
                self.state = self.S_SEP2_DOT
            else:
                self.reset()

        elif self.state == self.S_MON_WORD:
            if char.isalpha():
                self.buffer_month += char
            elif char == ' ':
                self.state = self.S_SEP2_SPC
            else:
                self.reset()

        elif self.state == self.S_SEP2_DOT:
            if char.isdigit():
                self.state = self.S_YEAR
                self.buffer_year += char
            else:
                self.reset()

        elif self.state == self.S_SEP2_SPC:
            if char.isdigit():
                self.state = self.S_YEAR
                self.buffer_year += char
            elif char.isalpha():
                pass
            else:
                self.reset()

        elif self.state == self.S_YEAR:
            if char.isdigit():
                self.buffer_year += char
            else:
                self._save_date()
                self.reset()
                if char.isdigit():
                    self._step(char)

    def _save_date(self):
        if self.buffer_day and self.buffer_month and self.buffer_year:
            try:
                d = int(self.buffer_day)
                y = int(self.buffer_year)
                m = self.buffer_month
                self.found_dates.append([d, m, y])
            except ValueError:
                pass

    def visualize(self, filename="date_dfa_full"):
        try:
            dot = graphviz.Digraph(comment='Date Recognition DFA')
            dot.attr(rankdir='LR')

            dot.node(self.S_IDLE, 'Start', shape='circle', style='filled', fillcolor='lightgrey')
            dot.node(self.S_YEAR, 'Year\n[ACCEPT]', shape='doublecircle', style='filled', fillcolor='lightblue')

            for s in [self.S_DAY, self.S_SEP1_DOT, self.S_SEP1_SPC, self.S_MON_NUM,
                      self.S_MON_WORD, self.S_SEP2_DOT, self.S_SEP2_SPC]:
                dot.node(s, s)

            dot.edge(self.S_IDLE, self.S_DAY, label='digit')
            dot.edge(self.S_DAY, self.S_DAY, label='digit')
            dot.edge(self.S_DAY, self.S_SEP1_DOT, label='.')
            dot.edge(self.S_DAY, self.S_SEP1_SPC, label='space')

            dot.edge(self.S_SEP1_DOT, self.S_MON_NUM, label='digit')
            dot.edge(self.S_SEP1_SPC, self.S_MON_WORD, label='alpha')

            dot.edge(self.S_MON_NUM, self.S_MON_NUM, label='digit')
            dot.edge(self.S_MON_NUM, self.S_SEP2_DOT, label='.')

            dot.edge(self.S_MON_WORD, self.S_MON_WORD, label='alpha')
            dot.edge(self.S_MON_WORD, self.S_SEP2_SPC, label='space')

            dot.edge(self.S_SEP2_DOT, self.S_YEAR, label='digit')
            dot.edge(self.S_SEP2_SPC, self.S_YEAR, label='digit')

            dot.edge(self.S_YEAR, self.S_YEAR, label='digit')
            dot.edge(self.S_YEAR, self.S_IDLE, label='other', style='dashed')

            output_path = dot.render(filename, view=True, format='png')
            print(f"\nСхема сохранена: {output_path}")

        except Exception as e:
            print(f"\nОшибка Graphviz: {e}")

if __name__ == "__main__":
    dfa = DateDFA()
    print(" ЗАПУСК ТЕСТОВ ")

    text_task = "Событие произошло 2 декабря 1934 года. Ничего не произошло 3.01.2025."
    print(f"\nТест 1: {text_task}")
    assert dfa.process_text(text_task) == [[2, 'декабря', 1934], [3, '01', 2025]]
    print("STATUS: OK")

    text_complex = "Важные: 10.10.2020. Ошибка: 99..10.2020. Короткий год: 1 янв 202"
    print(f"\nТест 2 (Сложный): {text_complex}")
    assert dfa.process_text(text_complex) == [[10, '10', 2020], [1, 'янв', 202]]
    print("STATUS: OK")

    text_tight = "Start12.12.2012End.Next 1 января 2023"
    print(f"\nТест 3 (Слитный): {text_tight}")
    res = dfa.process_text(text_tight)
    print(f"Получено: {res}")

    assert res == [[12, '12', 2012], [1, 'января', 2023]]
    print("STATUS: OK")

    print("\nВсе тесты пройдены!")
    dfa.visualize()