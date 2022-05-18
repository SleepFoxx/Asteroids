#importy kniznic
import math
import random
from tkinter import CENTER
from turtle import pos

import pyglet
from pyglet import gl
from pyglet.window import key

#konstanty a premenne co budeme pouzivat

#konstanty okna
WIDTH = 1200
HEIGHT = 800

#kontstanty hry
ACCELERATION = 120              #Zrýchlenie rakety
ROTATION_SPEED = 0.05           #Rýchlosť otáčania rakety

game_objects = []
batch = pyglet.graphics.Batch() #ZOZNAM SPRITOV PRE ZJEDNODUŠENÉ VYKRESLENIE
pressed_keyboards = set()       #MNOŽINA ZMAČKNUTÝCH KLÁVES

end_label = "Vyhral si! \n Tu mas trofej :]"
delay_shooting = 0.4
laserlifetime = 45
laserspeed = 200
pewpew = pyglet.media.load("Assetss/pew.wav", streaming=False)
boom = pyglet.media.load("Assetss/boom.wav", streaming=False)

shield_duration = 5
pos_x = 0
pos_y = 0
rotation = 0
#skore counter
lifes = 3
score = 490
shield = False
#funkcie

#vycentrovanie obrazka na stred
def set_anchor_of_image_to_center(img):
    img.anchor_x = img.width // 2
    img.anchor_y = img.height // 2
    

#vykreslenie kolizneho kolecka, budeme neskor odstranovat
def draw_circle(x, y, radius):
    iterations = 20
    s = math.sin(2 * math.pi / iterations)
    c = math.cos(2 * math.pi / iterations)

    dx, dy = radius, 0

    gl.glBegin(gl.GL_LINE_STRIP)
    gl.glColor3f(1, 1, 1)  # nastav barvu kresleni na bilou
    for i in range(iterations + 1):
        gl.glVertex2f(x + dx, y + dy)
        dx, dy = (dx * c - dy * s), (dy * c + dx * s)
    gl.glEnd()


#triedy hry

#hlavna trieda pre vsetky objekty

class SpaceObject:
    "Konštruktor"
    def __init__(self, sprite, x, y, speed_x= 0, speed_y = 0):
        self.x_speed = speed_x
        self.y_speed = speed_y
        self.rotation = 1.57  # radiany -> smeruje hore

        self.sprite = pyglet.sprite.Sprite(sprite, batch=batch)
        self.sprite.x = x
        self.sprite.y = y
        self.radius = (self.sprite.height + self.sprite.width) // 4

    #vypocet vzdialenosti medzi dvoma objektami 
    def distance(self, other):
        x = abs(self.sprite.x - other.sprite.x)
        y = abs(self.sprite.y - other.sprite.y)
        return (x**2 + y**2) ** 0.5 #pytagorova veta

    #kolizia s lodou, definujeme v dalsej triede
    def hit_by_spaceship(self, ship):
        pass

    #kolizia s laserom, definujeme v dalsej triede
    def hit_by_laser(self, laser):
        pass

    #vymazanie objektu
    def delete(self, dt =0 ):
        self.sprite.delete()
        game_objects.remove(self)

    #metoda, ci sa nachadzame na kraji obrazovky 
    def checkBoundaries(self):
        if self.sprite.x > WIDTH:
            self.sprite.x = 0

        if self.sprite.x < 0:
            self.sprite.x = WIDTH

        if self.sprite.y < 0:
            self.sprite.y = HEIGHT

        if self.sprite.y > HEIGHT:
            self.sprite.y = 0

    #metoda tick pre vsetky triedy
    def tick(self, dt):
        #posunutie objektu podla rychlosti
        self.sprite.x += dt * self.x_speed
        self.sprite.y += dt * self.y_speed
        self.sprite.rotation = 90 - math.degrees(self.rotation)
        #kontrola ci sme na kraji
        self.checkBoundaries()

