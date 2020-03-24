from gtts import gTTS
from subprocess import call

def criar_audio(texto, nome_arquivo):
    tts = gTTS(texto, lang='pt-br')
    path = 'audios/' + nome_arquivo + '.mp3'
    with open(path, 'wb') as file:
        tts.write_to_fp(file)
    call(['mpg321', path])

criar_audio('Prontinho, algo mais senhor?', 'algo_mais')