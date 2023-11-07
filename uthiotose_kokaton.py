import math
import random
import sys
import time
import pygame as pg
WIDTH = 1600 # ゲームウィンドウの幅
HEIGHT = 900 # ゲームウィンドウの高さ
def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj：オブジェクト（爆弾，戦闘機，ビーム）SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right: # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom: # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：戦闘機SurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Aircraft(pg.sprite.Sprite):
    """
    戦闘機に関するクラス
    """
    delta = { # 押下キーと移動量の辞書
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }


    def __init__(self, xy: tuple[int, int]):
        """
        戦闘機画像Surfaceを生成する
        引数1 xy：戦闘機画像の位置座標タプル
        """
        super().__init__()
        self.img = pg.transform.rotozoom(pg.image.load(f"ex05/fig/sentouki.png"), 0, 0.25)
        self.dire = (+1, 0)
        self.rect = self.img.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state="nomal"
        self.hyper_life=-1


    def change_img(self, screen: pg.Surface):
        """
        戦闘機画像を切り替え，画面に転送する
        引数1 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/explosion.gif"), 0, 1.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じて戦闘機を移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if check_bound(self.rect) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed*mv[0], -self.speed*mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            # self.image = self.imgs[self.dire]
        if self.state == "hyper":
           self.hyper_life -= 1
           self.img=pg.transform.laplacian(self.img)
        if self.hyper_life < 0:
            self.change_state("nomal",-1)
        screen.blit(self.img, self.rect)


    def get_direction(self) -> tuple[int, int]:
        return self.dire


    def change_state(self,state,hyper_life):
        self.state=state
        self.hyper_life=hyper_life


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    def __init__(self, emy: "Enemy", aircraft: Aircraft):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象の戦闘機
        """
        super().__init__()
        rad = random.randint(10, 50) # 爆弾円の半径：10以上50以下の乱数
        color = random.choice(__class__.colors) # 爆弾円の色：クラス変数からランダム選択
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のaircraftの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, aircraft.rect)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height/2
        self.speed = 6


    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class BossBomb(pg.sprite.Sprite):
    colors = [(255, 0, 255), (1, 0, 0), (1, 0, 0), (1, 0, 0), (255, 0, 255), (0, 0, 1)]
    def __init__(self, emy: "Enemy", aircraft: Aircraft):
        """
        ここではボスの攻撃を作る
        ボスの爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のプレイヤー　ここは今後名前を変える。
        """
        super().__init__()
        rad = random.randint(50, 80)  # 爆弾円の半径：50以上100以下の乱数
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, aircraft.rect)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height/2
        self.speed = 4

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class SmallBossBomb(pg.sprite.Sprite):
    colors = [(255, 255, 0), (0, 255, 255), (0, 0, 255), (255, 0, 0), (255, 255, 255), (200, 70, 120)]
    def __init__(self, emy: "Enemy", aircraft: Aircraft):
        """
        ここではボスの周りを旋回する小さい敵の攻撃を作る
        小さいボスの爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のプレイヤー　ここは今後名前を変える。
        """
        super().__init__()
        small_rad=random.randint(10,30)
        color=random.choice(__class__.colors)
        self.image = pg.Surface((2*small_rad, 2*small_rad))
        pg.draw.circle(self.image, color, (small_rad, small_rad), small_rad)
        self.image.set_colorkey((0,0,0))
        self.rect=self.image.get_rect()
        self.vx, self.vy = calc_orientation(emy.rect, aircraft.rect)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height/2
        self.speed = 8

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, aircraft: Aircraft):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つ戦闘機
        """
        super().__init__()
        self.vx, self.vy = (0,-1) # bird.get_direction()
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"ex04/fig/beam.png"), angle, 2.0) 
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = aircraft.rect.centery+aircraft.rect.height*self.vy
        self.rect.centerx = aircraft.rect.centerx+aircraft.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Charge_Beam(pg.sprite.Sprite):
    """
    チャージビームに関するクラス。
    """
    def __init__(self, aircraft: Aircraft, x:int):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        引数x：チャージ回数
        """
        super().__init__()
        self.vx, self.vy = (0,-1)
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        if 10 <= x <20:
            self.image = pg.transform.rotozoom(pg.image.load(f"ex04/fig/beam.png"), angle, 3.0)
        elif 20 <= x:
            self.image = pg.transform.rotozoom(pg.image.load(f"ex04/fig/beam.png"), angle, 5.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = aircraft.rect.centery+aircraft.rect.height*self.vy
        self.rect.centerx = aircraft.rect.centerx+aircraft.rect.width*self.vx
        self.speed = 10


    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "BossBomb|Bomb|SmallBossBomb|Enemy", life: int): 
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load("ex05/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life


    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"ex05/fig/alien{i}.png") for i in range(1, 4)]

    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +6
        self.bound = random.randint(50, HEIGHT/2) # 停止位置
        self.state = "down" # 降下状態or停止状態
        self.interval = random.randint(50, 300) # 爆弾投下インターバル


    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy

        # if WIDTH/2 > self.rect[0]:
        #     self.image = self.image2 #画面の左半分だったらこうかとんの画像を反転する


