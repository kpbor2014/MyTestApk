from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty, ListProperty, BooleanProperty, OptionProperty, \
    ReferenceListProperty, StringProperty
from kivy.graphics import Color, Triangle, Rectangle, Ellipse, Line, InstructionGroup
from kivy.uix.image import Image
from kivy.core.audio import SoundLoader
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.lang import Builder
from random import randint

Builder.load_string("""
#:kivy 2.0.0

<Playground>
    canvas:
        Color:
            rgba:[0.3,0.6,0.04,1]
        Rectangle:
            pos: self.pos
            size: self.size

    snake: snake_id
    fruit: fruit_id

    Snake:
        id: snake_id
        width: root.width/root.col_number
        height: root.height/root.row_number

    Fruit:
        id: fruit_id
        width: root.width/root.col_number
        height: root.height/root.row_number

    Label:
        font_size: 70
        center_x: root.x + root.width/root.col_number*2
        top: root.top - root.height/root.row_number
        text: str(root.score)

<Snake>
    head: snake_head_id
    tail: snake_tail_id

    SnakeHead:
        id: snake_head_id
        width: root.width
        height: root.height

    SnakeTail:
        id: snake_tail_id
        width: root.width
        height: root.height

# Добавления экранов управления игрой (3-я часть, 6 commit)

<WelcomeScreen>
    canvas:
        Color:
            rgba:[0,0.4,0,1]
        Rectangle:
            pos: self.pos
            size: self.size
    AnchorLayout:
        anchor_x: "center"

        BoxLayout:
            orientation: "vertical"
            size_hint: (1, 1)
            spacing: 10

            Label:
                size_hint_y: .4
                text: "Змейка"
                valign: "bottom"
                bold: False
                font_size: 0.2*self.height
                padding: 0, 0

            AnchorLayout:
                anchor_x: "center"
                size_hint_y: .6

                BoxLayout:
                    size_hint: .5, .5
                    orientation: "vertical"
                    spacing: 10

                    Button:
                        halign: "center"
                        valign: "middle"
                        text: "Играть"
                        font_size: 0.3*self.height
                        on_press: root.manager.current = "playground_screen"

                    Button:
                        halign: "center"
                        valign: "middle"
                        text: "Настройки"
                        font_size: 0.3*self.height
                        on_press: root.show_popup()

<PlaygroundScreen>:
    game_engine: playground_widget_id

    Playground:
        id: playground_widget_id

# Добавление виджетов для настроек отключенния границ экрана
# и скорости змейки (3-я часть, 7 commit)

<OptionsPopup>
    border_option_widget: border_option_widget_id
    speed_option_widget: speed_option_widget_id

    title: "Настройки"
    size_hint: .75, .75

    BoxLayout:
        orientation: "vertical"
        spacing: 20

        GridLayout:
            size_hint_y: .8
            cols: 2

            Label:
                text: "Без границ"
                halign: "center"

            Switch:
                id: border_option_widget_id

            Label:
                text: "Скорость Змейки"
                halign: "center"

            Slider:
                id: speed_option_widget_id
                max: 10
                min: 1
                step: 1
                value: 1

        AnchorLayout:
            anchor_x: "center"
            size_hint: 1, .25

            Button:
                size_hint: 0.6, 0.8
                text: "Сохранить"
                font_size: 0.3*self.height
                on_press: root.dismiss()


<VictoryScreen>
    canvas:
        Color:
            rgba:[0,0.4,0,1]
        Rectangle:
            pos: self.pos
            size: self.size
    AnchorLayout:
        anchor_x: "center"

        BoxLayout:
            orientation: "vertical"
            size_hint: (1, 1)
            spacing: 10

            Label:
                size_hint_y: .4
                text: "Ура!!! Змейка объелась!!!"
                font_size: 0.2*self.height
                valign: "bottom"
                bold: False
                padding: 0, 0

            AnchorLayout:
                anchor_x: "center"
                size_hint_y: .6

                Button:
                    size_hint: 0.5, 0.3
                    halign: "center"
                    valign: "middle"
                    text: "Продолжить"
                    font_size: 0.3*self.height
                    on_press: root.manager.current = "welcome_screen"


""")


