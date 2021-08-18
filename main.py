from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.audio import SoundLoader
from kivy.properties import StringProperty
from kivy.properties import ColorProperty
from kivy.uix.button import Button

nn=0
kk=1

class PongGame(Widget):
    pass

class Akulele1App(App):
    message = StringProperty()
    message1 = StringProperty()
    colors = ColorProperty()
    colors1 = ColorProperty()

    def build(self):
        global game
        game = PongGame()
        self.message = "Нота"
        self.colors = [1, 0.1, 0, 1]
        self.message1 = "Играть"
        self.colors1 = [0,1,0,1]
        return game

    def on_press_button(self):
        global game, nn, mm, sound

        if nn==0:
            sound.play()
            self.message1 = "Стоп"
            self.colors1 = [1, 0, 0, 1]
            nn=1
        elif nn==1:
            sound.stop()
            self.message1 = "Играть"
            self.colors1 = [0, 1, 0, 1]
            nn=0
        return game

    def stop_ping(self):
        pass

# Изменить ноту
    def level_ping(self):
        global kk, message, sound
        if kk == 1:
            self.message = "Ля"
            self.colors = [0.9, 0.2, 0.8, 1]
            sound = SoundLoader.load('music/notela1.wav')
            kk = 2
        elif kk == 2:
            self.message = "Ми"
            self.colors = [0, 0.8, 0.05, 1]
            sound = SoundLoader.load('music/notemi2.wav')
            kk = 3
        elif kk == 3:
            self.message = "До"
            self.colors = [0, 0.80, 1, 1]
            sound = SoundLoader.load('music/notedo3.wav')
            kk = 4
        elif kk == 4:
            self.message = "Соль"
            self.colors = [1, 0.2, 0.2, 1]
            sound = SoundLoader.load('music/notesol4.wav')
            kk = 1
        return kk


if __name__ == '__main__':
        Akulele1App().run()