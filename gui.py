"""
Interface graphique de l'orchestrateur véhicule (PyQt6) — version tableau de bord.

Panneau de gauche : conversation avec l'assistant véhicule.
Panneau de droite : tableau de bord visuel (jauges + icônes d'état),
                     mis à jour automatiquement après chaque commande.

Prérequis :
    pip install PyQt6

Lancement :
    python3 gui.py
"""

import sys
import os
import anthropic
from dotenv import load_dotenv

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QProgressBar, QFrame,
    QScrollArea
)

from orchestrator import run_command
from vehicle_controllers import vehicle  # instance partagée, on lit ses attributs directement

load_dotenv()


STYLE_SHEET = """
QWidget {
    background-color: #1e1f26;
    color: #e8e8ec;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QTextEdit {
    background-color: #262832;
    border: 1px solid #383a46;
    border-radius: 8px;
    padding: 8px;
}
QLineEdit {
    background-color: #262832;
    border: 1px solid #383a46;
    border-radius: 6px;
    padding: 8px;
}
QLineEdit:focus {
    border: 1px solid #5b8cff;
}
QPushButton {
    background-color: #5b8cff;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #4574e6;
}
QPushButton:disabled {
    background-color: #3a3d4a;
    color: #888;
}
QPushButton#resetButton {
    background-color: #383a46;
}
QPushButton#resetButton:hover {
    background-color: #45485a;
}
QFrame#card {
    background-color: #262832;
    border-radius: 10px;
}
QLabel#cardTitle {
    font-weight: 600;
    font-size: 13px;
    color: #a8acc0;
}
QLabel#cardValue {
    font-weight: 700;
    font-size: 18px;
    color: #e8e8ec;
}
QLabel#cardSub {
    font-size: 12px;
    color: #888ca0;
}
QProgressBar {
    border: none;
    border-radius: 5px;
    background-color: #383a46;
    height: 10px;
    text-align: center;
}
QProgressBar::chunk {
    border-radius: 5px;
}
"""


def gauge_color(percent: float, invert: bool = False) -> str:
    """Return a color (green -> orange -> red) according to a percentage."""
    if invert:
        percent = 100 - percent
    if percent < 40:
        return "#4caf50"   # vert
    elif percent < 75:
        return "#ffb74d"   # orange
    else:
        return "#ef5350"   # rouge


class Card(QFrame):
    """Reusable widget : a frame with title + gauge + value."""

    def __init__(self, title: str, min_val: int = 0, max_val: int = 100, unit: str = ""):
        super().__init__()
        self.setObjectName("card")
        self.unit = unit
        self.min_val = min_val
        self.max_val = max_val

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        top_row.addWidget(self.title_label)
        top_row.addStretch()
        self.value_label = QLabel("")
        self.value_label.setObjectName("cardValue")
        top_row.addWidget(self.value_label)
        layout.addLayout(top_row)

        self.bar = QProgressBar()
        self.bar.setRange(min_val, max_val)
        self.bar.setTextVisible(False)
        layout.addWidget(self.bar)

        self.sub_label = QLabel("")
        self.sub_label.setObjectName("cardSub")
        layout.addWidget(self.sub_label)

    def update_value(self, value: int, sub_text: str = "", invert_color: bool = False):
        self.bar.setValue(value)
        self.value_label.setText(f"{value}{self.unit}")
        self.sub_label.setText(sub_text)
        span = max(self.max_val - self.min_val, 1)
        percent = (value - self.min_val) / span * 100
        color = gauge_color(percent, invert=invert_color)
        self.bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")


class StatusCard(QFrame):
    """Widget for a boolean status (on/off) with an icon and a subtitle."""

    def __init__(self, title: str, icon_on: str, icon_off: str):
        super().__init__()
        self.setObjectName("card")
        self.icon_on = icon_on
        self.icon_off = icon_off

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        top_row.addWidget(self.title_label)
        top_row.addStretch()
        self.icon_label = QLabel("")
        self.icon_label.setStyleSheet("font-size: 20px;")
        top_row.addWidget(self.icon_label)
        layout.addLayout(top_row)

        self.sub_label = QLabel("")
        self.sub_label.setObjectName("cardSub")
        self.sub_label.setWordWrap(True)
        layout.addWidget(self.sub_label)

    def update_value(self, is_on: bool, sub_text: str = ""):
        self.icon_label.setText(self.icon_on if is_on else self.icon_off)
        self.sub_label.setText(sub_text)