class Playground(Widget):
    # root and children widget containers (корневой контейнер и контейнер дочерних виджетов)
    fruit = ObjectProperty(None)
    snake = ObjectProperty(None)

    # настройки пользователя - скорости и отключения границ
    start_speed = NumericProperty(1)
    border_option = BooleanProperty(False)

    # параметры сетки (выбраны 32-ширина, 18 высота)
    col_number = 32
    row_number = 18

    # game variables (игровые переменные)
    score = NumericProperty(0)
    turn_counter = NumericProperty(0)
    fruit_rhythm = NumericProperty(0)

    start_time_coeff = NumericProperty(1)
    running_time_coeff = NumericProperty(1)

    fr = NumericProperty(0)  # переменная события съедения фрукта

    # user input handling (обработка пользовательского ввода)
    touch_start_pos = ListProperty()
    action_triggered = BooleanProperty(False)

    def start(self):
        # если опция border_option False, рисуем прямоугольник вокруг игровой области
        if self.border_option == False:
            with self.canvas.after:
                self.l1 = Line(width=2., rectangle=(self.x, self.y, self.width, self.height))
        else:
            with self.canvas.after:
                self.l1 = Line(width=0.1, rectangle=(self.x, self.y, self.width, self.height))

        # вычислить временной коэф-т (time coeff),используемый как частота обновления для игры,
        # используя предоставленные параметры (default 1.1, max 2)
        # мы сохраняем значение дважды, чтобы сохранить ссылку в случае
        # сброса (действительно, running_time_coeff будет увеличиваться в игре, если
        # фрукт был съеден)
        self.start_time_coeff += (self.start_speed / 10)
        self.running_time_coeff = 1

        # нарисовать новую змейку
        self.new_snake()

        # запустить цикл обновления
        self.update()

    def reset(self):
        # сбросить игровые переменные
        self.turn_counter = 0
        self.score = 0
        self.running_time_coeff = self.start_time_coeff

        # удаляем виджет змейки и фрукт
        self.snake.remove()
        self.fruit.remove()

        # непланируем все события в случае сброса
        # (они будут перенесены в механизм перезапуска)
        Clock.unschedule(self.pop_fruit)
        Clock.unschedule(self.fruit.remove)
        Clock.unschedule(self.update)

    def new_snake(self):
        # генерируем случайные координаты
        start_coord = (
            randint(10, self.col_number - 10), randint(6, self.row_number - 6))

        # установливаем случайные координаты исходного положения змеи
        self.snake.set_position(start_coord)

        # генерируем случайное направление
        rand_index = randint(0, 3)
        start_direction = ["Up", "Down", "Left", "Right"][rand_index]

        # устанавливаем случайное исходное направление змейки
        self.snake.set_direction(start_direction)

    def pop_fruit(self, *args):
        # получаем случайные координаты фрукта
        random_coord = [
            randint(2, self.col_number - 1), randint(2, self.row_number - 1)]

        # получаем позиции всех ячеек, занятых змеей
        snake_space = self.snake.get_full_position()

        # если координаты находятся в ячейке, занятой змейкой, переопределяем координаты на незанятые
        while random_coord in snake_space:
            random_coord = [
                randint(2, self.col_number - 1), randint(2, self.row_number - 1)]

        # вставляем фруктовый виджет в сгенерированные координаты
        self.fruit.pop(random_coord)

    def is_defeated(self):
        """
        Функция используется для проверки, соответствует ли текущее положение змеи поражению.
        """
        snake_position = self.snake.get_position()

        # если змея кусает себя за хвост: поражение
        if snake_position in self.snake.tail.blocks_positions:
            return True

        # если змейка вышла за границы и опция нет границ выключена - False, то Конец Игры
        if self.border_option == False:
            if snake_position[0] > self.col_number \
                    or snake_position[0] < 1 \
                    or snake_position[1] > self.row_number \
                    or snake_position[1] < 1:
                return True

        return False

    def handle_outbound(self):
        """
         Используется для замены змеи на противоположной стороне, если она выходит за пределы
        (вызывается только в том случае, если для параметра границы установлено значение False)
        """
        position = self.snake.get_position()
        direction = self.snake.get_direction()

        if position[0] == 1 and direction == "Left":
            # добавить текущую позицию головы как хвостовой блок
            # иначе один блок будет пропущен обычной подпрограммой
            self.snake.tail.add_block(list(position))
            self.snake.set_position([self.col_number + 1, position[1]])
        elif position[0] == self.col_number and direction == "Right":
            self.snake.tail.add_block(list(position))
            self.snake.set_position([0, position[1]])
        elif position[1] == 1 and direction == "Down":
            self.snake.tail.add_block(list(position))
            self.snake.set_position([position[0], self.row_number + 1])
        elif position[1] == self.row_number and direction == "Up":
            self.snake.tail.add_block(list(position))
            self.snake.set_position([position[0], 0])

    def update(self, *args):
        """
        Функция используется для перехода игры к новому ходу.
        """
        # регистрирование фруктов в возрастающей последовательности в планировщике событий
        if self.turn_counter == 0:
            self.fruit_rythme = self.fruit.interval + self.fruit.duration
            Clock.schedule_interval(self.fruit.remove, self.fruit_rythme / self.running_time_coeff)
        elif self.turn_counter == self.fruit.interval:
            self.fruit.remove()
            self.pop_fruit()
            Clock.schedule_interval(self.pop_fruit, self.fruit_rythme / self.running_time_coeff)
        elif self.fr == 1:
            self.fruit.remove()
            self.pop_fruit()
            self.fr = 0
            Clock.unschedule(self.pop_fruit)
            Clock.unschedule(self.fruit.remove)
            Clock.schedule_interval(self.fruit.remove, self.fruit_rythme / self.running_time_coeff)
            Clock.schedule_interval(self.pop_fruit, self.fruit_rythme / self.running_time_coeff)

        #  если игра без границ - border_option=True, проверьте, собирается ли змейка покинуть экран
        # если да, замените на соответствующую противоположную границу
        if self.border_option:
            self.handle_outbound()

        # переместить змейку в следующую позицию
        self.snake.move()

        # проверка на поражение
        # если это так, сбросить и перезапустить игру
        if self.is_defeated():
            self.reset()
            # переход на экран приветствия
            sound = SoundLoader.load('sound/ups.wav')
            sound.play()
            SnakeApp.screen_manager.current = "welcome_screen"
            return

        # проверяем, наличие и съеден ли фрукт
        if self.fruit.is_on_board():
            if self.snake.get_position() == self.fruit.pos:
                # если это так, играем звук, удаляем плод, увеличиваем счет и размер хвоста, увеличиваем темп на 5%
                self.fr = 1  # событие, что фрукт съеден
                sound = SoundLoader.load('sound/eat.wav')
                sound.play()
                self.fruit.remove()
                self.score += 1
                self.snake.tail.size += 1
                self.running_time_coeff *= 1.05

                # Проверка условия победы - съедено установленное кол-во фруктов
                if self.score > 5:
                    sound = SoundLoader.load('sound/victory.wav')
                    sound.play()
                    self.reset()
                    SnakeApp.screen_manager.current = "victory_screen"
                    return

        # увеличиваем счетчик
        self.turn_counter += 1

        # расписание обновляется каждую секунду  (1'')
        Clock.schedule_once(self.update, 0.35 / self.running_time_coeff)

    def on_touch_down(self, touch):
        self.touch_start_pos = touch.spos

    def on_touch_move(self, touch):
        # вычисляем перевод из начальной позиции в текущую позицию
        delta = Vector(*touch.spos) - Vector(*self.touch_start_pos)

        # проверяем, не была ли команда еще отправлена, и если перевод
        # составляет > 10% от размера экрана
        if not self.action_triggered and (abs(delta[0]) > 0.1 or abs(delta[1]) > 0.1):
            # если это так, установливаем соответствующее направление для змеи
            if abs(delta[0]) > abs(delta[1]):
                if delta[0] > 0:
                    self.snake.set_direction("Right")
                else:
                    self.snake.set_direction("Left")
            else:
                if delta[1] > 0:
                    self.snake.set_direction("Up")
                else:
                    self.snake.set_direction("Down")
            # регистрируем, что действие было инициировано, чтобы
            # оно не повторилось дважды за один ход
            self.action_triggered = True

    def on_touch_up(self, touch):
        # готовы принять новую инструкцию касания экрана
        self.action_triggered = False


