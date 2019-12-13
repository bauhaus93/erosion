#!/bin/env python

import curses
import random
import time

DIR_UP = 0
DIR_DOWN = 1
DIR_LEFT = 2
DIR_RIGHT = 3


GRAVITY = 1.
PIPE_LENGTH = 1.
PIPE_AREA = PIPE_LENGTH ** 2
TIME_DELTA = 0.1
POINT_DISTANCE = (1., 1.)
SEDIMENT_CAPACITY_CONSTANT = 30.
SEDIMENT_DISSOLVING_CONSTANT = 0.0012
SEDIMENT_DEPOSITION_CONSTANT = 0.0012
EVAPORATION_CONSTANT = 0.0

def cross(a, b):
    return [ a[1] * b[2] - a[2] * b[1],
	         a[2] * b[0] - a[0] * b[2],
			 a[0] * b[1] - a[1] * b[0]]

def dot(a, b):
	return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

def get_opposite_dir(direction):
	if direction == 0:
		return 1
	elif direction == 1:
		return 0
	elif direction == 2:
		return 3
	elif direction == 3:
		return 2

class Cell:

	def __init__(self, pos):
		self.pos = pos
		self.water = 0.
		self.height = 0.
		self.flow = [0., 0., 0., 0.]
		self.velocity = (0., 0)
		self.transport_capacity = 0.
		self.normal = [0., 0., 1.]
		self.suspended_sediment = 0.
		self.deposited_sediment = 0.

	def get_pos(self):
		return self.pos

	def get_terrain_height(self):
		return self.height

	def get_water_height(self):
		return self.water

	def get_total_height(self):
		return self.height + self.water

	def get_flow(self, direction):
		return self.flow[direction]
	
	def get_velocity(self):
		return self.velocity

	def get_normal(self):
		return self.normal

	def get_tilt(self):
		return 1. - dot(self.normal, [0., 0., 1.])
	
	def get_transport_capacity(self):
		return self.transport_capacity

	def get_suspended_sediment(self):
		return self.suspended_sediment
	
	def get_deposited_sediment(self):
		return self.deposited_sediment

	def mod_water(self, amount):
		self.water += amount
		if self.water < 0.:
			self.water = 0.
	
	def mod_height(self, amount):
		self.height += amount
	
	def set_flow(self, direction, flow):
		self.flow[direction] = flow
	
	def set_velocity(self, velocity):
		self.velocity = velocity

	def set_normal(self, normal):
		self.normal = normal

	def set_transport_capacity(self, capacity):
		self.transport_capacity = capacity

	def set_suspended_sediment(self, sediment):
		self.suspended_sediment = sediment
	
	def set_deposited_sediment(self, sediment):
		self.deposited_sediment = sediment

	def __str__(self):
		return f"h = {self.height:5.2f}\tw = {self.water:5.2f}\tp = {self.pressure}"