class Boss(pg.sprite.Sprite):
    """
    Bossに関するクラス
    """
    def __init__(self):
        super().__init__()
        self.image = pg.image.load("ex05/fig/pattie.png")
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH/2, HEIGHT/3)
        self.interval = random.randint(100, 300)


class Boss_HP:
    """
    BossのHPに関するクラス
    """
    def __init__(self, life):
        self.life=life
        self.now_life=life
        self.font = pg.font.Font(None, 80)
        self.color = (0, 2, 0)
        self.img = self.font.render(f"HP: {self.now_life}", 0, self.color)
        self.rect2 = self.img.get_rect()
        self.rect2.center = 600, 100

    def update(self, screen: pg.Surface):
        self.img = self.font.render(f"HP: {self.now_life}", 0, self.color)
        screen.blit(self.img, self.rect2)


class S_Boss(pg.sprite.Sprite):
    """
    小さなBossに関するクラス
    """
    def __init__(self, wi):
        super().__init__()
        self.wi=wi
        self.image = pg.transform.rotozoom(pg.image.load("ex05/fig/kamatou.png"), 0, 0.3)
        self.rect = self.image.get_rect()
        self.rect.center = (self.wi, 100)
        self.vx, self.vy = 5, 5
        self.interval = random.randint(20, 100)

    def update(self):
        """
        上下左右に揺れる動きをする
        """
        if self.rect.centery > 450:
            self.vy *= -1
        if self.rect.centery < 100:
            self.vy *= -1
        if self.rect.centerx > self.wi+250:
            self.vx *= -1
        if self.rect.centerx < self.wi-100:
            self.vx *= -1
        self.rect.centerx += self.vx
        self.rect.centery += self.vy


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.score = 0
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def score_up(self, add):
        self.score += add

    def score_down(self,sa):
        self.score -= sa

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.image, self.rect)

