#!/bin/env python

import curses
import time

from grid import Grid

def print_simulation(stdscr, grid):
	stdscr.clear()
	stdscr.addstr(0, 0, f"cycles = {grid.get_cycles():5d}, total water = {grid.get_total_water():.2f}")
	for cell in grid.cell_iter():
		pos = cell.get_pos()
		stdscr.addstr(4 + pos[1], pos[0] * 20, f"{cell}")
	stdscr.refresh()
		

def main(stdscr):
	curses.noecho()
	curses.cbreak()
	curses.curs_set(0)

	grid = Grid()
	grid.rain(64., 1)
	for i in range(1000):
		grid.tick()
		print_simulation(stdscr, grid)
		time.sleep(0.1)
	stdscr.getkey()
	curses.endwin()



if __name__ == "__main__":
	curses.wrapper(main)
	
	# grid = Grid()
	# grid.rain(64., 1)
	# grid.tick()