class Fruit(Widget):
    # константы, используемые для вычисления fruit_rhythme - периода появления фрукта
    # значения выражают количество ходов
    duration = NumericProperty(10)
    interval = NumericProperty(1)

    # представление на холсте
    object_on_board = ObjectProperty(None)
    state = BooleanProperty(False)

    def is_on_board(self):
        return self.state

    def remove(self, *args):
        # мы принимаем * args, потому что этот метод будет
        # передан диспетчеру событий, поэтому он получит dt аргумент.
        if self.is_on_board():
            self.canvas.remove(self.object_on_board)
            self.object_on_board = ObjectProperty(None)
            self.state = False

    def pop(self, pos):
        self.pos = pos  # используется для проверки начала употребления плода

        # Рисунок фруктов
        # (который просто круг, поэтому предполагаю , что это яблоко)
        with self.canvas:
            Color(1, 1, 1)
            x = (pos[0] - 1) * self.size[0]
            y = (pos[1] - 1) * self.size[1]
            coord = (x, y)

            # сохранение представления и обновление состояния объекта с фоном картинки яблоко
            self.object_on_board = Ellipse(source='images/apple.png', pos=coord, size=self.size)
            self.state = True
            Color(1, 1, 1)


class Snake(Widget):
    # children widgets containers (контейнер дочерних виджетов)
    head = ObjectProperty(None)
    tail = ObjectProperty(None)

    def move(self):
        """
        Перемещение змейки состоит из 3 шагов:
            - сохранить текущее положение головы, так как оно будет использовано для добавления блока к хвосту.
            - переместить голову на одну клетку в текущем направлении.
            - добавляем новый хвостовой блок к хвосту.
        """
        next_tail_pos = list(self.head.position)
        self.head.move()
        self.tail.add_block(next_tail_pos)

    def remove(self):
        """
        В нашей текущей змейке удаление всего объекта сводится к удалению его головы и хвоста, поэтому нам просто нужно вызвать соответствующие методы. Как они занимаются этим - их проблема, а не Змеи. Это просто происходит вниз по команде.
        """
        self.head.remove()
        self.tail.remove()

    def set_position(self, position):
        self.head.position = position

    def get_position(self):
        """
        Мы рассматриваем положение Змеи как положение, занимаемое головой.
        """
        return self.head.position

    def get_full_position(self):
        """
        Но иногда нам нужно знать весь набор ячеек, занятых
         змейкой.
        """
        return self.head.position + self.tail.blocks_positions

    def set_direction(self, direction):
        self.head.direction = direction

    def get_direction(self):
        return self.head.direction


