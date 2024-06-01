import os
import uuid
import sqlite3
from cryptography.fernet import Fernet, InvalidToken
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QMessageBox, \
    QSplitter, QHBoxLayout, QComboBox, QTabWidget, QLineEdit, QLabel, QFormLayout, QFontComboBox, QSpinBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from dotenv import load_dotenv
from markdown import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from openai import OpenAI
from pygments.formatters.html import HtmlFormatter
from bs4 import BeautifulSoup
import openai
import re

# Encryption setup
KEY_FILE = "encryption.key"


def load_or_generate_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            key = key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
    return key


encryption_key = load_or_generate_key()
cipher_suite = Fernet(encryption_key)

# Database setup
db_path = "settings.db"


def initialize_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            theme TEXT,
            font_name TEXT,
            font_size INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY,
            api_key TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_api_key(api_key):
    encrypted_api_key = cipher_suite.encrypt(api_key.encode())
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO api_keys (id, api_key) VALUES (1, ?)", (encrypted_api_key,))
    conn.commit()
    conn.close()


def load_api_key():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT api_key FROM api_keys WHERE id = 1")
    result = cursor.fetchone()
    conn.close()
    if result:
        try:
            decrypted_api_key = cipher_suite.decrypt(result[0]).decode()
            return decrypted_api_key
        except InvalidToken:
            QMessageBox.warning(None, "Invalid Token",
                                "The stored API key could not be decrypted. Please re-enter your API key.")
            return ""
    return ""


def save_font_settings(font_name, font_size):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (id, font_name, font_size) VALUES (1, ?, ?)",
                   (font_name, font_size))
    conn.commit()
    conn.close()


