import math
import random
import sys
import time
import pygame as pg


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ


def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj：オブジェクト（爆弾，こうかとん，ビーム）SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right:  # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"ex05/fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        # self.imgs = {
        #     (+1, 0): img,  # 右
        #     (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
        #     (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
        #     (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
        #     (-1, 0): img0,  # 左
        #     (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
        #     (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
        #     (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        # }
        self.dire = (+1, 0)
        self.image = pg.transform.rotozoom(img, 90, 1.0)
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state="nomal"
        self.hyper_life=-1

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
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
            self.image=pg.transform.laplacian(self.image)
        if self.hyper_life < 0:
            self.change_state("nomal",-1)
        screen.blit(self.image, self.rect)

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

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
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

class BossBomb(pg.sprite.Sprite):
    colors = [(255, 0, 255), (1, 0, 0), (1, 0, 0), (1, 0, 0), (255, 0, 255), (0, 0, 1)]
    def __init__(self, emy: "Enemy", bird: Bird):
        """
        ここではボスの攻撃を作る
        ボスの爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のプレイヤー　ここは今後名前を変える。
        """
        super().__init__()
        rad = random.randint(100, 150)  # 爆弾円の半径：50以上100以下の乱数
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
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
    def __init__(self, emy: "Enemy", bird: Bird):
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
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
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
    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = (0,-1) # bird.get_direction()
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"ex04/fig/beam.png"), angle, 2.0) 
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))    
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
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
    def __init__(self, bird: Bird, x:int):
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
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
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
    imgs = pg.image.load(f"ex05/fig/3.png") #飛んでるこうかとんの画像読み込み
    imgs2 = pg.transform.flip(imgs, True, False) #反転したこうかとん

    def __init__(self):
        super().__init__()
        self.image = self.imgs
        self.image2 = self.imgs2
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +10
        self.bound = random.randint(50, 550)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

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
        
        if WIDTH/2 > self.rect[0]:
            self.image = self.image2 #画面の左半分だったらこうかとんの画像を反転する


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
        self.rect.center = 100, HEIGHT-850

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
    boss_attack = False
    pg.display.set_caption("こうかとんを打ち落とせ")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("ex05/fig/pg_bg.jpg")
    score = Score()
    beam_status = Beam_status()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    boss_bombs=pg.sprite.Group()
    small_bombs=pg.sprite.Group()
    beams = pg.sprite.Group()
    charge_beam = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    boss = pg.sprite.Group()
    s_boss = pg.sprite.Group()

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
                    beams.add(Beam(bird))
                else:
                    charge_beam.add(Charge_Beam(bird,x))
                    x = 0
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                x += 1
                

            if event.type == pg.KEYDOWN and event.key == pg.K_LSHIFT:
                bird.speed = 20
            if event.type == pg.KEYUP and event.key == pg.K_LSHIFT:
                bird.speed = 10

        screen.blit(bg_img, [0, 0])


        if not boss_attack:
            if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
                emys.add(Enemy())

            for emy in emys:
                if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                    bombs.add(Bomb(emy, bird))

        if boss_attack:
             for bos in boss:
                if tmr%emy.interval == 0:
                  bombs.add(BossBomb(bos, bird))
            
             for sbos in s_boss:
                 if tmr%emy.interval == 0:
                  bombs.add(SmallBossBomb(sbos, bird))
                 
  

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.score_up(10)  # 10点アップ
            
        # チャージビームの判定
        for emy in pg.sprite.groupcollide(emys, charge_beam, True, False).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.score_up(10)  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(boss_bombs, beams, False, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, False, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        # チャージビームの判定   
        for bomb in pg.sprite.groupcollide(bombs, charge_beam, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        for bomb in pg.sprite.groupcollide(boss_bombs, beams, False, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, False, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        for bo in pg.sprite.groupcollide(boss, beams, False, True).keys():
            exps.add(Explosion(bo, 50))  # 爆発エフェクト
            boss_hp.now_life -=1

        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            if bird.state=="hyper":
                exps.add(Explosion(bomb, 50))
                score.score_up(1)
            if bird.state=="nomal":
                bird.change_img(8, screen) # こうかとん悲しみエフェクト
                score.font = pg.font.Font(None, 250)
                score.rect.center = WIDTH/2-250, HEIGHT/2 #スコアをやられた際に真ん中に表示
                score.update(screen)
                font = pg.font.Font(None, 250)
                color = (0, 0, 255)
                image3 = font.render(f"Game Over", 0, color)
                image3.update(screen)
                pg.display.update()
                time.sleep(2)
                return

        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
            bird.change_img(8, screen) # こうかとん悲しみエフェクト


            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        
        if len(pg.sprite.spritecollide(bird,boss_bombs,True)) !=0:#ボス用こうかとんの当たり判定
            bird.change_img(8, screen) # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        
        if len(pg.sprite.spritecollide(bird,small_bombs,True)) !=0:#小ボス用こうかとんの当たり判定
            bird.change_img(8, screen) # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        if boss_attack:
            boss_hp.update(screen)
            boss.draw(screen)
            s_boss.update()
            s_boss.draw(screen)
            if boss_hp.now_life==0:
                boss_attack = False
        else:
            emys.update()
            emys.draw(screen)
        bird.update(key_lst, screen)
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
            boss_hp = Boss_HP(150)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
