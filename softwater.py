"""
# A component of anti hack tools(AHT)
# this script can detect moving impossible speed in water.

 by yuyasato
"""

from pyspades.constants import *
from pyspades.constants import UPDATE_FREQUENCY
from twisted.internet.reactor import callLater,seconds
from pyspades.server import position_data
from math import sqrt,sin,asin, cos, acos, pi, tan,atan,degrees,radians,hypot,atan2,fabs,floor
from commands import admin, add, name, get_team, get_player,alias


sprint_water_velocity  = 8.5
normal_water_velocity  = 7.0
crouch_water_velocity  = 2.2
sneak_water_velocity = 3.6

sprint_velocity  = 13.0
normal_velocity  = 10.0
crouch_velocity  = 3.5
sneak_velocity = 4.5

@alias('swpt')
@name('softwaterpt')
def softwaterpt(connection, player = None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
	elif connection in protocol.players:
		player = connection
	else:
		raise ValueError()
	player.swpointsshow()
	return "%s's softwater point is %s/100" % (player.name, player.swkickpoints)
add(softwaterpt)

def aht_send_softwater(suspect):
	sw = suspect.softwater_count
	nw = suspect.normalwater_count
	sw_points = suspect.swkickpoints
	return sw, nw, sw_points

def apply_script(protocol,connection,config):
	class SoftwaterConnection(connection):
		speed_loop_running=False

		walking = False
		crouching = False
		sprinting = False
		sneaking = False

		change_time = 0
		spawn_waiting=False
		discon = False

		softwater_count = 0 
		normalwater_count = 0 
		swkickpoints=0
		
		def swpointsshow(self):
			print
			print self.name
			print "soft", self.softwater_count,"   normal",	 self.normalwater_count	, "softwaterpoint", self.swkickpoints,"/60"

		def speedcheck(self,pre_x,pre_y, pre_z):
			if self.speed_loop_running and self in self.protocol.players and (self.team == self.protocol.green_team or self.team == self.protocol.blue_team):
				now_x, now_y, now_z = self.world_object.position.get()
				if not self.walking or fabs(self.world_object.velocity.z)>0.0001:
					self.change_time = seconds()
				if seconds()-self.change_time >2:
					delta_x = now_x - pre_x
					delta_y	= now_y - pre_y
					vel = hypot(delta_x, delta_y)	# blk/sec
					if 61 < now_z < 63:
						if self.sprinting:
							velocity_max = sprint_water_velocity
						elif self.crouching:
							velocity_max = crouch_water_velocity 
						elif self.sneaking:
							velocity_max = sneak_water_velocity
						else:
					 		velocity_max = normal_water_velocity 
						if vel > velocity_max:
					#		print self.name,"!!!softwater!!!",vel,velocity_max
							self.softwater_count += 1 
							self.swkickpoints+=10
						else:
							self.normalwater_count += 1 
							if self.swkickpoints>0:
								self.swkickpoints-=1
					"""
					else:
						if self.sprinting:
							velocity_max = sprint_velocity
						elif self.crouching:
							velocity_max = crouch_velocity 
						elif self.sneaking:
							velocity_max = sneak_velocity
						else:
					 		velocity_max = normal_velocity 	
						if vel > velocity_max:
							print self.name,"!!!speed hack!!!",vel,velocity_max
					"""
				callLater(1.0,self.speedcheck, now_x, now_y, now_z )

		def on_secondary_fire_set(self, secondary):
			self.change_time = seconds()
			return connection.on_secondary_fire_set(self, secondary)

		def on_walk_update(self, up, down, left, right):
			self.walking = up or down or left or right
			self.change_time = seconds()
			return connection.on_walk_update(self, up, down, left, right)

		def on_animation_update(self, jump, crouch, sneak, sprint):
			self.sprinting = sprint
			self.sneaking = sneak
			self.crouching = crouch
			self.change_time = seconds()
			return connection.on_animation_update(self, jump, crouch, sneak, sprint)

		def on_spawn(self,pos):
			self.sw_reset()
			self.discon = False
			if not self.spawn_waiting:callLater(3.0,self.speed_loop_init)
			self.spawn_waiting=True
			return connection.on_spawn(self,pos)
	
		def speed_loop_init(self):
			if not self.discon:
				self.speed_loop_running=True
				self.spawn_waiting=False
				if self in self.protocol.players and (self.team == self.protocol.green_team or self.team == self.protocol.blue_team):
					x, y, z = self.world_object.position.get()
					callLater(1.0,self.speedcheck, x, y, z)

		def sw_reset(self):
			self.walking = False
			self.crouching = False
			self.sprinting = False
			self.sneaking = False
			self.speed_loop_running=False

		def on_reset(self):
			self.sw_reset()
			self.discon = True
			return connection.on_reset(self)

	return protocol, SoftwaterConnection

