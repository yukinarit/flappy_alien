import itertools
import random
import time
import sound
import ui
from scene import *

FPS = 60

DEBUG = False


class GameObject(SpriteNode):
    """
    Game Object base class. / ゲームオブジェクト基本クラス
    """

    obj_id = 0

    def __init__(self, *args, **kwargs):
        super(GameObject, self).__init__(*args, **kwargs)
        self.id = self.get_new_id()

    def collided_with(self, other):
        """
        Collision detection. / 衝突判定
        """
        name = 'collided_with_' + type(other).__name__.lower()
        f = getattr(self, name, None)
        if f:
            f(other)

    def update(self):
        """
        Called on every game loop. / 毎フレームの更新
        """
        pass

    @property
    def body(self):
        """
        Get body size for collision detection. / 衝突判定用の矩形取得
        """
        return self.frame

    def draw_debug_info(self):
        """
        Draw object info for debugging. / デバッグ用の情報描画
        """
        if not DEBUG:
            return
        r = self.body
        path = ui.Path.rect(r.x, r.y, r.w, r.h)
        shape = ShapeNode(path, fill_color='clear', stroke_color='black', parent=self)

        label_id = LabelNode(text=str(self.id), parent=self)
        # label_coord = LabelNode(text='({},{})'.format(self.frame.x, self.frame.y), parent=self)

    def get_new_id(self):
        GameObject.obj_id += 1
        return self.obj_id


class Player(GameObject):
    """
    Game player class. / ゲームプレイヤークラス
    """
    def __init__(self, *args, **kwargs):
        super(Player, self).__init__(*args, **kwargs)

    def collided_with_block(self, other):
        """
        Handler when object gets collided with a brick. / ブロックとの衝突判定
        """
        # print(self, other)
        self.remove_from_parent()

    @property
    def body(self):
        r = self.frame
        return Rect(r.x, r.y, r.w - 10, r.h - 50)


class Brick(GameObject):
    """
    Brick object class. / ブロック
    """
    def __init__(self, *args, **kwargs):
        super(Brick, self).__init__(*args, **kwargs)

    def move(self):
        """
        Move left. / 左にスクロールする
        """
        x = self.position.x
        y = self.position.y
        dx, dy = -20, 0
        self.destination = (x + dx, y + dy)
        self.run_action(Action.move_by(dx, dy))

    def update(self):
        """
        Move left agan. Removed when it reaches to the left end. /
        左端に着くまで左にスクロールする
        """
        super(Brick, self).update()
        if self.position == self.destination:
            self.move()
        #print(self.position.x, self.parent.size.w)
        if self.position.x <= -self.parent.size.w / 2:
            self.remove_from_parent()

    def __repr__(self):
        return '[Brick] id={}'.format(self.id)


class Background(GameObject):
    """
    Background image class. / 背景画像オブジェクト
    """
    def __init__(self, *args, **kwargs):
        super(Background, self).__init__(*args, **kwargs)

    def move(self):
        """
        Move left slowly than bricks.
        左スクロールする、ブロックより少しゆっくり目。
        """
        x = self.position.x
        y = self.position.y
        dx, dy = -self.size.w, 0
        self.destination = (x + dx, y + dy)
        self.run_action(Action.move_by(dx, dy, 20), 'move')

    def update(self):
        """
        As it reaches out to the left end, it will go back to the
        original position (right end) and start scrolling left again
        so that the background looks contiguous to player.
        左端に着いたら元いた場所(右端)に戻って左スクロールを再開する。
        これによって背景画像が
        """
        super(Background, self).update()
        if self.position == self.destination:
            # self.move()
            x = self.position.x
            w = self.size.w
            self.position = (x + w, self.position.y)
            self.move()


class Game(Scene):
    """
    Game main class. / ゲームメインクラス
    """
    def setup(self):
        self.background = Background('plf:BG_Colored_grass', parent=self)
        self.background.position = self.size / 2
        self.background.size = self.size
        self.background.anchor_point = (0.5, 0.5)
        self.background.move()

        self.background2 = Background('plf:BG_Colored_grass', parent=self)
        self.background2.position = (self.size.w * 1.5, self.size.h / 2)
        self.background2.size = self.size
        self.background2.anchor_point = (0.5, 0.5)
        self.background2.move()

        self.ground = Node()
        self.add_child(self.ground)
        self.ground.position = self.size / 2
        self.ground.size = self.size
        self.ground.anchor_point = (0.5, 0.5)
        self.ground.alpha = 1.0

        self.player = Player('plf:AlienBlue_swim1')
        self.player.position = (self.size.w / 4, self.size.h / 2)
        self.player.draw_debug_info()
        self.add_child(self.player)
        self.last_spawned = 0

    def update(self):
        # Gravity calculation for alien / エイリアンの落下計算
        pos = self.player.position
        pos += (0, -4)
        pos.x = max(0, min(self.size.w, pos.x))
        pos.y = max(0, min(self.size.h, pos.y))
        self.player.position = pos
        now = time.time()

        # Spawn a new brick / 新しいブロックの生成
        if now - self.last_spawned >= (1 / FPS) * 70:
            self.spawn_block()
            self.last_spawned = time.time()

        # Collision calculation / 衝突判定
        self.check_collision(self.player, self.children)

        # Update child GameObjects / 子オブジェクトのupdateを呼ぶ
        for o in itertools.chain(self.children, self.ground.children):
            if isinstance(o, GameObject):
                o.update()

    def touch_began(self, touch):
        self.player.run_action(Action.move_by(0, 50))
        sound.play_effect('digital:HighUp')

    def spawn_block(self):
        x = self.size.w
        y = random.randint(0, self.size.y)
        block = Brick('plf:Tile_BoxCrate', position=(x, y), parent=self)
        block.draw_debug_info()
        block.move()

    def check_collision(self, obj, others):
        if not isinstance(obj, GameObject):
            return
        for other in others:
            if not isinstance(other, GameObject):
                continue
            # parent = other.parent
            # rect = other.body.translate(*parent.size * parent.anchor_point)
            rect = other.body
            if obj.body.intersects(rect):
                obj.collided_with(other)


if __name__ == '__main__':
    run(Game(), PORTRAIT, show_fps=True)