#trieda pre lod, (hrac)
class Spaceship(SpaceObject):

    #konstruktor
    def __init__(self, sprite, x ,y):
        super().__init__(sprite,x,y)
        self.laser_ready = True
        self.shield = False
        #naloadovanie obrazku flamu
        flame_sprite = pyglet.image.load("Assetss/PNG/Effects/fire19.png")
        set_anchor_of_image_to_center(flame_sprite)
        self.flame = pyglet.sprite.Sprite(flame_sprite,batch=batch)
        self.flame.visible = False
    
    #metoda vystrelenia laseru
    def shoot(self):
        img = pyglet.image.load("Assetss/PNG/Lasers/laserBlue04.png")
        set_anchor_of_image_to_center(img)

        laser_x = self.sprite.x + math.cos(self.rotation) * self.radius
        laser_y = self.sprite.y + math.sin(self.rotation) * self.radius

        laser = Laser(img,laser_x,laser_y)
        laser.rotation = self.rotation

        game_objects.append(laser)
        pewpew.play()
    
    #vykona sa metoda tick 60x za sekundu
    def tick(self, dt):
        super().tick(dt)

        #zrychlenie podla konstant pri zmacknuti W
        if 'W' in pressed_keyboards:
            self.x_speed = self.x_speed + dt * ACCELERATION * math.cos(self.rotation)
            self.y_speed = self.y_speed + dt * ACCELERATION * math.sin(self.rotation)

            #flame pozicia a zobrazenie
            self.flame.x = self.sprite.x - math.cos(self.rotation) * self.radius
            self.flame.y = self.sprite.y - math.sin(self.rotation) * self.radius
            self.flame.rotation = self.sprite.rotation
            self.flame.visible = True
        #ak nie je W v pressed_keyboards tak flame neni vidno
        else:
            self.flame.visible = False

        #pri zmacknuti S sa rychlost znizuje
        if 'S' in pressed_keyboards:
            self.x_speed = self.x_speed - dt * ACCELERATION * math.cos(self.rotation)
            self.y_speed = self.y_speed - dt * ACCELERATION * math.sin(self.rotation)

        #otocenie dolava pri zmacknuti A
        if 'A' in pressed_keyboards:
            self.rotation += ROTATION_SPEED

        #otocenie doprava pri zmacknuti D
        if 'D' in pressed_keyboards:
            self.rotation -= ROTATION_SPEED

        #"rucna brzda" pri zmacknuti Shift
        if 'SHIFT' in pressed_keyboards:
            self.x_speed = 0
            self.y_speed = 0

        #vystrelenie laseru pri zmacknuti Space + zapnutie "cooldownu na laser"
        if "SPACE" in pressed_keyboards and self.laser_ready:
            self.shoot()
            self.laser_ready = False
            pyglet.clock.schedule_once(self.reload, delay_shooting)
        if self.shield == True:
            self.get_position()

        #ukoncenie hry pri zmacknutom escape
        if 'ESCAPE' in pressed_keyboards:
            pyglet.app.exit()
        #vyberie vsetky objekty okrem seba
        for obj in [o for o in game_objects if o != self]:
            # d = distance medzi objektami
            d = self.distance(obj)
            if d < self.radius + obj.radius:
                obj.hit_by_spaceship(self)
                break
    #funkcia stitu
    def get_shield(self):
        #nastavenie stitu na True
        self.shield = True
        #nacitanie obrazku
        img = pyglet.image.load("Assetss/PNG/Effects/shield3.png")
        #nastavenie obrazku do stredu
        set_anchor_of_image_to_center(img)
        #definovanie shieldu
        shield = Shield(img,self.sprite.x,self.sprite.y)
        #zapisanie stitu do game objektov
        game_objects.append(shield)
        pyglet.clock.schedule_once(self.shield_off, shield_duration)

    #funkcia vypnutie stitu
    def shield_off(self, dt):
        self.shield = False
    #funckcia pozicie stitu
    def get_position(self):
        global pos_x, pos_y, rotation
        pos_x = self.sprite.x
        pos_y = self.sprite.y
        rotation = self.rotation
        

    #metoda zodpovedna za reset pozicie 
    def reset(self):
        self.sprite.x = WIDTH // 2
        self.sprite.y = HEIGHT // 2
        self.rotation = 1.57  # radiany -> smeruje hore
        self.x_speed = 0
        self.y_speed = 0
    
    def reload(self,dt):
        self.laser_ready = True

