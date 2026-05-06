"""
Crossword Puzzle Game — PyQt5
A fully playable crossword with clues, cell highlighting, and win detection.
"""
# hello
import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QLineEdit, QScrollArea,
    QFrame, QMessageBox, QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QKeyEvent

# ─────────────────────────────────────────────
#  Puzzle Data  (grid 13×13, 0=black cell)
# ─────────────────────────────────────────────
GRID_SIZE = 13

# '#' = black cell, '.' = white cell (to be filled)
LAYOUT = [
    "###.....#####",
    "###.###.#####",
    "....###......",
    ".###.....###.",
    ".###.###.###.",
    "....#...#....",
    "###.#.#.#.###",
    "....#...#....",
    ".###.###.###.",
    ".###.....###.",
    "......###....",
    "#####.###.###",
    "#####.....###",
]

WORDS = {
    # (row, col, direction, answer, clue)
    "1A":  (0, 3, "A", "FLAME",   "Fire's dancing tip"),
    "5A":  (2, 0, "A", "MOON",    "Night's glowing lantern"),
    "6A":  (2, 7, "A", "ATLAS",   "Map collection or a titan"),
    "7A":  (3, 1, "A", "RIVER",   "Flowing body of water"),
    "8A":  (4, 1, "A", "OLIVE",   "Martini garnish"),
    "9A":  (5, 0, "A", "PINE",    "Evergreen tree"),
    "10A": (5, 5, "A", "ARC",     "Curved path"),
    "11A": (5, 9, "A", "OVER",    "Finished or above"),
    "12A": (6, 4, "A", "AHA",     "Eureka! exclamation"),
    "13A": (7, 0, "A", "TROD",    "Walked upon (past)"),
    "14A": (7, 5, "A", "ETA",     "Greek letter / arrival time"),
    "15A": (7, 9, "A", "ROBE",    "Bath garment"),
    "16A": (8, 1, "A", "TIGER",   "Striped big cat"),
    "17A": (9, 1, "A", "ARENA",   "Sports stadium"),
    "18A": (10, 0, "A", "OSMIUM", "Densest metal element"),
    "19A": (11, 5, "A", "RUBY",   "Red precious gem"),
    "20A": (12, 5, "A", "SOLAR",  "Relating to the sun"),

    "1D":  (0, 3, "D", "MORT",   "Death (French)"),
    "2D":  (0, 4, "D", "LITRE",  "Metric liquid unit"),
    "3D":  (0, 5, "D", "AVIAN",  "Bird-related"),
    "4D":  (0, 6, "D", "MINOR",  "Under legal age / musical key"),
    "5D":  (2, 0, "D", "MITRE",  "Bishop's tall hat"),
    "6D":  (2, 7, "D", "ATOP",   "On top of"),
    "7D":  (2, 8, "D", "LORE",   "Traditional knowledge"),
    "8D":  (2, 9, "D", "AERO",   "Relating to air / chocolate bar"),
    "9D":  (2,10, "D", "SIRE",   "Father of a horse / address for king"),
    "10D": (3, 4, "D", "OPERA",  "Musical drama"),
    "11D": (3, 8, "D", "TIG",    "Children's chasing game"),
    "12D": (6, 6, "D", "HAT",    "Head covering"),
}


def build_grid_from_words(layout, words):
    """Fill in letters on the grid using word definitions."""
    grid = []
    for row in layout:
        grid.append(list(row))

    for key, (r, c, direction, answer, _) in words.items():
        for i, letter in enumerate(answer):
            if direction == "A":
                grid[r][c + i] = letter
            else:
                grid[r + i][c] = letter
    return grid


