import time
import requests
import json
from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import RecognizeCallback, AudioSource
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from browsermobproxy import Server

### CONFIG ###
apikey = ''

server = Server('browsermob-proxy-2.1.4\\bin\\browsermob-proxy.bat')
server.start()

chrome_options = webdriver.ChromeOptions()

proxy = server.create_proxy()
chrome_options.add_argument("--proxy-server={0}".format(proxy.proxy))
chrome_options.add_argument('--ignore-ssl-errors=yes')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--incognito')
driver = webdriver.Chrome('chromedriver.exe', options=chrome_options)
### CONFIG ###

class FinishRecognize(RecognizeCallback):
    def __init__(self):
        RecognizeCallback.__init__(self)

    def on_data(self, data):
        driver.find_element_by_id("audio-response").send_keys(data['results'][0]['alternatives'][0]['transcript'])
        driver.find_element_by_id("recaptcha-verify-button").click()
        print(' [!] Done.')

    def on_error(self, error):
        print('Error received: {}'.format(error))

    def on_inactivity_timeout(self, error):
        print('Inactivity timeout: {}'.format(error))

class ReCaptcha:
    def RecognizeAudio(self):
        RecognizeCallback = FinishRecognize()
        authenticator = IAMAuthenticator(apikey)
        speech_to_text = SpeechToTextV1(
            authenticator=authenticator
        )
        speech_to_text.set_service_url ('https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/edf44363-198b-489f-9aa8-a320cd094d65')
        with open('payload.mp3', 'rb') as audio:
            audio_source = AudioSource(audio)
            speech_to_text.recognize_using_websocket(
                audio=audio_source,
                content_type='audio/mpeg',
                recognize_callback=RecognizeCallback,
                model='en-US_BroadbandModel',
                keywords=['verdict', 'is', 'hot'],
                keywords_threshold=0,
                max_alternatives=3)

    def start(self):
        proxy.new_har()
        driver.get('https://google.com/recaptcha/api2/demo')

        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it(
            (By.CSS_SELECTOR, "iframe[src^='https://www.google.com/recaptcha/api2/anchor']")))
        driver.find_element_by_css_selector("div[class^='rc-anchor-center']").click()
        driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it(
            (By.CSS_SELECTOR, "iframe[title='recaptcha challenge']")))

        time.sleep(3)
        
        driver.find_element_by_css_selector("button[class='rc-button goog-inline-block rc-button-audio']").click()

        time.sleep(3)
        for entry in proxy.har["log"]["entries"]:
            if entry["request"]["url"].startswith('https://www.google.com/recaptcha/api2/payload') and entry['response']['content']['mimeType'] != 'image/jpeg':
                payload = entry["request"]["url"]

        response = requests.get(payload, stream=True)
        open('payload.mp3', 'wb').write(response.content)
        self.RecognizeAudio()
            
if __name__ == "__main__":
    main = ReCaptcha()
    main.start()