class Spaceship2(Spaceship):
    def __init__(self, sprite, x, y):
        #prebera atributy z dedenej classy 
        super().__init__(sprite, x, y)
        #nacitanie fotky flamu
        flame_sprite = pyglet.image.load("Assetss/PNG/Effects/fire19.png")
        #vycentrovanie
        set_anchor_of_image_to_center(flame_sprite)
        #zobrazenie flamu
        self.flame = pyglet.sprite.Sprite(flame_sprite,batch=batch)
        self.flame.visible = False
    
    def shoot(self):
        #nacitanie obrazku
        img = pyglet.image.load("Assetss/PNG/Lasers/laserGreen10.png")
        #vycentrovanie
        set_anchor_of_image_to_center(img)
        #vypocty na laser
        laser_x = self.sprite.x + math.cos(self.rotation) * self.radius
        laser_y = self.sprite.y + math.sin(self.rotation) * self.radius
        #callnutie laseru
        laser = Laser(img,laser_x,laser_y)
        laser.rotation = self.rotation
        #pridanie laseru do game_objects
        game_objects.append(laser)
        #zvuk
        pewpew.play()

    def tick(self, dt):
        #posunutie objektu podla rychlosti
        self.sprite.x += dt * self.x_speed
        self.sprite.y += dt * self.y_speed
        self.sprite.rotation = 90 - math.degrees(self.rotation)
        #kontrola ci sme na kraji
        self.checkBoundaries()
        #zrychlenie podla konstant pri zmacknuti UP (sipky hore)
        if 'UP' in pressed_keyboards:
            self.x_speed = self.x_speed + dt * ACCELERATION * math.cos(self.rotation)
            self.y_speed = self.y_speed + dt * ACCELERATION * math.sin(self.rotation)

            #flame pozicia a zobrazenie
            self.flame.x = self.sprite.x - math.cos(self.rotation) * self.radius
            self.flame.y = self.sprite.y - math.sin(self.rotation) * self.radius
            self.flame.rotation = self.sprite.rotation
            self.flame.visible = True
        #ak nie je UP (sipka hore) v pressed_keyboards tak flame neni vidno
        else:
            self.flame.visible = False

        #pri zmacknuti DOWN (sipka dole) sa rychlost znizuje
        if 'DOWN' in pressed_keyboards:
            self.x_speed = self.x_speed - dt * ACCELERATION * math.cos(self.rotation)
            self.y_speed = self.y_speed - dt * ACCELERATION * math.sin(self.rotation)

        #otocenie dolava pri zmacknuti LEFT (sipka dolava)
        if 'LEFT' in pressed_keyboards:
            self.rotation += ROTATION_SPEED

        #otocenie doprava pri zmacknuti RIGHT (sipka doprava)
        if 'RIGHT' in pressed_keyboards:
            self.rotation -= ROTATION_SPEED

        #"rucna brzda" pri zmacknuti praveho Shift
        if 'RSHIFT' in pressed_keyboards:
            self.x_speed = 0
            self.y_speed = 0

        #vystrelenie laseru pri zmacknuti praveho ctrl + zapnutie "cooldownu na laser"
        if "CTRL" in pressed_keyboards and self.laser_ready:
            self.shoot()
            self.laser_ready = False
            pyglet.clock.schedule_once(self.reload, delay_shooting)
        if self.shield == True:
            self.get_position()

        #zatvorenie hry pri stlaceni escape 
        if 'ESCAPE' in pressed_keyboards:
            pyglet.app.exit()
        #vyberie vsetky objekty okrem seba
        for obj in [o for o in game_objects if o != self]:
            # d = distance medzi objektami
            d = self.distance(obj)
            if d < self.radius + obj.radius:
                obj.hit_by_spaceship(self)
                break
    #definicia dostania stitu, preberame z dedenej triedy
    def get_shield(self):
        super().get_shield()
    #shield off
    def shield_off(self, dt):
        super().shield_off(dt)
    #get position
    def get_position(self):
        super().get_position()
    #reset 
    def reset(self):
        super().reset()
    #reload
    def reload(self, dt):
        super().reload(dt)
    
    