class Grid:

	def __init__(self, size = (8, 8)):
		self.size = size
		self.cycles = 0
		self.grid = dict()
		for pos in self.index_iter():
			self.grid[pos] = Cell(pos)
	
	def get_total_water(self):
		return sum(c.get_water_height() for c in self.cell_iter())

	def get_cycles(self):
		return self.cycles

	def place_water(self, amount):
		self.grid[(random.randint(0, self.size[0] - 1),
				   random.randint(0, self.size[1] - 1))].mod_water(amount)
	
	def rain(self, total_water, drop_count):
		for _ in range(drop_count):
			self.place_water(total_water / drop_count)

	def index_iter(self):
		for y in range(0, self.size[1]):
			for x in range(0, self.size[0]):
				yield (x, y)
	
	def cell_iter(self, watered = False):
		for pos in self.index_iter():
			cell = self.grid[pos]
			if (watered and cell.get_water_height() > 0) or not watered:
				yield cell
	
	def cell_dir_iter(self):
		for cell in self.cell_iter():
			for i in range(0, 4):
				yield (i, cell)
	
	def neighbour_iter(self, cell):
		for i in range(4):
			yield (i, self.get_neighbour(cell, i))

	def get_neighbour(self, cell, direction):
		pos = cell.get_pos()
		if direction == DIR_UP:
			nb_pos = (pos[0], pos[1] - 1)
		elif direction == 1:
			nb_pos = (pos[0], pos[1] + 1)
		elif direction == 2:
			nb_pos = (pos[0] - 1, pos[1])
		elif direction == 3:
			nb_pos = (pos[0] + 1, pos[1])
		if nb_pos in self.grid:
			return self.grid[nb_pos]
		else:
			return None

	def simulate(self, count):
		for _ in range(count):
			self.tick()

	def tick(self):
		self.cycles += 1
		self.update_flow()
		self.apply_flow()
		self.update_velocity()
		self.update_transport_capacity()
		self.apply_erosion_deposition()

		self.apply_water_evaporation()

	def update_flow(self):
		for cell in self.cell_iter(watered = True):
			new_flow = [0., 0., 0., 0.]
			for direction in range(0, 4):
				nb = self.get_neighbour(cell, direction)
				if nb:
					height_diff = cell.get_total_height() - nb.get_total_height()
					delta_flow = TIME_DELTA * PIPE_AREA * (GRAVITY * height_diff / PIPE_LENGTH)
					flow = cell.get_flow(direction) + delta_flow
					new_flow[direction] = max(0., flow)

			flow_sum = sum(new_flow)
			if flow_sum > 0.:
				k = min(1., (cell.get_water_height() * POINT_DISTANCE[0] * POINT_DISTANCE[1]) / (flow_sum * TIME_DELTA)) 
			else:
				k = 0.
			for direction in range(0, 4):
				cell.set_flow(direction, new_flow[direction] * k)


	def apply_flow(self):
		for cell in self.cell_iter():
			delta_water = 0.
			for (direction, nb) in self.neighbour_iter(cell):
				opposite_dir = get_opposite_dir(direction)
				if nb:
					delta_water += nb.get_flow(opposite_dir) - cell.get_flow(direction)
			delta_water *= (TIME_DELTA * PIPE_LENGTH)
			cell.mod_water(delta_water)
	
	def update_velocity(self):
		for cell in self.cell_iter():
			nb_up = self.get_neighbour(cell, DIR_UP)
			nb_down = self.get_neighbour(cell, DIR_DOWN)
			nb_left = self.get_neighbour(cell, DIR_LEFT)
			nb_right = self.get_neighbour(cell, DIR_RIGHT)
			if nb_left:
				f_lr = nb_left.get_flow(DIR_RIGHT) - cell.get_flow(DIR_LEFT)
			else:
				f_lr = 0.
			if nb_right:
				f_rl = cell.get_flow(DIR_RIGHT) - nb_right.get_flow(DIR_LEFT)
			else:
				f_rl = 0.

			if nb_up:
				f_ud = nb_up.get_flow(DIR_DOWN) - cell.get_flow(DIR_UP)
			else:
				f_ud = 0.

			if nb_down:
				f_du = cell.get_flow(DIR_DOWN) - nb_down.get_flow(DIR_UP)
			else:
				f_du = 0.

			vel_x = (f_lr - f_rl) / 2.
			vel_y = (f_ud - f_du) / 2.
			cell.set_velocity((vel_x, vel_y))

	def calculate_normal(self, cell):

		nb_up = self.get_neighbour(cell, DIR_UP)
		if nb_up:
			up_height = nb_up.get_total_height()
		else:
			up_height = cell.get_total_height()

		nb_down = self.get_neighbour(cell, DIR_DOWN)
		if nb_down:
			down_height = nb_down.get_total_height()
		else:
			down_height = cell.get_total_height()

		nb_left = self.get_neighbour(cell, DIR_LEFT)
		if nb_left:
			left_height = nb_left.get_total_height()
		else:
			left_height = cell.get_total_height()

		nb_right = self.get_neighbour(cell, DIR_RIGHT)
		if nb_right:
			right_height = nb_right.get_total_height()
		else:
			right_height = cell.get_total_height()

		slope_x = left_height - right_height
		slope_y = up_height - down_height
		v = [slope_x, slope_y, 2.]
		v_len = (v[0]**2 + v[1]**2 + v[2]**2)**0.5
		return [e / v_len for e in v]

	def update_transport_capacity(self):
		for cell in self.cell_iter():
			vel = cell.get_velocity()
			speed = (vel[0]**2 + vel[1]**2)**0.5
			cell.set_normal(self.calculate_normal(cell))
			tilt = max(0.1, cell.get_tilt())
			capacity = SEDIMENT_CAPACITY_CONSTANT * speed * tilt
			cell.set_transport_capacity(capacity)

	def apply_erosion_deposition(self):
		for cell in self.cell_iter():
			trans_cap = cell.get_transport_capacity()
			suspended = cell.get_suspended_sediment()
			deposited = cell.get_deposited_sediment()
			if trans_cap > suspended:
				dissolved_sediment = SEDIMENT_DISSOLVING_CONSTANT * (trans_cap - suspended)
				cell.mod_height(-dissolved_sediment)
				cell.set_suspended_sediment(suspended + dissolved_sediment)
			else:
				deposited_sediment = SEDIMENT_DEPOSITION_CONSTANT * (trans_cap - deposited)
				cell.mod_height(deposited_sediment)
				cell.set_deposited_sediment(deposited + deposited_sediment)

	def apply_water_evaporation(self):
		for cell in self.cell_iter(watered = True):
			evap_amount = cell.get_water_height() * EVAPORATION_CONSTANT * TIME_DELTA
			cell.mod_water(-evap_amount)



	def __str__(self):
		out = ""
		for cell in self.cell_iter():
			out += str(cell) + "\n"
		return out


def print_simulation(stdscr, grid):
	stdscr.clear()
	stdscr.addstr(0, 0, f"cycles = {grid.get_cycles():5d}, total water = {grid.get_total_water():.2f}")
	for cell in grid.cell_iter():
		pos = cell.get_pos()
		stdscr.addstr(4 + pos[1], pos[0] * 20, f"{cell.get_water_height():5.2f}")
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