class VehicleGUI(QWidget):
    def __init__(self, client: anthropic.Anthropic):
        super().__init__()
        self.client = client
        self.conversation_history = []

        self.setWindowTitle("Vehicle orchestrator - Dashboard")
        self.resize(1000, 600)
        self.setStyleSheet(STYLE_SHEET)
        self._build_ui()
        self._refresh_state()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)

        main_layout.addLayout(self._build_chat_panel(), stretch=3)
        main_layout.addLayout(self._build_dashboard_panel(), stretch=2)

    def _build_chat_panel(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        header = QLabel("💬 Vehicle assistant")
        header.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(header)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        layout.addWidget(self.chat_area)

        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Write your command here...")
        self.input_field.returnPressed.connect(self._send_command)
        input_row.addWidget(self.input_field)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._send_command)
        input_row.addWidget(self.send_button)
        layout.addLayout(input_row)

        reset_button = QPushButton("🧹 Reset conversation")
        reset_button.setObjectName("resetButton")
        reset_button.clicked.connect(self._reset_conversation)
        layout.addWidget(reset_button)

        return layout

    def _build_dashboard_panel(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        header = QLabel("🚗 Dashboard")
        header.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        grid = QGridLayout(content)
        grid.setSpacing(12)

        self.temp_card = Card("🌡️ Temperature", 16, 30, "°C")
        self.speed_card = Card("🚗 Speed", 0, 200, " km/h")
        self.fuel_card = Card("⛽ Fuel", 0, 100, "%")
        self.volume_card = Card("🔊 Volume", 0, 100, "")
        self.music_card = StatusCard("🎵 Music", "🎶 ON", "🔇 OFF")
        self.lights_card = StatusCard("💡 Lights", "💡 ON", "⚫ OFF")
        self.nav_card = StatusCard("🗺️ Navigation", "📍", "—")

        grid.addWidget(self.temp_card, 0, 0)
        grid.addWidget(self.speed_card, 0, 1)
        grid.addWidget(self.fuel_card, 1, 0)
        grid.addWidget(self.volume_card, 1, 1)
        grid.addWidget(self.music_card, 2, 0)
        grid.addWidget(self.lights_card, 2, 1)
        grid.addWidget(self.nav_card, 3, 0, 1, 2)

        grid.setRowStretch(4, 1)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return layout

    def _send_command(self):
        user_text = self.input_field.text().strip()
        if not user_text:
            return

        self.chat_area.append(f"<b style='color:#5b8cff;'>Toi :</b> {user_text}")
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)

        try:
            reply = run_command(user_text, self.conversation_history, self.client)
            self.chat_area.append(f"<b style='color:#4caf50;'>Vehicle :</b> {reply}<br>")
        except Exception as e:
            self.chat_area.append(f"<span style='color:#ef5350'><b>Error :</b> {e}</span><br>")

        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus()
        self._refresh_state()

    def _reset_conversation(self):
        self.conversation_history = []
        self.chat_area.append("<i style='color:#888ca0;'>🧹 Conversation history cleared.</i><br>")

    def _refresh_state(self):
        self.temp_card.update_value(vehicle.temperature["value"])
        self.speed_card.update_value(vehicle.speed["value"])
        self.fuel_card.update_value(vehicle.fuel_level["value"], invert_color=True)
        self.volume_card.update_value(vehicle.music["volume"])

        self.music_card.update_value(
            vehicle.music["on"],
            sub_text=f"Station : {vehicle.music['Station']}"
        )
        self.lights_card.update_value(
            vehicle.lights["headlights"],
            sub_text=f"Luminosité : {vehicle.lights['luminosity']}%"
        )
        destination = vehicle.navigation["destination"]
        self.nav_card.update_value(
            destination is not None,
            sub_text=destination if destination else "No destination defined"
        )


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  Environment variable missing.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    app = QApplication(sys.argv)
    window = VehicleGUI(client)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()