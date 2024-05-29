from application.notification import NotificationCenter
from sipsimple.account import AccountManager, Account
from sipsimple.application import SIPApplication
from sipsimple.core import SIPURI, ToHeader
from sipsimple.lookup import DNSLookup, DNSLookupError
from sipsimple.storage import FileStorage
from sipsimple.session import Session
from sipsimple.streams.rtp.audio import AudioStream
from sipsimple.threading.green import run_in_green_thread
from sipsimple.configuration.settings import SIPSimpleSettings
from sipsimple.audio import WavePlayer, AudioBridge
from threading import Event
import time
from copy import copy

class SimpleCallApplication(SIPApplication):
    def __init__(self):
        SIPApplication.__init__(self)
        self.ended = Event()
        self.callee = None
        self.session = None
        self.notification_center = NotificationCenter()
        self.notification_center.add_observer(self)

    def call(self, callee):
        self.callee = callee
        self.start(FileStorage('config'))

    @run_in_green_thread
    def _NH_SIPApplicationDidStart(self, notification):
        self.callee = ToHeader(SIPURI.parse(self.callee))
        try:
            routes = DNSLookup().lookup_sip_proxy(self.callee.uri, ['udp']).wait()
        except DNSLookupError as e:
            print('DNS lookup failed: %s' % str(e))
        else:
            account = Account('187188@sip.zadarma.com')
            account.auth.password = 'GerDitOdalsvegen300Ja'
            account.enabled = True
            self.session = Session(account)
            stream = AudioStream()
            self.session.connect(self.callee, routes, [stream])

    def _NH_WavePlayerDidStart(self, notification):
        print('Wave player started', notification)

    def _NH_WavePlayerDidFail(self, notification):
        print('Wave player failed', notification)

    def _NH_RTPAudioStreamGotDTMF(self, notification):
        print('GOT DTMF', notification)

    def _NH_SIPSessionGotRingIndication(self, notification):
        print('Ringing!')

    def _NH_SIPSessionDidStart(self, notification):
        audio_stream = notification.data.streams[0]
        print('Audio session established using "%s" codec at %sHz' % (audio_stream.codec, audio_stream.sample_rate))

    def _NH_SIPSessionDidFail(self, notification):
        print('Failed to connect')
        self.stop()

    def _NH_SIPSessionDidEnd(self, notification):
        print('Session ended')
        self.stop()

    def _NH_SIPApplicationDidEnd(self, notification):
        self.ended.set()


class SimpleWakeUpApplication(SIPApplication):
    def __init__(self):
        SIPApplication.__init__(self)
        self.ended = Event()
        self.callee = None
        self.session = None
        self.notification_center = NotificationCenter()
        self.notification_center.add_observer(self)

        # 16bit PCM mono/single channel (any clock rate is supported)
        self.stream = None
        self.previous_wave_player = None
        self.has_gotten_dtmf = False

    def call(self, callee):
        self.callee = callee
        self.start(FileStorage('config'))

    @run_in_green_thread
    def _NH_SIPApplicationDidStart(self, notification):
        self.callee = ToHeader(SIPURI.parse(self.callee))
        try:
            routes = DNSLookup().lookup_sip_proxy(self.callee.uri, ['udp']).wait()
        except DNSLookupError as e:
            print('DNS lookup failed: %s' % str(e))
        else:
            account = Account('187188@sip.zadarma.com')
            account.auth.password = 'GerDitOdalsvegen300Ja'
            account.enabled = True
            self.session = Session(account)
            self.stream = AudioStream()
            # removes defaut input/output sources
            self.stream.bridge = AudioBridge(self.stream.mixer)
            self.session.connect(self.callee, routes, [self.stream])

    def _NH_WavePlayerDidStart(self, notification):
        print('Wave player started', notification)

    def _NH_WavePlayerDidFail(self, notification):
        print('Wave player failed', notification)

    @run_in_green_thread
    def _NH_RTPAudioStreamGotDTMF(self, notification):
        if self.has_gotten_dtmf == True:
            return
        self.has_gotten_dtmf = True
        print('GOT DTMF', notification.data.digit, notification)
        
        if notification.data.digit not in ['1','2','3']:
            wave_player = WavePlayer(self.stream.mixer, '/home/gerhard/Dokumenter/programming/goip3/feil.wav', volume=200)
            self.stream.bridge.remove(self.previous_wave_player)
            self.stream.bridge.add(wave_player)
            self.previous_wave_player = wave_player
            wave_player.play().wait()
            self.has_gotten_dtmf = False

            wave_player = WavePlayer(self.stream.mixer, '/home/gerhard/Dokumenter/programming/goip3/svar.wav', volume=200)
            self.stream.bridge.remove(self.previous_wave_player)
            self.stream.bridge.add(wave_player)
            self.previous_wave_player = wave_player
            wave_player.play().wait()
            return

        wave_player = WavePlayer(self.stream.mixer, f'/home/gerhard/Dokumenter/programming/goip3/digits/{notification.data.digit}.wav', volume=200)
        self.stream.bridge.remove(self.previous_wave_player)
        self.stream.bridge.add(wave_player)
        self.previous_wave_player = wave_player
        wave_player.play().wait()
        self.stop()


    def _NH_SIPSessionGotRingIndication(self, notification):
        print('Ringing!')

    @run_in_green_thread
    def _NH_SIPSessionDidStart(self, notification):
        # self.stream = notification.data.streams[0]
        print('Audio session established using "%s" codec at %sHz' % (self.stream.codec, self.stream.sample_rate))
        wave_player = WavePlayer(self.stream.mixer, '/home/gerhard/Dokumenter/programming/goip3/svar.wav', volume=200)
        self.stream.bridge.add(wave_player)
        self.previous_wave_player = wave_player
        wave_player.play().wait()

    def _NH_SIPSessionDidFail(self, notification):
        print('Failed to connect')
        self.stop()

    def _NH_SIPSessionDidEnd(self, notification):
        print('Session ended')
        self.stop()

    def _NH_SIPApplicationDidEnd(self, notification):
        self.ended.set()

# place an audio call to the specified SIP URI in user@domain format
target_uri="sip:+4747332982@sip.zadarma.com"
application = SimpleWakeUpApplication()
application.call(target_uri)
print("Placing call to %s, press Enter to quit the program" % target_uri)
input()
application.session.end()
application.ended.wait()
