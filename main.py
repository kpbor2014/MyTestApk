from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import (
    NumericProperty, ReferenceListProperty, ObjectProperty
)
from kivy.vector import Vector
from kivy.clock import Clock
from random import randint
from kivy.core.audio import SoundLoader
from kivy.properties import StringProperty
from kivy.uix.button import Button

sound = SoundLoader.load('music/beep0.wav')
sound.play()

nn=0
kk=1

class PongPaddle(Widget):
    score = NumericProperty(0) ## очки игрока

    ## Отскок мячика при коллизии с панелькой игрока
    def bounce_ball(self, ball):
        if self.collide_widget(ball):
            vx, vy = ball.velocity
            offset = (ball.center_y - self.center_y) / (self.height / 2)
            bounced = Vector(-1 * vx, vy)
            vel = bounced * 1.1
            ball.velocity = vel.x, vel.y + offset
            sound = SoundLoader.load('music/beep2.wav')
            sound.play()

class PongPaddle1(Widget):
    score = NumericProperty(0) ## очки игрока

    ## Отскок мячика при коллизии с панелькой игрока
    def bounce_ball(self, ball):
        if self.collide_widget(ball):
            vx, vy = ball.velocity
            offset = (ball.center_y - self.center_y) / (self.height / 2)
            bounced = Vector(-1 * vx, vy)
            vel = bounced * 1.1
            ball.velocity = vel.x, vel.y + offset
            sound = SoundLoader.load('music/beep5.wav')
            sound.play()


class PongBall(Widget):

    # Скорость движения нашего шарика по двум осям
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)

    # Создаем условный вектор
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    # Заставим шарик двигаться
    def move(self):
        self.pos = Vector(*self.velocity) + self.pos

class PongGame(Widget):
    ball = ObjectProperty(None) # это будет наша связь с объектом шарика
    player1 = ObjectProperty(None) # Игрок 1
    player2 = ObjectProperty(None) # Игрок 2

    def serve_ball(self, vel=(4, 0)):
        self.ball.center = self.center
        self.ball.velocity = Vector(vel[0], vel[1]).rotate(randint(-45, 45)*(randint(0,1)+180))
    def update(self, dt):
        global nn, vel
        self.ball.move() # двигаем шарик в каждом обновлении экрана

        # проверка отскока шарика от панелек игроков
        self.player1.bounce_ball(self.ball)
        self.player2.bounce_ball(self.ball)

        # отскок шарика по оси Y
        if (self.ball.y < self.y) or (self.ball.top > self.top):
            self.ball.velocity_y *= -1
        # Перемещение ракетки компьютера при игре с ИИ
        if kk==2:
            if self.ball.x < 0.6*self.width:
                self.player2.center_y =self.ball.y
            elif self.ball.x >= 0.6 and self.ball.x < 0.9 :
                self.player2.center_y = self.ball.y + randint(0, 50)*randint(-1,1)

        # отскок шарика по оси X
        # тут если шарик смог уйти за панельку игрока, то есть игрок не успел отбить шарик
        # то это значит что он проиграл и мы добавим +1 очко противнику
        if nn==0:
            if self.ball.x < self.x:
                # Первый игрок проиграл, добавляем 1 очко второму игроку
                self.player2.score += 1
                sound = SoundLoader.load('music/beep1.wav')
                sound.play()
                self.serve_ball(vel=(4, 0)) # заново спавним шарик в центре
                if self.player2.score > 4:
                    Pong4App.stop_ping(self)
                    sound = SoundLoader.load('music/beep7.wav')
                    sound.play()

            if self.ball.x > self.width:
                # Второй игрок проиграл, добавляем 1 очко первому игрок
                self.player1.score += 1
                sound = SoundLoader.load('music/beep4.wav')
                sound.play()
                self.serve_ball(vel=(-4, 0)) # заново спавним шарик в центре
                if self.player1.score > 4:
                    Pong4App.stop_ping(self)
                    sound = SoundLoader.load('music/beep7.wav')
                    sound.play()
        elif nn==1:
            self.player1.score = 0
            self.player2.score = 0
            vel=(0,0)
            nn=0

    # Событие прикосновения к экрану
    def on_touch_move(self, touch):
        # первый игрок может касаться только своей части экрана (левой)
        if touch.x < self.width / 7:
            self.player1.center_y = touch.y
        # второй игрок может касаться только своей части экрана (правой)
        if kk==1:
           if touch.x > self.width - self.width / 7:
               self.player2.center_y = touch.y


class Pong4App(App):
    message = StringProperty()

    def build(self):
        global game
        game = PongGame()
        # game.serve_ball()
        # Clock.schedule_interval(game.update, 1.0 / 60.0)# 60 FPS
        self.message = "С игроком"
        return game

    def on_press_button(self):
        global game, nn, mm
        nn=1
        game.serve_ball()
        Clock.schedule_interval(game.update, 1.0 / 30)# 60 FPS
        return game

    def stop_ping(self):
        global game
        self.ball.center = self.center
        self.ball.velocity = vel
        return game

# Изменить уровень
    def level_ping(self):
        global kk, message
        if kk == 2:
            self.message = "С игроком"
            kk = 1
        elif kk == 1:
            self.message = "С ИИ"
            kk = 2
        return kk


if __name__ == '__main__':
    Pong4App().run()