"""
#trieda UFO
class Ufo(Spaceship):
    #metoda pri kolizi lode a ufa
    def hit_by_spaceship(self, ship):
        global score, lifes
        if ship.shield == False:
            pressed_keyboards.clear()
            ship.reset()
            ship.get_shield()
            score -= 50
            lifes -= 1
            if score <= 0:
                score = 0
        self.delete()

    #metoda pri kolizi ufa a laseru
    def hit_by_laser(self, laser):
        global score
        self.delete()
        laser.delete()
        score += 50

    def shoot(self):
        super().shoot()
"""
#trieda Asteroid
class Asteroid(SpaceObject):
    #metoda pri kolizi lode a asteroidu
    def hit_by_spaceship(self, ship):
        global score, lifes
        if ship.shield == False:
            pressed_keyboards.clear()
            ship.reset()
            ship.get_shield()
            score -= 50
            lifes -= 1
            if score <= 0:
                score = 0
        self.delete()

    #metoda pri kolizi asteroidu a laseru
    def hit_by_laser(self, laser):
        global score
        self.delete()
        laser.delete()
        score += 10

#trieda Laser
class Laser(SpaceObject):
    #konstruktor
    def __init__(self, sprite, x ,y):
        super().__init__(sprite,x,y)
        self.laserlifetime = laserlifetime
    #metoda tick preberana z hlavnej triedy + znizenie lifetime
    def tick(self,dt):
        super().tick(dt)
        self.laserlifetime -= 0.5
        if self.laserlifetime == 0:
            self.delete()
        #vypocet rychlosti laseru
        self.y_speed = laserspeed * math.sin(self.rotation)
        self.x_speed = laserspeed * math.cos(self.rotation)
        #vyberie vsetky objekty okrem lode
        for obj in [o for o in game_objects if o != self and o != Spaceship]:
            d = self.distance(obj)
            if d < self.radius + obj.radius:
                obj.hit_by_laser(self)
                break
"""
#trieda Laser2 vyuzivana v UFE
class Laser2(Laser):
    def __init__(self, sprite, x, y):
        super().__init__(sprite, x, y)
    def tick(self, dt):
        super().tick(dt)
        for obj in [o for o in game_objects if o != self]:
            d = self.distance(obj)
            if d < self.radius + obj.radius:
                obj.hit_by_laser(self)
                break
            """
#trieda stit

class Shield(SpaceObject):
    def __init__(self, sprite, x, y):
        super().__init__(sprite, x, y)
        self.shield_duration = shield_duration
    
    def tick(self, dt):
        global pos_x, pos_y
        super().tick(dt)
        self.sprite.x = pos_x
        self.sprite.y = pos_y
        self.shield_duration -= dt
        if self.shield_duration <= 0:
            self.delete()
        



