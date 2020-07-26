import time
import curses
import asyncio
import random
from fire_animation import fire
from curses_tools import draw_frame, read_controls, get_frame_size
from itertools import cycle
from space_garbage import fly_garbage

TIC_TIMEOUT = 0.1
POINTS_PER_PRESS = 5
BORDER_WIDTH = 2
NUMBER_OF_STARS = 100

def draw(canvas):
  canvas.border()
  canvas.nodelay(True)
  with open('animation/rocket_frame_1.txt') as f:
    rocket_frame_1 = f.read()
  with open('animation/rocket_frame_2.txt') as f:
    rocket_frame_2 = f.read()
  with open('animation/hubble.txt') as f:
    garbage_frame = f.read()
  canvas_height, canvas_width = canvas.getmaxyx() # getmaxyx() returns size of the canvas!
  fire_coro = fire(canvas, canvas_height/2, canvas_width/2)
  spaceship_coro = animate_spaceship(
    canvas, 
    canvas_height/2, 
    canvas_width/2 - 2,   # substrating 2 is to match the fire shot with the rocket at the first moment 
    canvas_height, 
    canvas_width, 
    rocket_frame_1, 
    rocket_frame_2
  ) 
  garbage_coro = fly_garbage(canvas, 10, garbage_frame)
  coroutines = [fire_coro, spaceship_coro, garbage_coro]
 
  for _ in range(NUMBER_OF_STARS):
    star_symbol = random.choice("+*.:")
    star_loc_y = random.randint(BORDER_WIDTH, canvas_height - BORDER_WIDTH - 1) # substracting 1 from the size values to calc maximum coordinates of the canvas
    star_loc_x = random.randint(BORDER_WIDTH, canvas_width - BORDER_WIDTH - 1)
    blink_offset = random.randint(0, 20)
    star_coroutine = blink(canvas, star_loc_y, star_loc_x, blink_offset, star_symbol)
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


async def blink(canvas, row, column, blink_offset_tics, symbol='*'): 
  for _ in range(blink_offset_tics):
    await asyncio.sleep(0)
    
  while True:  
    canvas.addstr(row, column, symbol, curses.A_DIM)
    for _ in range(20):
      await asyncio.sleep(0)

    canvas.addstr(row, column, symbol)
    for _ in range(3):
      await asyncio.sleep(0)

    canvas.addstr(row, column, symbol, curses.A_BOLD)
    for _ in range(5):
      await asyncio.sleep(0)

    canvas.addstr(row, column, symbol)
    for _ in range(3):
      await asyncio.sleep(0)    


async def animate_spaceship(canvas, row, column, canvas_height, canvas_width, frame_1, frame_2):
  frame_height, frame_width = get_frame_size(frame_1)
  current_y, current_x = row, column
  frame_sequence = [frame_1, frame_1, frame_2, frame_2]
  for frame in cycle(frame_sequence):
    rows_direction, columns_direction, space = read_controls(canvas) 
    current_y += POINTS_PER_PRESS * rows_direction 
    current_x += POINTS_PER_PRESS * columns_direction
    current_y_limited = max(BORDER_WIDTH, min(current_y, canvas_height - frame_height - BORDER_WIDTH))
    current_x_limited = max(BORDER_WIDTH, min(current_x, canvas_width - frame_width - BORDER_WIDTH))
    draw_frame(canvas, current_y_limited, current_x_limited, frame)
    await asyncio.sleep(0)
    draw_frame(canvas, current_y_limited, current_x_limited, frame, negative=True)
    


if __name__ == '__main__':
  curses.update_lines_cols()
  curses.wrapper(draw)