def load_font_settings():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT font_name, font_size FROM settings WHERE id = 1")
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0], result[1]
    return "Arial", 12  # default font settings if none are saved


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPT-4 Markdown Renderer")
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.main_widget = QWidget()
        self.settings_widget = QWidget()

        self.tabs.addTab(self.main_widget, "Main")
        self.tabs.addTab(self.settings_widget, "Settings")

        self.setup_main_tab()
        self.setup_settings_tab()

    def setup_main_tab(self):
        self.layout = QVBoxLayout(self.main_widget)

        self.splitter = QSplitter(Qt.Vertical)

        self.prompt_entry = QTextEdit(self)
        self.prompt_entry.setPlaceholderText("Enter your prompt")

        self.web_view = QWebEngineView(self)

        self.splitter.addWidget(self.prompt_entry)
        self.splitter.addWidget(self.web_view)

        self.layout.addWidget(self.splitter)

        self.controls_widget = QWidget(self)
        self.controls_layout = QHBoxLayout(self.controls_widget)

        self.model_selector = QComboBox(self)
        self.model_selector.addItems(["gpt-3.5-turbo", "gpt-4", "gpt-4o"])
        self.controls_layout.addWidget(self.model_selector)

        self.fetch_button = QPushButton("Generate Markdown", self)
        self.fetch_button.clicked.connect(self.fetch_and_display)

        self.copy_all_button = QPushButton("Copy All Content", self)
        self.copy_all_button.clicked.connect(self.copy_all_content)

        self.controls_layout.addWidget(self.fetch_button)
        self.controls_layout.addWidget(self.copy_all_button)

        self.layout.addWidget(self.controls_widget)

        self.raw_markdown = ""

    def setup_settings_tab(self):
        self.settings_layout = QFormLayout(self.settings_widget)

        self.api_key_input = QLineEdit(self)
        self.api_key_input.setPlaceholderText("Enter your OpenAI API Key")
        saved_api_key = load_api_key()
        if saved_api_key:
            self.api_key_input.setText(saved_api_key)

        self.save_api_key_button = QPushButton("Save API Key", self)
        self.save_api_key_button.clicked.connect(self.save_api_key)

        self.font_combo_box = QFontComboBox(self)
        self.font_size_spin_box = QSpinBox(self)
        self.font_size_spin_box.setRange(8, 48)

        saved_font_name, saved_font_size = load_font_settings()
        self.font_combo_box.setCurrentFont(QFont(saved_font_name))
        self.font_size_spin_box.setValue(saved_font_size)

        self.save_font_settings_button = QPushButton("Save Font Settings", self)
        self.save_font_settings_button.clicked.connect(self.save_font_settings)

        self.settings_layout.addRow(QLabel("OpenAI API Key:"), self.api_key_input)
        self.settings_layout.addWidget(self.save_api_key_button)
        self.settings_layout.addRow(QLabel("Font:"), self.font_combo_box)
        self.settings_layout.addRow(QLabel("Font Size:"), self.font_size_spin_box)
        self.settings_layout.addWidget(self.save_font_settings_button)

    def fetch_and_display(self):
        openai_api_key = load_api_key()

        if not openai_api_key:
            QMessageBox.critical(self, "Error", "OpenAI API Key not set. Please enter it in the settings tab.")
            return

        user_prompt = self.prompt_entry.toPlainText()

        if not user_prompt:
            QMessageBox.warning(self, "Input Error", "Please enter a prompt.")
            return

        model = self.model_selector.currentText()

        try:
            completion = self.send_gpt_request(openai_api_key, model, user_prompt)
            response = completion.choices[0].message.content
            self.raw_markdown = response

            codehilite = CodeHiliteExtension(linenums=False, css_class='codehilite')
            fenced_code = FencedCodeExtension()
            html_content = markdown(response, extensions=[codehilite, fenced_code])

            html_content = self.add_code_headers_and_copy_buttons(html_content, response)

            self.web_view.setHtml(html_content)

            self.splitter.setSizes([100, 500])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def send_gpt_request(self, api_key, model, prompt):
        # Set up the OpenAI client with the provided API key
        client = OpenAI()
        client.api_key = api_key

        # Prepare and send the request to OpenAI
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": f"{prompt}: "}],
            stream=False  # Stream responses to process them as they arrive
        )

        return completion

    def extract_languages_from_markdown(self, markdown_content):
        pattern = re.compile(r'```(\w+)?')
        matches = pattern.findall(markdown_content)
        languages = ['plaintext' if not lang else lang for lang in matches]
        return languages

    def add_code_headers_and_copy_buttons(self, html_content, markdown_content):
        languages = self.extract_languages_from_markdown(markdown_content)

        style = "monokai"
        background_color = "#2E2E2E"
        text_color = "#d8dee9"

        full_html_content = f"""
        <html>
        <head>
            <style>
                {HtmlFormatter(style=style).get_style_defs('.codehilite')}
                .code-block-container {{
                    position: relative;
                    margin-bottom: 20px;
                    border: 1px solid #e1e4e8;
                    border-radius: 6px;
                    overflow: hidden;
                }}
                .code-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: {background_color};
                    padding: 8px;
                    font-size: 12px;
                    font-family: Arial, sans-serif;
                    color: {text_color};
                    border-bottom: 1px solid #e1e4e8;
                }}
                .code-header .language {{
                    font-weight: bold;
                }}
                .code-header button.copy-button {{
                    background: none;
                    border: none;
                    color: #0366d6;
                    cursor: pointer;
                    font-size: 12px;
                }}
                pre {{
                    background: {background_color};
                    color: {text_color};
                    border-radius: 0 0 6px 6px;
                    padding: 10px;
                    overflow: auto;
                    margin: 0;
                }}
            </style>
        </head>
        <body>
            {html_content}
            <script>
            function copyToClipboard(button) {{
                var codeBlock = button.parentNode.nextSibling;
                var text = codeBlock.innerText || codeBlock.textContent;
                var tempTextArea = document.createElement("textarea");
                tempTextArea.value = text;
                document.body.appendChild(tempTextArea);
                tempTextArea.select();
                document.execCommand("copy");
                document.body.removeChild(tempTextArea);
                button.innerText = "Copied";
                setTimeout(function() {{
                    button.innerText = "Copy";
                }}, 10000);
            }}
            </script>
        </body>
        </html>
        """

        soup = BeautifulSoup(full_html_content, 'html.parser')

        code_blocks = soup.find_all('div', class_='codehilite')
        for index, code_block in enumerate(code_blocks):
            unique_id = str(uuid.uuid4())
            code_block['id'] = unique_id

            language = languages[index] if index < len(languages) else 'plaintext'

            div = soup.new_tag('div', **{'class': 'code-block-container', 'id': unique_id})
            code_block.wrap(div)

            header = soup.new_tag('div', **{'class': 'code-header'})
            language_span = soup.new_tag('span', **{'class': 'language'})
            language_span.string = language
            button = soup.new_tag('button', **{'class': 'copy-button', 'onclick': f'copyToClipboard(this)'})
            button.string = "Copy"

            header.insert(0, language_span)
            header.insert(1, button)

            div.insert(0, header)

        return str(soup)

    def copy_all_content(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.raw_markdown)
        QMessageBox.information(self, "Copied", "The entire content has been copied to the clipboard.")

    def save_api_key(self):
        api_key = self.api_key_input.text()
        if api_key:
            save_api_key(api_key)
            QMessageBox.information(self, "Saved", "API Key has been saved.")
        else:
            QMessageBox.warning(self, "Input Error", "Please enter a valid API Key.")

    def save_font_settings(self):
        font_name = self.font_combo_box.currentFont().family()
        font_size = self.font_size_spin_box.value()
        save_font_settings(font_name, font_size)
        self.prompt_entry.setFontFamily(font_name)
        self.prompt_entry.setFontPointSize(font_size)
        QMessageBox.information(self, "Saved", "Font settings have been saved.")


if __name__ == "__main__":
    initialize_database()
    load_dotenv()

    app = QApplication([])
    window = MainWindow()
    saved_font_name, saved_font_size = load_font_settings()
    window.prompt_entry.setFontFamily(saved_font_name)
    window.prompt_entry.setFontPointSize(saved_font_size)
    window.show()
    app.exec_()