#trieda "hra"
class Game:
    #kontruktor
    def __init__(self):
        global game_objects
        self.window = None
        game_objects = []

    #nacitanie obrazkov hry
    def load_resources(self):
        self.playerShip_image = pyglet.image.load('Assetss/PNG/playerShip1_blue.png')
        self.playerShip2_image = pyglet.image.load('Assetss/PNG/playerShip1_red.png')
        set_anchor_of_image_to_center(self.playerShip_image)
        set_anchor_of_image_to_center(self.playerShip2_image)
        self.background_image = pyglet.image.load('Assetss/Backgrounds/black.png')
        self.endbackground_image = pyglet.image.load('Assetss/Backgrounds/trophy.png')
        self.losebackground_image = pyglet.image.load('end.png')
        """
        self.ufo_images = ['Assetss/PNG/ufoBlue.png',
                            'Assetss/PNG/ufoGreen.png',
                            'Assetss/PNG/ufoRed.png',
                             'Assetss/PNG/ufoYellow.png']
                             """
        self.asteroid_images = ['Assetss/PNG/Meteors/meteorGrey_big1.png',
                           'Assetss/PNG/Meteors/meteorGrey_med1.png',
                           'Assetss/PNG/Meteors/meteorGrey_small1.png',
                           'Assetss/PNG/Meteors/meteorGrey_tiny1.png']

    #vytvorenie objektu hry
    def init_objects(self):
        #Vytvorenie lode
        spaceShip = Spaceship(self.playerShip_image, WIDTH // 3 , HEIGHT//2)
        spaceShip2 = Spaceship2(self.playerShip2_image, WIDTH // 3 * 2, HEIGHT//2)
        game_objects.append(spaceShip)
        game_objects.append(spaceShip2)

        #Nastavenie pozadia a prescalovanie
        self.background = pyglet.sprite.Sprite(self.background_image)
        self.endbackground = pyglet.sprite.Sprite(self.endbackground_image)
        self.losebackground = pyglet.sprite.Sprite(self.losebackground_image)
        self.background.scale_x = 6
        self.background.scale_y = 4

        
        
        #Vytvorenie Meteoritov
        self.create_asteroids(count=7)
        self.create_asteroids(count=(random.randint(1, 5)))
        #Pridavanie novych asteroidoch každych 6 sekund
        pyglet.clock.schedule_interval(self.create_asteroids, 6, 1)
        #pridavanie novych UF kazdych 6 sekund
        #pyglet.clock.schedule_interval(self.create_ufo, 6, 1)
        


    def create_asteroids(self, dt=0, count=1):
        #vytvorenie poctu asteroidov
        for i in range(count):
            # Výber asteroidu náhodne
            img = pyglet.image.load(random.choice(self.asteroid_images))
            set_anchor_of_image_to_center(img)

            # Nastavenie pozície na okraji obrazovky náhodne
            position = [0, 0]
            dimension = [WIDTH, HEIGHT]
            axis = random.choice([0, 1])
            position[axis] = random.uniform(0, dimension[axis])

            # Nastavenie rýchlosti
            tmp_speed_x = random.uniform(-100, 100)
            tmp_speed_y = random.uniform(-100, 100)

            #Temp asteroid object
            asteroid = Asteroid(img, position[0], position[1], tmp_speed_x, tmp_speed_y)
            game_objects.append(asteroid)
    """
    #vytvorenie Ufa
    def create_ufo(self, dt=0, count=1):
    #vytvorenie poctu UF
        for i in range(count):
             #Výber ufa náhodne
            img = pyglet.image.load(random.choice(self.ufo_images))
            set_anchor_of_image_to_center(img)

         #Nastavenie pozície na okraji obrazovky náhodne
        positionn = [0, 0]
        dimensionn = [WIDTH, HEIGHT]
        axiss = random.choice([0, 1])
        positionn[axiss] = random.uniform(0, dimensionn[axiss])

         #Nastavenie rýchlosti
        tmp_speed_xx = random.uniform(-100, 100)
        tmp_speed_yy = random.uniform(-100, 100)

        #Temp ufo object
        UFO = Ufo(img, positionn[0], positionn[1])
        game_objects.append(UFO) 
        """

    
    #definicia zivotov
    def game_lifes(self):
        global lifes
        life = pyglet.image.load("Assetss/PNG/UI/playerLife1_orange.png")
        width = 15
        for i in range(lifes):
            life_sprite = pyglet.sprite.Sprite(life,width,HEIGHT - 40)
            life_sprite.draw()
            width += 35
    


    #metoda ktora sa vola n a "on_draw" stale a vykresluje vsetko v hre
    def draw_game(self):
        global score, scoreLabel, endGame
        # Vymaže aktualny obsah okna
        self.window.clear()
        # Vykreslenie pozadia
        self.background.draw()
        scoreLabel = pyglet.text.Label(text=str(score), font_size=40,x = 1150, y = 760, anchor_x='right', anchor_y='center')
        self.game_lifes()
        if score >= 500:
            endGame = pyglet.text.Label(text= "Vyhral si", font_size = 60, color = (255,0,0,255), x = WIDTH // 2, y = HEIGHT // 2, anchor_x='center', anchor_y='center')
            endGame2 = pyglet.text.Label(text= "Tu mas trofej", font_size = 60, color = (255,0,0,255), x = WIDTH // 2, y = HEIGHT // 2 - 100, anchor_x='center', anchor_y='center')
            game_objects.clear()
            self.window.clear()
            self.endbackground.x = WIDTH // 3
            self.endbackground.y = HEIGHT // 3
            self.endbackground.draw()
            endGame.draw()
            endGame2.draw()
            boom.play()
        elif lifes == 0:
            lose = pyglet.text.Label(text="Prehral si", font_size= 60, color= (0,255,0,255), x = WIDTH // 2, y = HEIGHT // 2, anchor_x = 'center', anchor_y= 'center')
            game_objects.clear()
            self.window.clear()
            self.losebackground.x = WIDTH // 3
            self.losebackground.y = HEIGHT // 3
            self.losebackground.draw()
            lose.draw()
        else:
            scoreLabel.draw()
        
        
        #vykreslenie pomocnych koliecok 
        for o in game_objects:
            draw_circle(o.sprite.x, o.sprite.y, o.radius)

        # Táto časť sa stará o to aby bol prechod cez okraje okna plynulý a nie skokový
        for x_offset in (-self.window.width, 0, self.window.width):
            for y_offset in (-self.window.height, 0, self.window.height):
                # Remember the current state
                gl.glPushMatrix()
                # Move everything drawn from now on by (x_offset, y_offset, 0)
                gl.glTranslatef(x_offset, y_offset, 0)

                # Draw !!! -> Toto vykreslí všetky naše sprites
                batch.draw()

                # Restore remembered state (this cancels the glTranslatef)
                gl.glPopMatrix()

    #spracovanie klavesovych zmacknuti
    def key_press(self, symbol, modifikatory):
        if symbol == key.W:
            pressed_keyboards.add('W')
        if symbol == key.UP:
            pressed_keyboards.add('UP')
        if symbol == key.S:
            pressed_keyboards.add('S')
        if symbol == key.DOWN:
            pressed_keyboards.add('DOWN')
        if symbol == key.A:
            pressed_keyboards.add('A')
        if symbol == key.LEFT:
            pressed_keyboards.add('LEFT')
        if symbol == key.D:
            pressed_keyboards.add('D')
        if symbol == key.RIGHT:
            pressed_keyboards.add('RIGHT')
        if symbol == key.LSHIFT:
            pressed_keyboards.add('SHIFT')
        if symbol == key.RSHIFT:
            pressed_keyboards.add('RSHIFT')
        if symbol == key.SPACE:
            pressed_keyboards.add("SPACE")
        if symbol == key.RCTRL:
            pressed_keyboards.add("CTRL")
        if symbol == key.ESCAPE:
            pressed_keyboards.add("ESCAPE")

    #spracovanie klavesovych "vystupov"
    def key_release(self, symbol, modifikatory):
        if symbol == key.W:
            pressed_keyboards.discard('W')
        if symbol == key.UP:
            pressed_keyboards.discard('UP')
        if symbol == key.S:
            pressed_keyboards.discard('S')
        if symbol == key.DOWN:
            pressed_keyboards.discard('DOWN')
        if symbol == key.A:
            pressed_keyboards.discard('A')
        if symbol == key.LEFT:
            pressed_keyboards.discard('LEFT')
        if symbol == key.D:
            pressed_keyboards.discard('D')
        if symbol == key.RIGHT:
            pressed_keyboards.discard('RIGHT')
        if symbol == key.LSHIFT:
            pressed_keyboards.discard('SHIFT')
        if symbol == key.RSHIFT:
            pressed_keyboards.discard('RSHIFT')
        if symbol == key.SPACE:
            pressed_keyboards.discard("SPACE")
        if symbol == key.RCTRL:
            pressed_keyboards.discard("CTRL")
        if symbol == key.ESCAPE:
            pressed_keyboards.discard("ESCAPE")

    #metoda update
    def update(self, dt):
        for obj in game_objects:
            obj.tick(dt)

    #metoda startu hry
    def start(self):
        #vytvorenie okna hry
        self.window = pyglet.window.Window(width=WIDTH, height=HEIGHT)

        #nastavenie eventov, zaznamenanie klavesovych zmacknuti, "odmacknuti" a callovanie on_draw
        self.window.push_handlers(
            on_draw=self.draw_game,
            on_key_press=self.key_press,
            on_key_release=self.key_release
        )

        #load resources 
        self.load_resources()

        #inicializacia objektov
        self.init_objects()

        #nastavenie timeru na 1/60 sekundy, 
        pyglet.clock.schedule_interval(self.update, 1. / 60)

        pyglet.app.run()  #vsetko je hotove, runnujeme hru

#zaciatok hry
Game().start()