class Beam_status:
    """
    ビームの状態を表すステータス。ビームのクラスではなく状態を表示させる。
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 255, 255)
        self.image = self.font.render(f"normal_beam", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 300, HEIGHT-50

    def update(self, screen: pg.Surface, x:int):
        """
        x：ビームのチャージ回数。20が一番上それ以上は変わらない
        """
        if x < 10:
            self.image = self.font.render(f"normal BEAM", 0, self.color)
        elif 10 <= x < 20:
            self.image = self.font.render(f"charge BEAM", 0, (255,255,0))
        elif 20 <= x:
            self.image = self.font.render(f"super BEAM", 0, (255,0,0))
        screen.blit(self.image, self.rect)


def main():
    pg.display.set_caption("こうかとんを撃ち落とす")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("ex05/fig/pg_bg.jpg")
    boss_attack = False
    score = Score()
    aircraft = Aircraft((800, 825))
    beam_status = Beam_status()
    bombs = pg.sprite.Group()
    boss_bombs=pg.sprite.Group()
    small_bombs=pg.sprite.Group()
    beams = pg.sprite.Group()
    charge_beam = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    boss = pg.sprite.Group()
    s_boss = pg.sprite.Group()
    boss_hp = Boss_HP(100)
    tmr = 0
    x = 0
    clock = pg.time.Clock()

    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if x < 10:
                    beams.add(Beam(aircraft))
                else:
                    charge_beam.add(Charge_Beam(aircraft,x))
                    x = 0
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and score.score > 100:
                score.score_down(100)
                aircraft.change_state("hyper",500)
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                x += 1


            if event.type == pg.KEYDOWN and event.key == pg.K_LSHIFT:
                aircraft.speed = 20
            if event.type == pg.KEYUP and event.key == pg.K_LSHIFT:
                aircraft.speed = 10
        screen.blit(bg_img, [0, 0])

        if not boss_attack:
            if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
                emys.add(Enemy())

            for emy in emys:
                if emy.state == "stop" and tmr%emy.interval == 0:
                    # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                    bombs.add(Bomb(emy, aircraft))

        if boss_attack:
            for bos in boss:
                if tmr%200 == 0:
                    boss_bombs.add(BossBomb(bos, aircraft))

            for bos in s_boss:
                if tmr%100 == 0:
                    small_bombs.add(SmallBossBomb(bos, aircraft))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.score_up(10)  # 10点アップ

        # チャージビームの判定
        for emy in pg.sprite.groupcollide(emys, charge_beam, True, False).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.score_up(10)  # 10点アップ
            aircraft.change_img(screen)

        for bomb in pg.sprite.groupcollide(boss_bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト

        for bomb in pg.sprite.groupcollide(small_bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト

        for bos in pg.sprite.groupcollide(boss, beams, False, True).keys():
            exps.add(Explosion(bos, 50))  # 爆発エフェクト
            boss_hp.now_life -= 1

        for bos in pg.sprite.groupcollide(boss, charge_beam, False, True).keys():
            exps.add(Explosion(bos, 50))  # 爆発エフェクト
            boss_hp.now_life -= 1

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        # チャージビームの判定
        for bomb in pg.sprite.groupcollide(bombs, charge_beam, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        for bomb in pg.sprite.groupcollide(boss_bombs, charge_beam, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        for bomb in pg.sprite.groupcollide(small_bombs, charge_beam, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50)) # 爆発エフェクト
            score.score_up(1) # 1点アップ

        for bomb in pg.sprite.spritecollide(aircraft, bombs, True):
            if aircraft.state=="hyper":
                exps.add(Explosion(bomb, 50))
                score.score_up(1)
            if aircraft.state=="nomal":
                aircraft.change_img(screen)
                score.font = pg.font.Font(None, 250)
                score.rect.center = WIDTH/2-250, HEIGHT/2 #スコアをやられた際に真ん中に表示

            if aircraft.state=="nomal":
                aircraft.change_img(screen) # 戦闘機爆発エフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return

        if len(pg.sprite.spritecollide(aircraft, bombs, True)) != 0:
            aircraft.change_img(screen)

            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        if len(pg.sprite.spritecollide(aircraft,boss_bombs,True)) !=0:#ボス用こうかとんの当たり判定
            aircraft.change_img(screen)
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        if len(pg.sprite.spritecollide(aircraft,small_bombs,True)) !=0:#小ボス用こうかとんの当たり判定
            aircraft.change_img(screen)
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        if len(pg.sprite.spritecollide(aircraft, bombs, True)) != 0:
            aircraft.change_img(screen) # 戦闘機爆発エフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        if boss_attack:
            boss.draw(screen)
            boss_hp.update(screen)
            s_boss.update()
            s_boss.draw(screen)
            small_bombs.update()
            boss_bombs.update()
            small_bombs.draw(screen)
            boss_bombs.draw(screen)
        else:
            emys.update()
            emys.draw(screen)
        aircraft.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        charge_beam.update()
        charge_beam.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        beam_status.update(screen, x)
        if score.score > 20 and boss_attack==False:
            boss_attack = True
            boss.add(Boss())
            s_boss.add(S_Boss(200))
            s_boss.add(S_Boss(1200))
        if boss_hp.now_life<1:
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        pg.display.update()
        tmr += 1
        clock.tick(50)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()