# ─────────────────────────────────────────────
#  Custom Cell Widget
# ─────────────────────────────────────────────
class CrosswordCell(QLineEdit):
    """A single crossword cell: white (editable) or black (blocked)."""
    navigated = pyqtSignal(int, int, str)   # row, col, direction key

    def __init__(self, row, col, is_black=False, number="", parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.is_black = is_black
        self.correct_letter = ""
        self.number = number
        self._highlighted = False
        self._selected = False

        self.setFixedSize(QSize(46, 46))
        self.setAlignment(Qt.AlignCenter)
        self.setMaxLength(1)
        self.setFont(QFont("Georgia", 16, QFont.Bold))

        if is_black:
            self.setReadOnly(True)
            self.setStyleSheet("background:#1a1a2e; border:none;")
        else:
            self._apply_style()

        if number:
            self._num_label = QLabel(number, self)
            self._num_label.setFont(QFont("Courier", 7, QFont.Bold))
            self._num_label.setStyleSheet("color:#c0392b; background:transparent;")
            self._num_label.move(2, 1)

        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text):
        if text:
            self.setText(text.upper())
            # Auto-advance
            self.navigated.emit(self.row, self.col, "advance")

    def _apply_style(self):
        if self._selected:
            bg = "#f39c12"
        elif self._highlighted:
            bg = "#fdebd0"
        else:
            bg = "#fdfefe"
        self.setStyleSheet(
            f"background:{bg}; border:2px solid #2c3e50; color:#1a252f;"
            f"selection-background-color:#f39c12;"
        )

    def set_highlighted(self, val):
        self._highlighted = val
        self._apply_style()

    def set_selected(self, val):
        self._selected = val
        self._apply_style()

    def mark_correct(self):
        self.setStyleSheet(
            "background:#d5f5e3; border:2px solid #27ae60; color:#1e8449;"
        )
        self.setReadOnly(True)

    def mark_wrong(self):
        self.setStyleSheet(
            "background:#fadbd8; border:2px solid #c0392b; color:#922b21;"
        )

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key_Backspace and not self.text():
            self.navigated.emit(self.row, self.col, "back")
            return
        dirs = {
            Qt.Key_Up: "up", Qt.Key_Down: "down",
            Qt.Key_Left: "left", Qt.Key_Right: "right",
        }
        if key in dirs:
            self.navigated.emit(self.row, self.col, dirs[key])
            return
        super().keyPressEvent(event)


# ─────────────────────────────────────────────
#  Clue Panel
# ─────────────────────────────────────────────
class CluePanel(QWidget):
    clue_clicked = pyqtSignal(str)   # emits word key like "3A"

    def __init__(self, words, parent=None):
        super().__init__(parent)
        self.words = words
        self.labels = {}
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        for direction, title in [("A", "ACROSS"), ("D", "DOWN")]:
            header = QLabel(title)
            header.setFont(QFont("Palatino Linotype", 13, QFont.Bold))
            header.setStyleSheet(
                "color:#fdfefe; background:#2c3e50; padding:6px 10px; letter-spacing:2px;"
            )
            outer.addWidget(header)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setStyleSheet("background:#1a1a2e;")

            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setSpacing(2)
            layout.setContentsMargins(6, 6, 6, 6)

            keys = sorted(
                [k for k in self.words if k.endswith(direction)],
                key=lambda x: int(x[:-1])
            )

            for key in keys:
                _, _, _, answer, clue = self.words[key]
                num = key[:-1]
                lbl = QLabel(f"<b>{num}.</b> {clue} <i>({len(answer)})</i>")
                lbl.setFont(QFont("Georgia", 10))
                lbl.setStyleSheet(
                    "color:#ecf0f1; padding:4px 6px; border-radius:4px;"
                )
                lbl.setWordWrap(True)
                lbl.setCursor(Qt.PointingHandCursor)
                lbl.mousePressEvent = lambda e, k=key: self.clue_clicked.emit(k)
                self.labels[key] = lbl
                layout.addWidget(lbl)

            layout.addStretch()
            scroll.setWidget(container)
            outer.addWidget(scroll, 1)

    def highlight_clue(self, key):
        for k, lbl in self.labels.items():
            lbl.setStyleSheet(
                "color:#f39c12; padding:4px 6px; border-radius:4px; background:#2c3e50;"
                if k == key else
                "color:#ecf0f1; padding:4px 6px; border-radius:4px;"
            )


