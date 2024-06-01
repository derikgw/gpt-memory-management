import os
import uuid
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QMessageBox, \
    QSplitter, QHBoxLayout, QComboBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt
from dotenv import load_dotenv
from markdown import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from openai import OpenAI
from pygments.formatters.html import HtmlFormatter
from pygments.styles import get_style_by_name
from bs4 import BeautifulSoup
import openai
import re


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPT-4 Markdown Renderer")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

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

    def fetch_and_display(self):
        openai_api_key = os.getenv('OPENAI_API_KEY')

        if not openai_api_key:
            QMessageBox.critical(self, "Error", "OPENAI_API_KEY not set in .env file.")
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

        style = get_style_by_name('monokai')
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
                    background: #333333;
                    padding: 8px;
                    font-size: 12px;
                    font-family: Arial, sans-serif;
                    color: #ffffff;
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
                    background: #000000;
                    color: #d8dee9;
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


if __name__ == "__main__":
    load_dotenv()

    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
