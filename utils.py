import pygame as pp


def scale_image(img, factor):
    size = round(img.get_width() * factor), round(img.get_height() * factor)
    return pp.transform.scale(img, size)


def blit_rotate_center(tela, image, top_left, angulo):
    rotated_image = pp.transform.rotate(image, angulo)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=top_left).center)
    tela.blit(rotated_image, new_rect.topleft)


def distancia(cur_x, init_x, cur_y, init_y):
    distance_x = cur_x - init_x
    distance_y = cur_y - init_y
    distance = (distance_x ** 2 + distance_y ** 2) ** 0.5
    return distance

