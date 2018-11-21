"""
# A component of anti hack tools(AHT)
# this script can detect Nospread

script by yuyasato 20170321
"""

from twisted.internet.reactor import callLater,seconds
from pyspades.server import position_data
from commands import alias, admin, add, name, get_team, get_player
from pyspades.common import *
from pyspades.constants import *
from math import sqrt,sin,asin, cos, acos, pi, tan,atan,degrees,radians,hypot,atan2,fabs,floor
from AHT_clientcheck_Y1 import aht_client_send

@alias('nosppt')
@name('nospreadpt')
def nospreadpt(connection, player = None, ayasi=None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
	elif connection in protocol.players:
		player = connection
	else:
		raise ValueError()
	return "%s's nospread suspect point: %s/200, evidence point:%s/100" % (player.name,  player.nosppoint, player.nospevid )
add(nospreadpt)

def aht_nospread_send(suspect):
	return suspect.nosppoint, suspect.nospevid

def apply_script(protocol,connection,config):
	class NospreadConnection(connection):
		nosppoint=0
		nospevid=0

		nospdestroy=0
		SG_nosphit=0
		SGdestroy2=0

		sgfired=0
		lastdestroy=0
		SG_destroy=0
		lastfiretime=0
		sghittype=0

		nosameaim=False
		phi1=0
		theta1=0

		def on_hit(self, hit_amount, hit_player, type, grenade):
			if type <= 1:
				if self.weapon == SHOTGUN_WEAPON and self.tool == WEAPON_TOOL:
					dx = hit_player.world_object.position.x - self.world_object.position.x
					dy = hit_player.world_object.position.y - self.world_object.position.y
					dz = hit_player.world_object.position.z - self.world_object.position.z
					distance = (dx**2.0 + dy**2.0 + dz**2.0)**(1/2.0)

					if self.SG_nosphit==0:
						self.sghittype=type
					if type == self.sghittype:
						self.SG_nosphit+=1
					callLater(0.3, self.sghitreset)

					if self.SG_nosphit>=8:
						self.nospevid+=(distance/10.0)+1
						if distance>25:
							point = ((distance-10)//10)*4
							if distance>60:
								point*=2							
							if point>60:point=60 
							self.nosppoint+=point
				#			print self.name,"nospread kill  pointadd",point	
			return connection.on_hit(self, hit_amount, hit_player, type, grenade)

		def sghitreset(self):
			if self:
				if 0<self.SG_nosphit<8:
					self.nosppoint-=10	
					self.nospevid=0					
					if self.nosppoint<0:self.nosppoint=0
				self.SG_nosphit=0

		def sgdstroyreset(self,point,distance):
			if self:
				if self.SGdestroy2==1:
					if aht_client_send(self):
						self.nospevid+=(distance/10.0)+1
				elif self.SGdestroy2>1:
					self.nospevid=0
				self.SGdestroy2=0	
			
				if self.SG_destroy==1 and point and self.nosameaim:
					if point>60:point=60 
					self.nosppoint+=point
					self.nospdestroy+=1
		#			print self.name,"nospread destroy  pointadd",point	
				elif self.SG_destroy>1:
					self.nosppoint=0						
					if self.nosppoint<0:self.nosppoint=0				
				self.SG_destroy=0			

		def on_block_destroy(self, x, y, z, mode):
			if mode == DESTROY_BLOCK:
				if self.weapon == SHOTGUN_WEAPON and self.tool == WEAPON_TOOL:
					dx = x - self.world_object.position.x
					dy = y - self.world_object.position.y
					dz = z - self.world_object.position.z
					distance = (dx**2.0 + dy**2.0 + dz**2.0)**(1/2.0)
					point = 0
					self.SGdestroy2+=1
					if distance >30:
						self.SG_destroy+=1	
						if self.world_object.cast_ray(810):
							location = self.world_object.cast_ray(810)
							if (x, y, z)==location:
								if dx**2>=dy**2:
									around = 0
									around += self.protocol.map.get_solid(x, y+1, z)
									around += self.protocol.map.get_solid(x, y-1, z)

									around += self.protocol.map.get_solid(x, y+1, z+1)*0.5
									around += self.protocol.map.get_solid(x, y, z+1)
									around += self.protocol.map.get_solid(x, y-1, z+1)*0.5

									around += self.protocol.map.get_solid(x, y+1, z-1)*0.5
									around += self.protocol.map.get_solid(x, y, z-1)
									around += self.protocol.map.get_solid(x, y-1, z-1)*0.5
								else:
									around = 0
									around += self.protocol.map.get_solid(x+1, y, z)
									around += self.protocol.map.get_solid(x-1, y, z)

									around += self.protocol.map.get_solid(x+1, y, z+1)*0.5
									around += self.protocol.map.get_solid(x, y, z+1)
									around += self.protocol.map.get_solid(x-1, y, z+1)*0.5

									around += self.protocol.map.get_solid(x+1, y, z-1)*0.5
									around += self.protocol.map.get_solid(x-1, y, z-1)*0.5
									around += self.protocol.map.get_solid(x, y, z-1)
								if around>4:around=4
								point = ((distance-20)//10)*around
							else:
								self.nosppoint-=1							
					callLater(0.3, self.sgdstroyreset,point,distance)
			return connection.on_block_destroy(self, x, y, z, mode)

		def sgfireloop(self):
			if self.world_object is not None:
				if self.weapon == SHOTGUN_WEAPON and self.tool == WEAPON_TOOL:
					if self.world_object.primary_fire:
						if seconds() - self.lastfiretime > 1.0 and self.weapon_object.current_ammo>0 and not self.world_object.sprint:
							self.lastfiretime = seconds() 
							x,y,z=self.world_object.orientation.get()

							phi= degrees(asin(z))
							theta= degrees(atan2(y,x)) 
							deltaphi = phi - self.phi1
							deltatheta = theta - self.theta1
							if deltatheta>180:deltatheta-=360
							if deltatheta<-180:deltatheta+=360

							self.phi1 = phi
							self.theta1 = theta
							self.nosameaim=False
							lim=3.0
							if not(-lim<deltaphi<lim and -lim<deltatheta<lim):
								self.nosameaim=True
								if self.world_object.cast_ray(810):
									location = self.world_object.cast_ray(810)
									if 0 <= location[0] <=511 and 0 <= location[1] <=511 and 0 <= location[2] <=62:
										dx = location[0] - self.world_object.position.x
										dy = location[1] - self.world_object.position.y
										dz = location[2] - self.world_object.position.z
										distance = (dx**2.0 + dy**2.0 + dz**2.0)**(1/2.0)
										if distance>30:
											if self.nosppoint>0:self.nosppoint-=1
							callLater(1.0, self.sgfireloop)

		def on_shoot_set(self, fire):
			if self.weapon == SHOTGUN_WEAPON and self.tool == WEAPON_TOOL:
				if fire:	
					if seconds() - self.lastfiretime > 1.0 and self.weapon_object.current_ammo>0 and not self.world_object.sprint:
						self.lastfiretime = seconds() 
						x,y,z=self.world_object.orientation.get()

						phi= degrees(asin(z))
						theta= degrees(atan2(y,x)) 
						deltaphi = phi - self.phi1
						deltatheta = theta - self.theta1
						if deltatheta>180:deltatheta-=360
						if deltatheta<-180:deltatheta+=360

						self.phi1 = phi
						self.theta1 = theta

						self.nosameaim=False

						lim=4.0
						if not(-lim<deltaphi<lim and -lim<deltatheta<lim):
							self.nosameaim=True
							if self.world_object.cast_ray(810):
								location = self.world_object.cast_ray(810)
								if 0 <= location[0] <=511 and 0 <= location[1] <=511 and 0 <= location[2] <=62:
									dx = location[0] - self.world_object.position.x
									dy = location[1] - self.world_object.position.y
									dz = location[2] - self.world_object.position.z
									distance = (dx**2.0 + dy**2.0 + dz**2.0)**(1/2.0)
									if distance>30:
										if self.nosppoint>0:self.nosppoint-=1
						callLater(1.0, self.sgfireloop)						
			return connection.on_shoot_set(self, fire)

	return protocol, NospreadConnection

