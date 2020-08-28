import time
import curses
import asyncio
import random
from fire_animation import fire
from curses_tools import draw_frame, read_controls, get_frame_size
from itertools import cycle
from space_garbage import fly_garbage, obstacles
from physics import update_speed
from obstacles import show_obstacles
from game_scenario import PHRASES, get_garbage_delay_tics

TIC_TIMEOUT = 0.1
POINTS_PER_PRESS = 1
BORDER_WIDTH = 2
NUMBER_OF_STARS = 100

coroutines = []
current_year = 1956

async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, blink_offset_tics, symbol='*'):
    for _ in range(blink_offset_tics):
        await sleep()

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)
        canvas.addstr(row, column, symbol)
        await sleep(3)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)
        canvas.addstr(row, column, symbol)
        await sleep(3)


async def animate_spaceship(canvas, row, column, canvas_height, canvas_width):
    global current_year
    row_speed = column_speed = 0
    with open('animation/rocket_frame_1.txt') as f:
        frame_1 = f.read()
    with open('animation/rocket_frame_2.txt') as f:
        frame_2 = f.read()
    frame_height, frame_width = get_frame_size(frame_1)
    current_y, current_x = row, column
    frame_sequence = [frame_1, frame_1, frame_2, frame_2]
    for frame in cycle(frame_sequence):
        rows_direction, columns_direction, space = read_controls(canvas)
        row_speed, column_speed = update_speed(
            row_speed, column_speed,
            rows_direction, columns_direction
        )
        current_y += (POINTS_PER_PRESS * rows_direction + row_speed)
        current_x += (POINTS_PER_PRESS * columns_direction + column_speed)
        current_y_limited = max(BORDER_WIDTH, min(current_y, canvas_height - frame_height - BORDER_WIDTH))
        current_x_limited = max(BORDER_WIDTH, min(current_x, canvas_width - frame_width - BORDER_WIDTH))
        if space and current_year >= 2020:
            fire_coro = fire(
                canvas, current_y_limited,
                current_x_limited + 2, -0.9
            )
            coroutines.append(fire_coro)
        for obstacle in obstacles:
            if obstacle.has_collision(current_y_limited, current_x_limited):
                coroutines.append(show_gameover(canvas, canvas_height, canvas_width))          
                return
        draw_frame(canvas, current_y_limited, current_x_limited, frame)
        await sleep()
        draw_frame(canvas, current_y_limited, current_x_limited, frame, negative=True)


async def fill_orbit_with_garbage(canvas, canvas_height, canvas_width):
    global current_year
    garbage_frames = [
        'duck.txt', 'hubble.txt',
        'lamp.txt', 'trash_large.txt',
        'trash_small.txt', 'trash_xl.txt'
    ]
    garbage_list = []

    for frame in garbage_frames:
        with open(f'animation/{frame}') as f:
            garbage_list.append(f.read())
    while True:
        garbage_frame_number = random.randint(0, len(garbage_list) - 1)
        garbage_column = random.randint(BORDER_WIDTH, canvas_width - BORDER_WIDTH - 1)
        garbage_delay = get_garbage_delay_tics(current_year)
        if garbage_delay is not None:
            fly_garbage_coro = fly_garbage(canvas, garbage_column, garbage_list[garbage_frame_number])
            coroutines.append(fly_garbage_coro)
            await sleep(garbage_delay)
        await sleep()


async def show_gameover(canvas, canvas_height, canvas_width):
    with open('animation/game_over.txt') as f:
        gameover = f.read()
    frame_height, frame_width = get_frame_size(gameover)
    while True:
        draw_frame(
            canvas,
            (canvas_height - frame_height) / 2,
            (canvas_width - frame_width) / 2,
            gameover
        )
        await sleep()


async def count_years(canvas, canvas_height, canvas_width):
    global current_year
    while True:
        phrase = PHRASES[current_year] if current_year in PHRASES.keys() else ''
        current_label = f'{current_year} {phrase}'
        subcanvas = canvas.derwin(canvas_height - BORDER_WIDTH , canvas_width - len(current_label) - BORDER_WIDTH)
        current_year += 1
        subcanvas.addstr(current_label)
        await sleep(15)
        subcanvas.clear()


def draw(canvas):
    canvas.border()
    canvas.nodelay(True)
    canvas_height, canvas_width = canvas.getmaxyx()  # getmaxyx() returns size of the canvas!
    garbage_coro = fill_orbit_with_garbage(canvas, canvas_height, canvas_width)
    spaceship_coro = animate_spaceship(
        canvas,
        canvas_height/2,
        canvas_width/2,
        canvas_height,
        canvas_width,
    )
    count_years_coro = count_years(canvas, canvas_height, canvas_width)
    coroutines.append(spaceship_coro)
    coroutines.append(garbage_coro)
    coroutines.append(count_years_coro)


    for _ in range(NUMBER_OF_STARS):
        star_symbol = random.choice("+*.:")
        star_loc_y = random.randint(BORDER_WIDTH, canvas_height - BORDER_WIDTH - 1)  # substracting 1 from the size values to calc maximum coordinates of the canvas
        star_loc_x = random.randint(BORDER_WIDTH, canvas_width - BORDER_WIDTH - 1)
        blink_offset = random.randint(0, 20)
        star_coroutine = blink(
            canvas, star_loc_y,
            star_loc_x, blink_offset,
            star_symbol
        )
        coroutines.append(star_coroutine)

    while coroutines:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        curses.curs_set(False)
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
