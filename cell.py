import numpy as np

UP_VECTOR = np.array([0., 0., 1.])

class Cell:

	def __init__(self, pos):
		self.pos = np.array(pos)
		self.water = 0.
		self.height = 0.
		self.flow = np.zeros(4)
		self.velocity = np.zeros(2)
		self.transport_capacity = 0.
		self.normal = UP_VECTOR
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
		return 1. - np.dot(self.normal, UP_VECTOR)
	
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
		return f"{self.height:5.2f}/{self.water:5.2f}"
