# Doc for MadArtist TxtParse BaseVoiceGenerator
This is a guide of making a custom BaseVoiceGenerator. 
## \_\_init\_\_.py

- **Class Main**: The core class of the generator
- **Func Main.generate**: The function of BaseVoice TTS. It was defined like below:
```python
def generate(self, txt: str, note: str | int | float) -> pathlib.Path
'''Generate the voice of the txt with the note and save it to the path of the voice. The Voice of the BaseVoiceGenerator will be automatically choosen.
:param txt: The text to be converted to voice.
:param note: The note of the voice(if str: like C3, D4, E4, etc. if int: like 3000, 4000, 5000, etc. in Hz. if float: like 233.91 etc. in Hz.).'''
```
- **Func Main.EditConfig**: The function of editing the config of the generate function. It was defined like below:
```python
def EditConfig(self, **kwargs) -> None
```
### The Main Class is defined like below:
```python
import pathlib
class Main:
    def __init__(self):
        ...
    def generate(self, txt: str, note: str | int | float) -> pathlib.Path:
        ...
    def EditConfig(self, *args, **kwargs) -> None:
        ...
```
## config.py

- **Func User_ConfigEdit**: The function of editing the config of the generate function in the ui form based on PyQt6. It was defined like below:
```python
def User_ConfigEdit() -> dict:
    ...
```
- **Func NonUser_ConfigEdit**: The function of saving the config of the generate function in the non-ui form. It was defined like below:
```python
def NonUser_ConfigEdit(**kwargs): -> dict:
    ...
```
### The config.py is defined like below:
```python
...
def User_ConfigEdit() -> dict:
    ...
def NonUser_ConfigEdit(**kwargs): -> dict:
    ...
```
