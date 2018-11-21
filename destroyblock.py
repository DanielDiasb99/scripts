"""
# A component of anti hack tools(AHT)
# this script can detect rapid destroy and spade hack, rapid build hack

script by yuyasato 2017
"""
from pyspades.constants import *
from twisted.internet.reactor import callLater, seconds
from pyspades.server import position_data
from math import sqrt,sin,asin, cos, acos, pi, tan,atan,degrees,radians,hypot,atan2,floor
from collections import deque
from commands import alias, admin, add, name, get_team, get_player
from AHT_clientcheck_Y1 import aht_client_send

RAPID_ALLOW = False

@alias('dbpt')
@name('destroyblockpt')
def destroyblockpt(connection, player = None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
	elif connection in protocol.players:
		player = connection
	else:
		raise ValueError()
	return "%s's destroy block hack point %s/30,  suspicious %s, bigspade %s/30" % (player.name, player.destroy_hack_points, player.destroy_suspicious_points,player.bigspade)
add(destroyblockpt)

def aht_destroyblock_send(suspect):
	return suspect.destroy_hack_points, suspect.destroy_suspicious_points,suspect.bigspade, suspect.build_hack_points

def apply_script(protocol,connection,config):
	class DestroyblockConnection(connection):
		firetime=0
		destroytime=0
		lastfiretime=0
		last_build=0
		right_spade_destroy=0
		left_spade_destroy=0

		forbidden_destroying=False
		firstshot=False
		destroy_smg = deque([10,9,8,7,6,5,4,3,2,1,0])
		destroy_rifle = deque([5,4,3,2,1,0])
		destroy_hack_points=0
		destroy_suspicious_points=0
		bigspade=0
		build_hack_points=0
		rapidbuild=0
		onetime = False

		def on_spawn(self,pos):
			self.rapid_hack_detect = False
			return connection.on_spawn(self,pos)

		def _on_reload(self):
			self.lastreloadtime=seconds()
			return connection._on_reload(self)

		def on_block_build(self, x, y, z):
			if seconds() - self.last_build < 0.23:
				self.build_hack_points+=2
				if self.build_hack_points>2:
			#		print "rapidbuild",self.name,seconds() - self.last_build
					pass
			elif 0.49 < seconds() - self.last_build:
				if self.build_hack_points>0:
					self.build_hack_points-=1
			self.last_build=seconds()
			return connection.on_block_build(self, x, y, z)

		def on_block_destroy(self, x, y, z, mode):
			if mode == SPADE_DESTROY:
				if self.world_object.primary_fire:
					if not self.world_object.secondary_fire:
			#			print "!!!!bigspadehack00!!!!",self.name
						self.bigspade+=30
					else:
						if aht_client_send(self):
			#				print "???bigspadehack1???",self.name
							self.bigspade+=10

				else:
					if not self.world_object.secondary_fire:
			#			print "???bigspade2???",self.name
						self.bigspade+=10
					else:
						if self.bigspade>0:self.bigspade-=1				
				dt = seconds()-self.right_spade_destroy
				if dt<0.7:
					self.destroy_hack_points+=1
				self.right_spade_destroy = seconds()
			if self.tool==SPADE_TOOL and mode != SPADE_DESTROY and mode != GRENADE_DESTROY:
				if self.bigspade>0:self.bigspade-=1	
				dt = seconds()-self.left_spade_destroy
				if dt<0.15:
					self.destroy_hack_points+=1
				self.left_spade_destroy = seconds()

			if not RAPID_ALLOW:
				if mode != GRENADE_DESTROY and mode != SPADE_DESTROY and self.tool==WEAPON_TOOL:
					if self.weapon != SHOTGUN_WEAPON:
						lastdestroytime = self.destroytime
						newdestroytime = seconds()
						self.destroytime = newdestroytime 
						if self.weapon == SMG_WEAPON:
							first_forbidden_time = 0.18
						elif self.weapon == RIFLE_WEAPON:
							first_forbidden_time = 0.7
						if newdestroytime-lastdestroytime<first_forbidden_time:
							if not self.onetime:
								self.onetime = True
							else:
								if self.weapon == SMG_WEAPON:
									self.destroy_suspicious_points+=3
								elif self.weapon == RIFLE_WEAPON:
									self.destroy_suspicious_points+=10
						else:
							if self.destroy_suspicious_points>0:self.destroy_suspicious_points-=1
							self.onetime = False

						if newdestroytime-self.lastfiretime>12 and aht_client_send(self):	
							if self.weapon == SMG_WEAPON:
								first_forbidden_time = 0.18
								olddestroytime=self.destroy_smg.popleft()	
								if newdestroytime-olddestroytime < 4:
									self.destroy_hack_points+=1	
								self.destroy_smg.append(newdestroytime)
							elif self.weapon == RIFLE_WEAPON:
								first_forbidden_time = 0.35
								olddestroytime=self.destroy_rifle.popleft()	
								if newdestroytime-olddestroytime < 6:
									self.destroy_hack_points+=1
								self.destroy_rifle.append(newdestroytime)

							if self.forbidden_destroying:
								if newdestroytime-lastdestroytime<first_forbidden_time*2:
									self.destroy_hack_points+=1	
								else:
									self.forbidden_destroying=False
							if self.firstshot and newdestroytime-self.firetime < first_forbidden_time:
								self.forbidden_destroying=True
								self.destroy_hack_points+=1	
			return connection.on_block_destroy(self, x, y, z, mode)

		def on_shoot_set(self, fire):
			if not fire:
				self.lastfiretime=seconds()
			else:
				if self.tool==WEAPON_TOOL:
					self.firetime = seconds()					
					if self.firetime-self.lastfiretime > 12:
						self.firstshot=True
					else:
						self.firstshot=False
			return connection.on_shoot_set(self, fire)

	return protocol, DestroyblockConnection

