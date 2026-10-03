#!/usr/bin/env python3
"""Tiny Google Tasks popup for waybar. Reads from the disk cache; API only on
add / delete / complete / refresh."""
#this is ai slop i dont wanna write ui in python3

import sys
import threading

from PySide6.QtCore import QEvent, QObject, QTimer, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QMenu, QPushButton, QVBoxLayout, QWidget,
)

import tasks

STYLE = """
#card { background: #1e1e2e; border: 1px solid #313244; border-radius: 12px; }
QComboBox, QLineEdit, QPushButton {
    background: #313244; color: #cdd6f4; border: none; border-radius: 8px;
    padding: 6px 10px; font-size: 13px;
}
QPushButton { padding: 6px 0; min-width: 30px; max-width: 30px; }
QPushButton:hover { background: #45475a; }
QPushButton:disabled, QLineEdit:disabled { color: #6c7086; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #313244; color: #cdd6f4; border: none;
    selection-background-color: #45475a; outline: none;
}
QListWidget { background: transparent; border: none; outline: none; color: #cdd6f4; font-size: 13px; }
QListWidget::item { padding: 5px 2px; }
QListWidget::item:hover, QListWidget::item:selected { background: transparent; }
QListWidget::indicator { width: 14px; height: 14px; border-radius: 7px; border: 2px solid #6c7086; }
QListWidget::indicator:hover { border-color: #89b4fa; }
QListWidget::indicator:checked { background: #89b4fa; border-color: #89b4fa; }
QScrollBar:vertical { width: 4px; background: transparent; }
QScrollBar::handle:vertical { background: #45475a; border-radius: 2px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QMenu { background: #313244; color: #cdd6f4; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 5px 16px; border-radius: 6px; }
QMenu::item:selected { background: #45475a; }
"""

LIST_ID, TASK_ID = Qt.UserRole + 1, Qt.UserRole


class Bus(QObject):
    data = Signal(dict)  # fresh cache contents, emitted after any background job


class Popup(QWidget):
    def __init__(self):
        super().__init__()
        self.bus = Bus()
        self.data = tasks.load_cache()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(STYLE)
        self.resize(280, 340)

        card = QFrame(objectName="card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(6)
        self.combo = QComboBox()
        self.refresh = QPushButton("⟳", toolTip="Sync with Google")
        top.addWidget(self.combo, 1)
        top.addWidget(self.refresh)

        self.list = QListWidget()
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.entry = QLineEdit()

        lay.addLayout(top)
        lay.addWidget(self.list)
        lay.addWidget(self.entry)

        self.bus.data.connect(self.set_data)
        self.combo.currentIndexChanged.connect(self.render)
        self.refresh.clicked.connect(self.do_sync)
        self.list.itemChanged.connect(self.on_check)
        self.list.customContextMenuRequested.connect(self.on_menu)
        self.entry.returnPressed.connect(self.on_add)

        self.set_data(self.data)
        if not self.data["lists"]:  # first run, nothing cached yet
            self.do_sync()

    # ---- background jobs: run fn, then push the cache back to the UI
    def run(self, fn):
        def job():
            try:
                fn()
            except Exception as e:
                print("tasks error:", e, file=sys.stderr)
            self.bus.data.emit(tasks.load_cache())

        threading.Thread(target=job).start()

    def do_sync(self):
        self.refresh.setEnabled(False)
        self.run(tasks.sync)

    # ---- rendering
    def set_data(self, data):
        self.data = data
        self.refresh.setEnabled(True)
        keep = self.combo.currentData()
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItem("All", "")
        for l in data["lists"]:
            self.combo.addItem(l["title"], l["id"])
        self.combo.setCurrentIndex(max(self.combo.findData(keep), 0))
        self.combo.blockSignals(False)
        self.render()

    def render(self):
        lid = self.combo.currentData()
        self.list.blockSignals(True)
        self.list.clear()
        for l in self.data["lists"]:
            if (lid and l["id"] != lid) or not l["tasks"]:
                continue
            if not lid:  # "All": small header per list
                h = QListWidgetItem(l["title"].upper())
                h.setFlags(Qt.NoItemFlags)
                h.setForeground(QColor("#6c7086"))
                f = h.font()
                f.setPointSize(8)
                f.setBold(True)
                h.setFont(f)
                self.list.addItem(h)
            for t in l["tasks"]:
                it = QListWidgetItem(t["title"])
                it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                it.setCheckState(Qt.Unchecked)
                it.setData(TASK_ID, t["id"])
                it.setData(LIST_ID, l["id"])
                if t.get("notes"):
                    it.setToolTip(t["notes"])
                self.list.addItem(it)
        self.list.blockSignals(False)
        self.entry.setEnabled(bool(lid))
        self.entry.setPlaceholderText("Add task…" if lid else "Pick a list to add tasks")

    # ---- actions
    def on_add(self):
        title, lid = self.entry.text().strip(), self.combo.currentData()
        if title and lid:
            self.entry.clear()
            self.run(lambda: tasks.add(lid, title))

    def drop(self, item, complete):
        lid, tid = item.data(LIST_ID), item.data(TASK_ID)
        self.list.takeItem(self.list.row(item))  # instant feedback
        self.run(lambda: tasks.remove(lid, tid, complete=complete))

    def on_check(self, item):
        if item.checkState() == Qt.Checked:
            self.drop(item, complete=True)

    def on_menu(self, pos):
        item = self.list.itemAt(pos)
        if not item or item.data(TASK_ID) is None:
            return
        menu = QMenu(self)
        delete = menu.addAction("Delete")
        if menu.exec(self.list.viewport().mapToGlobal(pos)) == delete:
            self.drop(item, complete=False)

    # ---- close on Esc / focus loss (but not when a dropdown or menu steals focus)
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()

    def changeEvent(self, e):
        if e.type() == QEvent.ActivationChange and not self.isActiveWindow():
            QTimer.singleShot(150, self.maybe_close)

    def maybe_close(self):
        if not self.isActiveWindow() and QApplication.activePopupWidget() is None:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Popup()
    w.show()
    sys.exit(app.exec())