class SnakeHead(Widget):
    nn = 0  # используется для переключения картинки с открытым и закрытым ртом
    # представление в «сетке» игрового поля
    direction = OptionProperty(
        "Right", options=["Up", "Down", "Left", "Right"])
    x_position = NumericProperty(0)
    y_position = NumericProperty(0)
    position = ReferenceListProperty(x_position, y_position)

    # представление на холсте
    points = ListProperty([0] * 2)
    object_on_board = ObjectProperty(None)
    state = BooleanProperty(False)

    def is_on_board(self):
        return self.state

    def remove(self):
        if self.is_on_board():
            self.canvas.remove(self.object_on_board)
            self.object_on_board = ObjectProperty(None)
            self.state = False

    def show(self):
        """
        Фактический рендеринг головы змеи. Представление - это просто
        Треугольник ориентирован в соответствии с направлением объекта
        """
        with self.canvas:
            Color(1, 1, 0)
            if not self.is_on_board():
                self.object_on_board = Ellipse(source='images/head.png', pos=self.points, size=self.size)
                self.state = True  # object is on board
            else:
                # если объект уже на борту, удалить старое представление
                # перед рисованием нового
                # рисуем с фоном головы в соответствии со значением nn
                if self.nn == 0:
                    if self.direction == "Right":
                        self.canvas.remove(self.object_on_board)
                        self.object_on_board = Ellipse(source='images/head0R.png', pos=self.points, size=self.size)
                    elif self.direction == "Left":
                        self.canvas.remove(self.object_on_board)
                        self.object_on_board = Ellipse(source='images/head0L.png', pos=self.points, size=self.size)
                    elif self.direction == "Up":
                        self.canvas.remove(self.object_on_board)
                        self.object_on_board = Ellipse(source='images/head0Up.png', pos=self.points, size=self.size)
                    elif self.direction == "Down":
                        self.canvas.remove(self.object_on_board)
                        self.object_on_board = Ellipse(source='images/head0D.png', pos=self.points, size=self.size)

                else:
                    if self.direction == "Right":
                        self.canvas.remove(self.object_on_board)
                        self.object_on_board = Ellipse(source='images/head1R.png', pos=self.points, size=self.size)
                    elif self.direction == "Left":
                        self.canvas.remove(self.object_on_board)
                        self.object_on_board = Ellipse(source='images/head1L.png', pos=self.points, size=self.size)
                    elif self.direction == "Up":
                        self.canvas.remove(self.object_on_board)
                        self.object_on_board = Ellipse(source='images/head1Up.png', pos=self.points, size=self.size)
                    elif self.direction == "Down":
                        self.canvas.remove(self.object_on_board)
                        self.object_on_board = Ellipse(source='images/head1D.png', pos=self.points, size=self.size)

            Color(1, 1, 1)

    def move(self):
        """
        Это решение не очень изящно. Но оно работает.
        Положение обновляется в соответствии с текущим направлением. Набор из
        точки, представляющие треугольник, повернутый в направлении объекта,
        вычисляется и сохраняется как свойство.
        Затем вызывается метод show () для визуализации треугольника.
        """
        # переключатель nn для смены картинки головы
        if self.nn == 0:
            self.nn = 1
        else:
            self.nn = 0

        # обновление позиции
        if self.direction == "Right":
            self.position[0] += 1
            # вычисление множества точек
            x0 = (self.position[0] - 1) * self.width
            y0 = (self.position[1] - 1) * self.height
        elif self.direction == "Left":
            self.position[0] -= 1
            x0 = (self.position[0] - 1) * self.width
            y0 = (self.position[1] - 1) * self.height
        elif self.direction == "Up":
            self.position[1] += 1
            x0 = (self.position[0] - 1) * self.width
            y0 = (self.position[1] - 1) * self.height
        elif self.direction == "Down":
            self.position[1] -= 1
            x0 = (self.position[0] - 1) * self.width
            y0 = (self.position[1] - 1) * self.height

        # сохранение точек как свойства(списка)
        self.points = [x0, y0]
        # представление треугольника/эллепса
        self.show()


