# coding=UTF-8
import speech_recognition as sr
from requests import get
from bs4 import BeautifulSoup
from gtts import gTTS
from paho.mqtt import publish
import json
import os

##### FLAG PARA CONTROLE #####
executar_acao = False

hotword = 'antonieta'
hotNoticias = 'notícias'
hotPrevisao = 'qual a previsão do tempo hoje'
hotObrigado = 'Não obrigado'
hotIrrigar = 'ligar a irrigacao'

##### CONFIGURAÇÕES DA CHAVE DO GOOGLE #####
with open('.env.json', 'r') as credenciais:
    credenciais = json.load(credenciais)

##### CONFIGURAÇÕES DO MQTT #####
server_mqtt = credenciais['mqtt']['server']
porta_mqtt = '14909'
topico_irrigacao = '/onoff/rele'
topico_combo_acoes = '/onoff/combo'
usuario_mqtt = credenciais['mqtt']['usuario']
senha_mqtt = credenciais['mqtt']['senha']

    
def monitorar_audio():
    microfone = sr.Recognizer()
    with sr.Microphone() as source:
        print("Aguardando o Comando: ")
        microfone.adjust_for_ambient_noise(source)
        audio = microfone.listen(source)
    try:
        trigger = microfone.recognize_google_cloud(
            audio, credentials_json=credenciais['google'], language='pt-BR')
        trigger = trigger.lower()
        print(trigger)
        if hotword in trigger and not get_status_trigger():
            print('Comando reconhecido!')
            responder('feedback')
            set_status_trigger(True)
        elif get_status_trigger():
            set_status_trigger(False)
            return trigger
    except sr.UnknownValueError:
        print("Google not understand audio")
    except sr.RequestError as e:
        print(
            "Could not request results from Google Cloud Speech service; {0}".format(e))

    return None
    
def analisar_acao(comando):
    if hotNoticias in comando:
        print('Comando reconhecido! Notícias!')
        responder_ultimas_noticias()
    elif hotIrrigar in comando:
        publicar_no_topico(topico_irrigacao, 0)
    elif hotPrevisao in comando:
        print('Comando reconhecido! Previsão!')
        retornarPrevisaoTempo()
    elif hotObrigado in comando:
        responder('tchau')

def publicar_no_topico(topico, payload):
    publish.single(topico, payload=payload, qos=1, retain=True, hostname=server_mqtt,
        auth={'username': usuario_mqtt, 'password': senha_mqtt})

def responder_ultimas_noticias():
    site = get('https://news.google.com/news/rss?ned=pt_br&gl=BR&hl=pt')
    noticias = BeautifulSoup(site.text, 'html.parser')

    for item in noticias.findAll('item')[:5]:
        noticia = item.title.text
        criar_audio(noticia, 'noticia')
        responder('noticia')
    
    responder('algo_mais')

def retornarPrevisaoTempo():
    site = get('http://api.openweathermap.org/data/2.5/weather?id=3462377&q=goiania,br&APPID=1d20fd1ca254ea2797f60e64520675a8&units=metric&lang=pt')
    clima = site.json()
    temperatura = clima['main']['temp']
    #minima = clima['main']['temp_min']
    #maxima = clima['main']['temp_max']
    descricao = clima['weather'][0]['description']
    mensagem = f'No momento a temperatura é de {temperatura} graus celsius com {descricao}'
    criar_audio(mensagem, 'clima')
    responder('clima')
    responder('algo_mais')

def criar_audio(texto, nome_arquivo):
    tts = gTTS(texto, lang='pt-br')
    path = 'audios/' + nome_arquivo + '.mp3'
    with open(path, 'wb') as file:
        tts.write_to_fp(file)


def responder(nome_arquivo):
    path = 'audios/' + nome_arquivo + '.mp3'
    os.system('mpg321 ' + path)


def set_status_trigger(status):
    global executar_acao
    executar_acao = status


def get_status_trigger():
    return executar_acao

def __main__():
    while True:
        comando = monitorar_audio()
        if comando is not None:
            analisar_acao(comando)

__main__()
