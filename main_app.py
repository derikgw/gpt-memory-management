import os
import uuid
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from dotenv import load_dotenv
from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from pygments.formatters.html import HtmlFormatter
from bs4 import BeautifulSoup
import api_client


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPT-4o Markdown Renderer")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.prompt_entry = QLineEdit(self)
        self.prompt_entry.setPlaceholderText("Enter your prompt")
        self.layout.addWidget(self.prompt_entry)

        self.fetch_button = QPushButton("Generate Markdown", self)
        self.fetch_button.clicked.connect(self.fetch_and_display)
        self.layout.addWidget(self.fetch_button)

        self.web_view = QWebEngineView(self)
        self.layout.addWidget(self.web_view)

    def fetch_and_display(self):
        # Access the OpenAI API key
        openai_api_key = os.getenv('OPENAI_API_KEY')

        if not openai_api_key:
            QMessageBox.critical(self, "Error", "OPENAI_API_KEY not set in .env file.")
            return

        # Get the user input from the input box
        user_prompt = self.prompt_entry.text()

        if not user_prompt:
            QMessageBox.warning(self, "Input Error", "Please enter a prompt.")
            return

        # Define the model
        model = "gpt-4o-2024-05-13"

        # Send request to GPT API
        response = api_client.send_gpt_request(openai_api_key, model, user_prompt)

        # Convert Markdown to HTML with code highlighting
        codehilite = CodeHiliteExtension(linenums=False, css_class='codehilite')
        html_content = markdown(response, extensions=[codehilite, 'fenced_code'])

        # Add headers and "Copy" buttons to code blocks
        html_content = self.add_code_headers_and_copy_buttons(html_content)

        # Display in QWebEngineView
        self.web_view.setHtml(html_content)

    def add_code_headers_and_copy_buttons(self, html_content):
        # Ensure the HTML content has necessary structure
        full_html_content = f"""
        <html>
        <head>
            <style>
                {HtmlFormatter().get_style_defs('.codehilite')}
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
                    background: #333333;  /* Darker background for more contrast */
                    padding: 8px;
                    font-size: 12px;
                    font-family: Arial, sans-serif;
                    color: #ffffff;  /* White text for better contrast */
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
                    background: #000000;  /* Set background to black */
                    color: #d8dee9;      /* Set text color to a light color */
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

        # Parse the HTML
        soup = BeautifulSoup(full_html_content, 'html.parser')

        # Find all code blocks
        for code_block in soup.find_all('div', class_='codehilite'):
            # Create a unique identifier
            unique_id = str(uuid.uuid4())
            code_block['id'] = unique_id

            # Wrap the code block in a div with a unique identifier
            div = soup.new_tag('div', **{'class': 'code-block-container', 'id': unique_id})
            code_block.wrap(div)

            # Create a header
            header = soup.new_tag('div', **{'class': 'code-header'})
            language = soup.new_tag('span', **{'class': 'language'})
            language.string = "python"  # This should be dynamically set based on actual language
            button = soup.new_tag('button', **{'class': 'copy-button', 'onclick': f'copyToClipboard(this)'})
            button.string = "Copy"

            # Insert the language and button into the header
            header.insert(0, language)
            header.insert(1, button)

            # Insert the header before the code block
            div.insert(0, header)

        # Return the modified HTML content as a string
        return str(soup)


if __name__ == "__main__":
    load_dotenv()

    app = QApplication([])

    window = MainWindow()
    window.show()

    app.exec_()