class SnakeTail(Widget):
    # tail length, in number of blocks (длина хвоста в количестве блоков)
    size = NumericProperty(3)

    # blocks positions on the Playground's grid (позиции блоков в сетке)
    blocks_positions = ListProperty()

    # blocks objects drawn on the canvas (блокирует объекты, нарисованные на холсте)
    tail_blocks_objects = ListProperty()

    def remove(self):
        # сбросить размер змейки
        self.size = 3

        # удалить каждый блок хвоста с холста
        # вот почему нам здесь не нужна is_on_board () здесь:
        # если блока нет на борту, его нет и в списке
        # поэтому мы не можем пытаться удалить не нарисованный объект

        for block in self.tail_blocks_objects:
            self.canvas.remove(block)

        # очищаем списки, содержащие координаты блоков
        # и изображения на холсте
        self.blocks_positions = []
        self.tail_blocks_objects = []

    def add_block(self, pos):
        """
        Здесь происходят 3 вещи:
            - новая позиция блока, переданная в качестве аргумента, добавляется к список объектов.
            - количество элементов в списке при необходимости адаптируется всплывающим самый старый блок.
            - блоки нарисованы на холсте, и процесс такой же, как и раньше происходит так, что наш список блочных объектов сохраняет постоянный размер.
        """
        # добавить новую позицию блока в список
        self.blocks_positions.append(pos)

        # контролировать количество блоков в списке
        if len(self.blocks_positions) > self.size:
            self.blocks_positions.pop(0)

        with self.canvas:
            # рисуем блоки в соответствии с позициями, хранящимися в списке
            Color(0, 0, 1)
            for block_pos in self.blocks_positions:
                x = (block_pos[0] - 1) * self.width
                y = (block_pos[1] - 1) * self.height
                coord = (x, y)
                block = Ellipse(pos=coord, size=(self.width, self.height))

                # добавить новый объект блока в список
                self.tail_blocks_objects.append(block)

                # контролировать количество блоков в списке и удалять с холста
                # при необходимости
                if len(self.tail_blocks_objects) > self.size:
                    last_block = self.tail_blocks_objects.pop(0)
                    self.canvas.remove(last_block)
            Color(1, 1, 1)


class WelcomeScreen(Screen):
    options_popup = ObjectProperty(None)

    def show_popup(self):
        # создать экземпляр всплывающего окна и отобразить его
        self.options_popup = OptionsPopup()
        self.options_popup.open()


class PlaygroundScreen(Screen):
    game_engine = ObjectProperty(None)

    def on_enter(self):
        # мы видим экран, запускаем игру
        self.game_engine.start()


class OptionsPopup(Popup):
    border_option_widget = ObjectProperty(None)
    speed_option_widget = ObjectProperty(None)

    def on_dismiss(self):
        Playground.start_speed = self.speed_option_widget.value
        Playground.border_option = self.border_option_widget.active


class VictoryScreen(Screen):
    pass


class SnakeApp(App):
    screen_manager = ObjectProperty(None)

    def build(self):
        # объявить ScreenManager как свойство класса
        SnakeApp.screen_manager = ScreenManager()

        # создаем экраны
        ws = WelcomeScreen(name="welcome_screen")
        ps = PlaygroundScreen(name="playground_screen")
        vs = VictoryScreen(name="victory_screen")

        # регистрируем экраны в диспетчере экранов
        self.screen_manager.add_widget(ws)
        self.screen_manager.add_widget(ps)
        self.screen_manager.add_widget(vs)

        return self.screen_manager


if __name__ == '__main__':
    SnakeApp().run()

