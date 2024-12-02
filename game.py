# Example file showing a circle moving on screen
from typing import List, Tuple
import pygame
from enum import Enum
from pygame.rect import Rect
import json

GREEN = (0, 255, 0)
RED = (255, 0, 0)

class Mode(Enum):
    EDITOR_CREATE_RECTS = 1
    EDITOR_SELECT_RECTS = 2
    LEVEL = 3

class Selectable(Rect):
    score = 1

def resize_img(image: pygame.Surface, target_size: Tuple[int, int]):
    img_size = image.get_size()
    diff = target_size[0] / img_size[0], target_size[1] / img_size[1],
    if abs(diff[0]) < abs(diff[1]):
        return pygame.transform.smoothscale_by(image, target_size[0] / img_size[0])
    else:
        return pygame.transform.smoothscale_by(image, target_size[1] / img_size[1])

def corners_to_rect(corner1: Tuple[int, int], corner2: Tuple[int, int]): 
    width, height = abs(corner1[0] - corner2[0]), abs(corner1[1] - corner2[1])
    start_x, start_y = min(corner1[0], corner2[0]), min(corner1[1], corner2[1])
    return Rect(start_x, start_y, width, height)


def scale_to_10000(target_rect: Rect, reference: Rect):
    scale_x = 10000.0 / reference.size[0]
    scale_y = 10000.0 / reference.size[1]

    left = target_rect.left * scale_x
    top = target_rect.top * scale_y
    width = target_rect.width * scale_x
    height = target_rect.height * scale_y
    return Selectable(round(left), round(top), round(width), round(height))

def unscale_from_10000(target_rect: Rect, reference: Rect):
    scale_x = reference.size[0] / 10000.0 
    scale_y = reference.size[1] / 10000.0 

    left = target_rect.left * scale_x
    top = target_rect.top * scale_y
    width = target_rect.width * scale_x
    height = target_rect.height * scale_y
    return Rect(round(left), round(top), round(width), round(height))

def clear_mode_temps():
    global new_rectangle, selected_rect
    new_rectangle = 0
    selected_rect = -1


def decode_selectable(dct):
    if '__Selectable__' in dct:
        selectable = Selectable(dct["topleft"], dct["size"])
        selectable.score = dct["score"]
        return selectable


def encode_selectable(obj):
    if isinstance(obj, Selectable):
        return {"size": obj.size, "topleft": obj.topleft, "score": obj.score}
    raise TypeError(f'Object of type {obj.__class__.__name__} '
                    f'is not JSON serializable')

def encode_complex(obj):
    if isinstance(obj, complex):
        return [obj.real, obj.imag]

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
running = True
editor_mode = False

background_img = pygame.image.load("res/bg.jpg").convert()
background = resize_img(background_img, screen.get_size())
mode = Mode.EDITOR_CREATE_RECTS

selected_rect = -1
rect_start = (0, 0)
new_rectangle = False

rects: List[Selectable] = []
font = pygame.font.Font('freesansbold.ttf', 20)
clock = pygame.time.Clock()

score = 0


while running:
    mouse_pos = pygame.mouse.get_pos();
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.VIDEORESIZE:
            background = resize_img(background_img, screen.get_size())
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                editor_mode = False
            if event.key == pygame.K_1:
                mode = Mode.EDITOR_CREATE_RECTS
                clear_mode_temps()
            if event.key == pygame.K_2:
                mode = Mode.EDITOR_SELECT_RECTS
                clear_mode_temps()
            if event.key == pygame.K_3:
                mode = Mode.LEVEL
                clear_mode_temps()
        if mode == Mode.EDITOR_CREATE_RECTS:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if new_rectangle:
                        rects.append(
                            scale_to_10000(
                                corners_to_rect(rect_start, mouse_pos), background.get_rect()
                            )
                        )
                    rect_start = mouse_pos
                    new_rectangle = not new_rectangle
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    new_rectangle = 0
        elif mode == Mode.EDITOR_SELECT_RECTS:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for (idx, rect) in enumerate(rects):
                        rect = unscale_from_10000(rect, background.get_rect())
                        if rect.collidepoint(mouse_pos):
                            selected_rect = idx
                            break;
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    selected_rect = -1
                if event.key == pygame.K_s:
                    file = open("level1_zones.json", "w")
                    json.dump(rects, file)
                if event.key == pygame.K_DELETE:
                    if selected_rect != -1:
                        rects.pop(selected_rect)
                        selected_rect = -1
                if event.key == pygame.K_SPACE:
                    if selected_rect != -1:
                        rects[selected_rect].score *= -1
                        selected_rect = -1
        elif mode == Mode.LEVEL:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    hit = -1
                    for (idx, rect) in enumerate(rects):
                        rect = unscale_from_10000(rect, background.get_rect())
                        if rect.collidepoint(mouse_pos):
                            hit = idx
                            break;
                    if hit != -1:
                        rect = rects.pop(hit)
                        score += rect.score
    screen.fill("purple")
    screen.blit(background, (0, 0))
    if mode != Mode.LEVEL:
        for (idx, selectable) in enumerate(rects):
            rect = unscale_from_10000(selectable, background.get_rect())
            s = pygame.Surface(rect.size)
            if idx == selected_rect:
                s.fill((120, 120, 120))
            elif selectable.score == 1:
                s.fill(GREEN)
            elif selectable.score == -1:
                s.fill(RED)
            screen.blit(s, rect.topleft)
    if new_rectangle:
        rect = corners_to_rect(rect_start, mouse_pos)
        s = pygame.Surface(rect.size)
        s.fill((100, 0, 0))
        screen.blit(s, rect.topleft)

    text = font.render(str(mode), True, GREEN)
    screen.blit(text, (0, 0))

    text = font.render(str(score), True, GREEN)
    text_rect = text.get_rect()
    text_rect.right = screen.get_width()
    screen.blit(text, text_rect)

    pygame.display.flip()
    clock.tick(60)
pygame.quit()