# ─────────────────────────────────────────────
#  Main Game Window
# ─────────────────────────────────────────────
class CrosswordGame(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("✦ Crossword Puzzle ✦")
        self.setMinimumSize(1000, 700)
        self.cells = {}           # (row,col) -> CrosswordCell
        self.solution = build_grid_from_words(LAYOUT, WORDS)
        self.current_word_key = None
        self.current_direction = "A"   # "A" or "D"
        self._build_ui()
        self._number_cells()
        self._populate_solution_map()

    # ── UI Construction ──────────────────────
    def _build_ui(self):
        self.setStyleSheet("background:#0f3460; color:#ecf0f1;")

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Left: grid + toolbar
        left = QVBoxLayout()
        left.setSpacing(10)

        title = QLabel("✦  CROSSWORD  ✦")
        title.setFont(QFont("Palatino Linotype", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#f39c12; letter-spacing:6px;")
        left.addWidget(title)

        # Grid
        grid_frame = QFrame()
        grid_frame.setStyleSheet(
            "background:#1a1a2e; border:3px solid #f39c12; border-radius:6px;"
        )
        grid_layout = QGridLayout(grid_frame)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(8, 8, 8, 8)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                ch = LAYOUT[r][c]
                is_black = (ch == '#')
                cell = CrosswordCell(r, c, is_black=is_black)
                cell.navigated.connect(self._handle_navigate)
                if not is_black:
                    cell.focusInEvent = lambda e, rr=r, cc=c: self._cell_focused(rr, cc, e)
                grid_layout.addWidget(cell, r, c)
                self.cells[(r, c)] = cell

        left.addWidget(grid_frame, 0, Qt.AlignHCenter)

        # Buttons
        btn_row = QHBoxLayout()
        for label, slot, color in [
            ("Check", self._check_answers, "#27ae60"),
            ("Reveal", self._reveal_all, "#e67e22"),
            ("Clear", self._clear_all, "#7f8c8d"),
            ("New Game", self._new_game, "#2980b9"),
        ]:
            btn = QPushButton(label)
            btn.setFont(QFont("Georgia", 11, QFont.Bold))
            btn.setFixedHeight(38)
            btn.setStyleSheet(
                f"QPushButton{{background:{color}; color:white; border:none; border-radius:6px; padding:0 18px;}}"
                f"QPushButton:hover{{background:{color}cc;}}"
            )
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        left.addLayout(btn_row)

        # Status bar
        self.status_label = QLabel("Select a cell to begin solving!")
        self.status_label.setFont(QFont("Georgia", 10))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color:#bdc3c7;")
        left.addWidget(self.status_label)

        main_layout.addLayout(left, 3)

        # Right: clue panel
        self.clue_panel = CluePanel(WORDS)
        self.clue_panel.clue_clicked.connect(self._jump_to_word)
        self.clue_panel.setMinimumWidth(260)
        main_layout.addWidget(self.clue_panel, 2)

    # ── Numbering ────────────────────────────
    def _number_cells(self):
        """Assign clue numbers to cells based on word starts."""
        cell_numbers = {}
        for key, (r, c, direction, answer, _) in WORDS.items():
            num = key[:-1]
            cell_numbers[(r, c)] = num

        for (r, c), num in cell_numbers.items():
            cell = self.cells.get((r, c))
            if cell and not cell.is_black:
                cell.number = num
                lbl = QLabel(num, cell)
                lbl.setFont(QFont("Courier", 7, QFont.Bold))
                lbl.setStyleSheet("color:#c0392b; background:transparent;")
                lbl.move(2, 1)
                lbl.show()

    def _populate_solution_map(self):
        """Store correct letters in each cell."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                ch = self.solution[r][c]
                if ch not in ('#', '.'):
                    cell = self.cells.get((r, c))
                    if cell:
                        cell.correct_letter = ch

    # ── Navigation / Focus ───────────────────
    def _cell_focused(self, row, col, event):
        """Handle clicking a cell."""
        QLineEdit.focusInEvent(self.cells[(row, col)], event)
        self._select_word_at(row, col)

    def _select_word_at(self, row, col):
        """Highlight the word that contains this cell."""
        # Find which word(s) include this cell
        matching = []
        for key, (r, c, direction, answer, _) in WORDS.items():
            cells_in_word = []
            for i in range(len(answer)):
                if direction == "A":
                    cells_in_word.append((r, c + i))
                else:
                    cells_in_word.append((r + i, c))
            if (row, col) in cells_in_word:
                matching.append((key, cells_in_word))

        if not matching:
            return

        # Prefer same direction; toggle if only one direction available
        same_dir = [(k, cells) for k, cells in matching if k.endswith(self.current_direction)]
        chosen_key, chosen_cells = (same_dir or matching)[0]

        # If clicking same cell again, toggle direction
        if chosen_key == self.current_word_key and len(matching) > 1:
            other = [m for m in matching if m[0] != chosen_key]
            chosen_key, chosen_cells = other[0]
            self.current_direction = "D" if chosen_key.endswith("D") else "A"

        self.current_word_key = chosen_key
        self.current_direction = "D" if chosen_key.endswith("D") else "A"

        # Clear all highlights
        for cell in self.cells.values():
            if not cell.is_black:
                cell.set_highlighted(False)
                cell.set_selected(False)

        # Highlight word cells
        for pos in chosen_cells:
            self.cells[pos].set_highlighted(True)
        self.cells[(row, col)].set_selected(True)

        self.clue_panel.highlight_clue(chosen_key)
        _, _, _, answer, clue = WORDS[chosen_key]
        self.status_label.setText(f"{chosen_key}: {clue}  ({len(answer)} letters)")

    def _handle_navigate(self, row, col, action):
        if action == "advance":
            self._move(row, col, 1)
        elif action == "back":
            self._move(row, col, -1)
        elif action == "left":
            self._goto(row, col - 1)
        elif action == "right":
            self._goto(row, col + 1)
        elif action == "up":
            self._goto(row - 1, col)
        elif action == "down":
            self._goto(row + 1, col)

    def _move(self, row, col, delta):
        """Move within current word direction."""
        if self.current_direction == "A":
            self._goto(row, col + delta)
        else:
            self._goto(row + delta, col)

    def _goto(self, row, col):
        cell = self.cells.get((row, col))
        if cell and not cell.is_black:
            cell.setFocus()

    def _jump_to_word(self, key):
        r, c, direction, _, _ = WORDS[key]
        self.current_direction = direction
        self._goto(r, c)
        self._select_word_at(r, c)

    # ── Game Actions ─────────────────────────
    def _check_answers(self):
        wrong = 0
        total = 0
        for (r, c), cell in self.cells.items():
            if cell.is_black or not cell.correct_letter:
                continue
            total += 1
            entered = cell.text().upper()
            if entered == cell.correct_letter:
                cell.mark_correct()
            elif entered:
                cell.mark_wrong()
                wrong += 1

        if wrong == 0:
            self.status_label.setText("🎉🎉 Puzzle complete! Congratulations!")
            QMessageBox.information(self, "Solved!", "🎉 You completed the crossword!\n\nWell done!")
        else:
            self.status_label.setText(f"❌ {wrong} wrong answer(s). Keep trying!")

    def _reveal_all(self):
        reply = QMessageBox.question(
            self, "Reveal All?",
            "This will fill in all answers. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            for (r, c), cell in self.cells.items():
                if not cell.is_black and cell.correct_letter:
                    cell.blockSignals(True)
                    cell.setText(cell.correct_letter)
                    cell.blockSignals(False)
                    cell.mark_correct()
            self.status_label.setText("Puzzle revealed.")

    def _clear_all(self):
        for cell in self.cells.values():
            if not cell.is_black:
                cell.blockSignals(True)
                cell.clear()
                cell.setReadOnly(False)
                cell.blockSignals(False)
                cell._highlighted = False
                cell._selected = False
                cell._apply_style()
        self.status_label.setText("Board cleared. Start fresh!")

    def _new_game(self):
        self._clear_all()
        self.current_word_key = None
        self.status_label.setText("Select a cell to begin solving!")


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark palette base
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#0f3460"))
    palette.setColor(QPalette.WindowText, QColor("#ecf0f1"))
    app.setPalette(palette)

    window = CrosswordGame()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
