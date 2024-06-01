@echo off
REM List of unnecessary packages to be uninstalled
set UNNECESSARY_PACKAGES=annotated-types anyio blinker certifi cffi charset-normalizer click colorama distro Flask h11 httpcore httpx idna itsdangerous Jinja2 joblib MarkupSafe nltk numpy pillow pycparser pydantic pydantic_core regex scikit-learn scipy sniffio soupsieve threadpoolctl tkhtmlview tkinterweb tqdm typing_extensions urllib3 Werkzeug

REM Loop through each package and uninstall it
for %%i in (%UNNECESSARY_PACKAGES%) do (
    echo Uninstalling %%i...
    pip uninstall -y %%i
)

echo Uninstallation of unnecessary packages is complete.
pause
