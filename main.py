import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
# using os is so we can dynamically load sprite sheets and images.

#Initialize the window
pygame.init()
pygame.display.set_caption("Platformer")

#All colors will be in RGB

WIDTH, HEIGHT = 1000,800
FPS = 60
PLAYER_VEL = 5

#setup window
window = pygame.display.set_mode((WIDTH, HEIGHT))


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction = False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path,f))] #load every single file in this directory

    all_sprites ={}

    for image in images:    #get images from sprite sheet and load them
        sprite_sheet = pygame.image.load(join(path,image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32) #create surface dimensions of each frame
            #grab from main image
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0,0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png","") + "_right"] = sprites
            all_sprites[image.replace(".png","") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png","")] = sprites

    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size,size), pygame.SRCALPHA, 32)      #size and coordinates will be changed to use other textures
    rect = pygame.Rect(96, 0, size, size) # position from this 96,0 coordinate on terrain image
    surface.blit(image, (0,0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    # Using Sprite method for collision
    COLOR = (255,0,0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters","NinjaFrog",32,32,True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x,y, width, height)
        self.x_vel = 0  #how fast the character is moving in each direction
        self.y_vel = 0  #we'll apply a velocity in a direction and keep the velocity
        self.mask = None
        self.direction = "left"
        self.animation_count = 0 #resets animation frame for each direction
        self.fall_count = 0 #determine velocity increment for gravity
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8 #dont need a down function because gravity is always applied
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count ==1:
            self.fall_count = 0 #stop accumulated gravity for a double jump

    def move(self,dx,dy):
        self.rect.x +=dx
        self.rect.y +=dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        #called every frame and move  character in correct direction
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY) #gravity calculator
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps*2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0 #flag that tirggers reset of gravity counter
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel += -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        if self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites) #update index and pull from frame of animation

        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft = (self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)



    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name = None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0,0))
        self.mask = pygame.mask.from_surface(self.image)

class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__( x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = self.animation_count // self.ANIMATION_DELAY % len(sprites)

        self.image = sprites[sprite_index]
        self.animation_count += 1

        #update for collision
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        #prevent animations from getting too large and causing lag
        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0



def get_background(name):
    #loading the image requires us to run this code from the directory not externally
    image = pygame.image.load(join("assets", "Background", name))
    _,_, width, height = image.get_rect()
    tiles = []

    #loop for loading tiles loop
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height +1):
            pos = (i*width, j*height) #denotes the position of the top left pixel
            tiles.append(pos)

    return tiles, image

#Draw the background
def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)
        #loop through every tile, draw the tile into the screen

    for obj in objects:
        obj.draw(window, offset_x)
    player.draw(window, offset_x)

    pygame.display.update() #every single frame is cleared then updated

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0: #down collision
                player.rect.bottom = obj.rect.top #bottom of character feet touching top of box
                player.landed()
            elif dy < 0: #up collision
                player.rect.top = obj.rect.bottom #hit head
                player.hit_head()

            collided_objects.append(obj)
    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0) #If the character moves to the left or right, will they hit a block?
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj): #if we collide with something...
            collided_object = obj
            break
    #... move them back and return collided object
    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects):
    #check keyboard command collision
    keys = pygame.key.get_pressed()

    player.x_vel = 0 #reset to 0 so instant stop
    #check horizontal collision
    collide_left = collide(player, objects, -PLAYER_VEL * 2) #multiply by two so the sprites have some space before we collide
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()

def main(window):
    #event loop, collision, redraw window etc.
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    block_size = 96

    player = Player(100,100,50,50)
    fire = Fire(100, HEIGHT - block_size -64, 16, 32)
    fire.on()

    floor = [Block(i * block_size, HEIGHT -block_size, block_size) for i in range(-WIDTH // block_size, WIDTH * 2 // block_size)]

    objects = [*floor, Block(0, HEIGHT - block_size *2, block_size), Block(block_size * 3, HEIGHT - block_size * 4, block_size), fire]
    offset_x = 0
    scroll_area_width = 200

    run = True
    while run:
        clock.tick(FPS) #Ensures framerate stays at 60
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        fire.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or ((player.rect.left - offset_x <= scroll_area_width) and player.x_vel <0):
            offset_x += player.x_vel



    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
    #if we don't run this game directrly we wont run the game code