"""
# A component of anti hack tools(AHT)
# this script can detect Norecoil, Aimbot, Wallhack, Noscopeshot

 by yuyasato
"""

from pyspades.constants import *
from twisted.internet.reactor import callLater,seconds
from pyspades.server import position_data
from math import sqrt,sin,asin, cos, acos, pi, tan,atan,degrees,radians,hypot,atan2,fabs,floor
from commands import alias, admin, add, name, get_team, get_player
from pyspades.bytes import ByteReader, ByteWriter
from pyspades.packet import load_client_packet
from pyspades.common import *
from pyspades.constants import *
from pyspades import contained as loaders
import traceback

from AHT_clientcheck_Y1 import aht_client_send

OUTPUT_CONSOLE=False
DEFAULT_RECOIL=0.716
dt = 0.1	#wallhack detect accuracy

@alias('whpt')
@name('wallhackpt')
def wallhackpt(connection, player = None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
	elif connection in protocol.players:
		player = connection
	else:
		raise ValueError()
	return "%s's wallhack point is %s/500 ( %dtimes )" % (player.name, player.wallhack_points, player.wallhack_num/10 )
add(wallhackpt)

@alias('nspt')
@name('noscopept')
def noscopept(connection, player = None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
	elif connection in protocol.players:
		player = connection
	else:
		raise ValueError()
	return "%s's noscope point is %s/15 ( short%d/%d, middle%d/%d, long %d/%d )" % (player.name, player.noscope_points, player.short_off, player.short_on, player.middle_off, player.middle_on, player.long_off, player.long_on)
add(noscopept)

@alias('cspt')
@name('centershotpt')
def centershotpt(connection, player = None, ayasi=None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
	elif connection in protocol.players:
		player = connection
	else:
		raise ValueError()
	if ayasi == 'ayasi':
		player.ayasi=True
		connection.send_chat("%s keikai ok"% player.name)
	elif ayasi == 'ok':
		player.ayasi=False
		connection.send_chat("%s keikai kaijo"% player.name)
	return "%s's center shot point is %s/50 ( %s / %s )  (oshack %s)" % (player.name,  player.center_shot_points, player.theta_count + player.z_count, player.hit_count, player.ospt )
add(centershotpt)

@alias('nrpt')
@name('norecoilpt')
def norecoilpt(connection, player = None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
	elif connection in protocol.players:
		player = connection
	else:
		raise ValueError()
	player.pointsshow()
	return "%s's norecoil point is %s/200" % (player.name, player.norecoilpoints)
add(norecoilpt)

@alias('nranal')
@admin
@name('recoil_analysis')
def recoil_analysis(connection, player = None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
	elif connection in protocol.players:
		player = connection
	else:
		raise ValueError()

	player.recoil_anal = not player.recoil_anal
	if player.recoil_anal:
		return "%s's recoil analysing start" %player.name
	else:
		return "%s's recoil analysing stop" %player.name
add(recoil_analysis)

def aht_send_norecoil(suspect):
	
	s_sr_3 = suspect.stand_sr_norecoil_fire
	s_sr_2 = suspect.stand_sr_smallrecoil_fire
	s_sr_1 = suspect.stand_sr_normalfire 

	c_sr_3 = suspect.crouch_sr_norecoil_fire
	c_sr_2 = suspect.crouch_sr_smallrecoil_fire
	c_sr_1 = suspect.crouch_sr_normalfire


	s_smg_3 = suspect.stand_smg_norecoil_fire 
	s_smg_2 = suspect.stand_smg_smallrecoil_fire
	s_smg_1 = suspect.stand_smg_normalfire 
        
	c_smg_3 = suspect.crouch_smg_norecoil_fire
	c_smg_2 = suspect.crouch_smg_smallrecoil_fire
	c_smg_1 = suspect.crouch_smg_normalfire 
        

	s_sg_3 = suspect.stand_sg_norecoil_fire
	s_sg_2 = suspect.stand_sg_smallrecoil_fire
	s_sg_1 = suspect.stand_sg_normalfire 
        
	c_sg_3 = suspect.crouch_sg_norecoil_fire
	c_sg_2 = suspect.crouch_sg_smallrecoil_fire
	c_sg_1 = suspect.crouch_sg_normalfire
	norecoil_points = suspect.norecoilpoints

	return s_sr_3, s_sr_2, s_sr_1, c_sr_3, c_sr_2, c_sr_1, s_smg_3, s_smg_2, s_smg_1, c_smg_3, c_smg_2, c_smg_1, s_sg_3, s_sg_2, s_sg_1, c_sg_3, c_sg_2, c_sg_1 ,norecoil_points

def aht_send_centershot(suspect):
	cs = suspect.theta_count + suspect.z_count
	return suspect.hit_count, cs, suspect.center_shot_points,suspect.ospt

def aht_wallhack_send(suspect):
	return suspect.wallhack_points ,  suspect.wallhack_num

def aht_noscope_send(suspect):
	return suspect.noscope_points, suspect.short_on, suspect.short_off, suspect.middle_on, suspect.middle_off, suspect.long_on, suspect.long_off


def apply_script(protocol,connection,config):

	class NR_CS_WH_NS_Connection(connection):
	
		fire=False
		prephi = 0
		pretheta= 0
		pre2phi = 0
		pre2theta= 0

		predeltaphi = 0
		predeltatheta= 0
		presecdelta=0
		presec=0
		pre2secdelta=0

		pre2deltaphi = 0
		pre2deltatheta= 0

		clickend=0
		lastfired=0
		reloadtime=0
		firstpacket=False
		firstpackettime=0

		oridata=[]
		recoil_anal=False

		be_killed = False

		fivepacket=0

		fivenrp=False
		fivenrt=False
		fivenro=False

		crouching=0
		sprint_time = 0
		tool_change_time=0

		stand_sr_norecoil_fire = 0
		stand_sr_smallrecoil_fire = 0
		stand_sr_normalfire = 0

		crouch_sr_norecoil_fire = 0
		crouch_sr_smallrecoil_fire = 0
		crouch_sr_normalfire = 0

		stand_smg_norecoil_fire = 0
		stand_smg_smallrecoil_fire = 0
		stand_smg_normalfire = 0

		crouch_smg_norecoil_fire = 0
		crouch_smg_smallrecoil_fire = 0
		crouch_smg_normalfire = 0

		stand_sg_norecoil_fire = 0
		stand_sg_smallrecoil_fire = 0
		stand_sg_normalfire = 0

		crouch_sg_norecoil_fire = 0
		crouch_sg_smallrecoil_fire = 0
		crouch_sg_normalfire = 0

		norecoilpoints=0
		
		def pointsshow(self):
			print
			print self.name
			print "stand, norecoil smallrecoil normalfire  crouch, norecoil smallrecoil normalfire"
			print "SR    stand", self.stand_sr_norecoil_fire, self.stand_sr_smallrecoil_fire, self.stand_sr_normalfire,    "   \t,crouch" ,self.crouch_sr_norecoil_fire, self.crouch_sr_smallrecoil_fire, self.crouch_sr_normalfire
			print "SMG   stand", self.stand_smg_norecoil_fire, self.stand_smg_smallrecoil_fire, self.stand_smg_normalfire, "   \t,crouch", self.crouch_smg_norecoil_fire, self.crouch_smg_smallrecoil_fire, self.crouch_smg_normalfire
			print "SG    stand", self.stand_sg_norecoil_fire, self.stand_sg_smallrecoil_fire, self.stand_sg_normalfire,    "   \t,crouch", self.crouch_sg_norecoil_fire, self.crouch_sg_smallrecoil_fire, self.crouch_sg_normalfire

			print "norecoilpoint", self.norecoilpoints

		def addnorecoilpoints(self, norecoilpoints_add, norecoil):
			if norecoilpoints_add<0:
				if not self.crouching:
					if self.weapon == RIFLE_WEAPON:
						self.stand_sr_normalfire += 1
					elif self.weapon == SMG_WEAPON:
						self.stand_smg_normalfire += 1
					elif self.weapon == SHOTGUN_WEAPON:
						self.stand_sg_normalfire += 1
				else:
					if self.weapon == RIFLE_WEAPON:
						self.crouch_sr_normalfire += 1
					elif self.weapon == SMG_WEAPON:
						self.crouch_smg_normalfire += 1
					elif self.weapon == SHOTGUN_WEAPON:
						self.crouch_sg_normalfire += 1
			elif norecoil:
				if not self.crouching:
					if self.weapon == RIFLE_WEAPON:
						self.stand_sr_norecoil_fire += 1
					elif self.weapon == SMG_WEAPON:
						self.stand_smg_norecoil_fire += 1
					elif self.weapon == SHOTGUN_WEAPON:
						self.stand_sg_norecoil_fire += 1
				else:
					if self.weapon == RIFLE_WEAPON:
						self.crouch_sr_norecoil_fire += 1
					elif self.weapon == SMG_WEAPON:
						self.crouch_smg_norecoil_fire += 1
					elif self.weapon == SHOTGUN_WEAPON:
						self.crouch_sg_norecoil_fire += 1
			elif norecoilpoints_add>0:					
				if not self.crouching:
					if self.weapon == RIFLE_WEAPON:
						self.stand_sr_smallrecoil_fire += 1
					elif self.weapon == SMG_WEAPON:
						self.stand_smg_smallrecoil_fire += 1
					elif self.weapon == SHOTGUN_WEAPON:
						self.stand_sg_smallrecoil_fire += 1
				else:
					if self.weapon == RIFLE_WEAPON:
						self.crouch_sr_smallrecoil_fire += 1
					elif self.weapon == SMG_WEAPON:
						self.crouch_smg_smallrecoil_fire += 1
					elif self.weapon == SHOTGUN_WEAPON:
						self.crouch_sg_smallrecoil_fire += 1

			self.norecoilpoints+=norecoilpoints_add
			if self.norecoilpoints<0: self.norecoilpoints=0

		def fiveset1(self):
			if self.fivepacket>1:self.fivepacket=1

		def loader_received(self, loader):
			k=114514
			try:
				if self.player_id is not None:
					contained = load_client_packet(ByteReader(loader.data))
					if self.firstpacket:
						if not(contained.id == loaders.WeaponReload.id or contained.id == loaders.HitPacket.id or contained.id == loaders.BlockAction.id):
							self.firstpackettime=seconds()
							self.firstpacket=False
					if self.hp and self.world_object:
						if contained.id == loaders.WeaponReload.id:
							self.reloadtime=seconds()
						if contained.id == loaders.OrientationData.id:
							x, y, z = contained.x, contained.y, contained.z

							nowphi= degrees(asin(z))
							nowtheta= degrees(atan2(y,x)) 
							deltaphi = nowphi - self.prephi
							deltatheta = nowtheta - self.pretheta
							norecoilpoints_add=-1

							if self.world_object.primary_fire and self.recoil_anal:
								if self.weapon_object.ammo*0.7 > (seconds()-self.lastfired)/self.weapon_object.delay > self.weapon_object.ammo*0.2:
 									if seconds() - self.tool_change_time > 0.6 and seconds() - self.reloadtime > self.weapon_object.reload_time  and not self.world_object.sprint:
										self.oridata.append((nowtheta, nowphi))
							if self.fivepacket>0:
								if self.fivepacket>1:		
									if not -0.005 < self.predeltaphi - deltaphi < 0.005  or  not -0.005 <deltatheta - self.predeltatheta < 0.005:
										self.fivenro=False								
									if not -0.00001 < self.predeltaphi - deltaphi < 0.00001:
										self.fivenrp=False							
									if not -0.00001 <deltatheta - self.predeltatheta < 0.00001:
										self.fivenrt=False	
									self.fivepacket-=1
								else:
									norecoilpoints_addnr1=0
									if self.fivenro:
										if OUTPUT_CONSOLE:
											print self.name, self.weapon_object.name,"nr"
										norecoilpoints_addnr1+=3																		
									if self.fivenrp:
										if OUTPUT_CONSOLE:
											print self.name, self.weapon_object.name,"nr1p"
										norecoilpoints_addnr1+=5
									if self.fivenrt:
										if OUTPUT_CONSOLE:
											print self.name, self.weapon_object.name,"nr1t"
										norecoilpoints_addnr1+=5
									if norecoilpoints_addnr1>0:
										if self.weapon != SMG_WEAPON:
											norecoilpoints_addnr1*=2
										self.addnorecoilpoints(norecoilpoints_addnr1, False)
									self.fivenro=False	
									self.fivenrp=False	
									self.fivenrt=False	
									self.fivepacket-=1								


							if self.fire and self.tool == WEAPON_TOOL:
								callLater(self.weapon_object.delay+0.01, self.clear_recoil)
								self.fire=False
								fromfire = seconds() - self.lastfired
								fromfirstpacket = seconds() -self.firstpackettime

								if -85<self.prephi<85 and not self.be_killed:
									norecoil = False
									if fromfire < max(0.2, self.latency*0.0013) or fromfirstpacket<0.05:
										if -0.005 < self.predeltaphi - deltaphi < 0.005  and  -0.005 <deltatheta - self.predeltatheta < 0.005:
											self.fivepacket=6
											self.fivenro=True
											callLater(min(0.6, max(0.2, self.latency*0.0013)),self.fiveset1)
										if -0.00001 < self.predeltaphi - deltaphi < 0.00001:
											self.fivepacket=6
											self.fivenrp=True
											callLater(min(0.6, max(0.2, self.latency*0.0013)),self.fiveset1)
										if -0.00001 <deltatheta - self.predeltatheta < 0.00001:
											if self.weapon != SMG_WEAPON:
												self.fivepacket=6
												self.fivenrt=True
												callLater(min(0.6, max(0.2, self.latency*0.0013)),self.fiveset1)

										if aht_client_send(self):
											if self.weapon == RIFLE_WEAPON:
												weapon_ratio = 4
											elif self.weapon == SMG_WEAPON:
												weapon_ratio = 1*0.5
											elif self.weapon == SHOTGUN_WEAPON:
												weapon_ratio = 4

											crouch_ratio = self.crouching +1

											recoil = DEFAULT_RECOIL * weapon_ratio  / crouch_ratio
											if self.predeltaphi<recoil/(1+(3.0*(self.weapon == SMG_WEAPON))) and deltaphi> -recoil /4.0:
												norecoilpoints_add+=1
										norecoil = False
									else:
										if OUTPUT_CONSOLE:
											print self.name, self.weapon_object.name, "NR!!"
										norecoilpoints_add+= 11
										norecoil = True
									if norecoilpoints_add>0:
										if self.weapon != SMG_WEAPON:
											norecoilpoints_add*=2
									self.addnorecoilpoints(norecoilpoints_add, norecoil)
								self.be_killed=False
							self.pre2phi = self.prephi
							self.pre2theta= self.pretheta

							self.prephi = nowphi
							self.pretheta= nowtheta
							self.pre2secdelta=self.presecdelta*1.0
							self.presecdelta=seconds()-self.presec*1.0
							self.pre2sec = self.presec
							self.presec=seconds()
							self.pre2deltaphi = self.predeltaphi
							self.pre2deltatheta= self.predeltatheta
							self.predeltaphi = deltaphi
							self.predeltatheta= deltatheta

			except KeyError as ke:
				k=ke
			except:
				if k!=34 and k!=32:
					print "!!!! error catch code: N4  in aht_ncws loader_received !!!!"
					traceback.print_exc()
				else:
					pass
			return connection.loader_received(self, loader)

		def clear_recoil(self):
			self.predeltaphi = 0
			self.predeltatheta= 0

		def on_shoot_set(self, fire):
			if self.tool == WEAPON_TOOL:
				if fire:
					if seconds() - self.clickend > self.weapon_object.delay+0.1+(self.weapon == SMG_WEAPON)*0.2 and self.weapon_object.current_ammo>0 and seconds() - self.tool_change_time > 0.6 and seconds() - self.reloadtime > self.weapon_object.reload_time  and not self.world_object.sprint:
						self.lastfired = seconds()
						self.crouching = self.world_object.crouch
						self.fire = True
						self.firstpacket=True
				else:
					if self.recoil_anal:
						if self.oridata!=[]:
							print self.name,"orientation data"
							print "theta", "phi"
							for odata in self.oridata:
								print odata[0], odata[1]
							print 
						self.oridata=[]
					self.clickend=seconds()

				
			return connection.on_shoot_set(self, fire)
		
		def on_tool_changed(self, tool):
			if seconds() - self.lastfired <0.005:
				self.fire = False	
			self.tool_change_time=seconds()
			return connection.on_tool_changed(self, tool)

		def on_animation_update(self, jump, crouch, sneak, sprint):
			if sprint:
				if seconds() - self.lastfired <0.005:
					self.fire = False
				
			return connection.on_animation_update(self, jump, crouch, sneak, sprint)



		hit_count = 0
		theta_count = 0
		sg_first=True
		z_count = 0
		center_shot_points = 0
		ayasi=False
		ospt=0

		wallhack_num = 0
		wallhack_points = 0


		def sg_reset(self):
			self.sg_first=True
		
		def on_hit(self, hit_amount, hit_player, type, grenade):
			if not grenade and ((self.team != hit_player.team) or self.protocol.friendly_fire):
				if type <= 1:
					if self.weapon == SHOTGUN_WEAPON:
						if not self.sg_first:
							return connection.on_hit(self, hit_amount, hit_player, type, grenade)
						callLater(0.1,self.sg_reset)
						self.sg_first=False
					self.hit_count+=1 
					if self.center_shot_points>0:self.center_shot_points-=1
					s_pos_x, s_pos_y, s_pos_z = self.world_object.position.get()
					v_pos_x, v_pos_y, v_pos_z = hit_player.world_object.position.get()

					s_ori_x, s_ori_y, s_ori_z = self.world_object.orientation.get()
					v_ori_x, v_ori_y, v_ori_z = hit_player.world_object.orientation.get()

					delta_x, delta_y, delta_z = v_pos_x - s_pos_x, v_pos_y - s_pos_y, v_pos_z - s_pos_z

					theta_v = degrees(atan2(delta_y, delta_x))
					theta_ori = degrees(atan2(s_ori_y, s_ori_x))
					phi_ori= degrees(asin(s_ori_z))

					victim_phi= degrees(asin(v_ori_z))
					victim_theta= degrees(atan2(v_ori_y, v_ori_x))

					delta_theta = theta_v - theta_ori
					delta_theta_p = theta_v - self.pretheta
					delta_theta_p2 = theta_v - self.pre2theta
					delta_victim_theta = victim_theta - theta_ori

					if delta_victim_theta>180:
						delta_victim_theta-=360
					delta_victim_theta=fabs(delta_victim_theta)

					if delta_theta>180:
						delta_theta-=360
					delta_theta=fabs(delta_theta)

					if delta_theta_p>180:
						delta_theta_p-=360
					delta_theta_p=fabs(delta_theta_p)

					if delta_theta_p2>180:
						delta_theta_p2-=360
					delta_theta_p2=fabs(delta_theta_p2)

					distance_v = hypot(delta_x, delta_y)
					distance_ori = hypot(s_ori_x, s_ori_y)
					distance_ori_p = cos(radians(self.prephi))
					distance_ori_p2 = cos(radians(self.pre2phi))

					n = distance_v / distance_ori 
					n_p = distance_v / distance_ori_p 
					n_p2 = distance_v / distance_ori_p2

					if n>3:
						if delta_theta<0.0005:

							self.theta_count+=1
							self.center_shot_points+=11
							if self.center_shot_points>20:
								if OUTPUT_CONSOLE:
									print self.name, "horizontal center shot detect"
									print "d theta",delta_theta
									print "centershot points ", self.center_shot_points,"/50"


						hit_z = s_ori_z * n		#z distance at victim(x,y) from self
						hit_z_p = sin(radians(self.prephi))* n		#z distance at victim(x,y) from self
						hit_z_p2 = sin(radians(self.pre2phi)) * n		#z distance at victim(x,y) from self
						distance_z = s_pos_z + hit_z - v_pos_z    	#distance between victim.position.z to bullet.collision_point_at(victim(x,y))
						distance_z_p = s_pos_z + hit_z_p - v_pos_z    	#distance between victim.position.z to bullet.collision_point_at(victim(x,y))
						distance_z_p2 = s_pos_z + hit_z_p2 - v_pos_z    	#distance between victim.position.z to bullet.collision_point_at(victim(x,y))
						if 0.698<distance_z<0.702 or 0.898<distance_z<0.902 or -0.0005<distance_z<0.0005:

							self.z_count+=1

							self.center_shot_points+=6
							if -0.0005<distance_z<0.0005:	
								self.center_shot_points+=5					
							if self.center_shot_points>20:
								if OUTPUT_CONSOLE:
									print self.name, "vertical center shot detect"
									print "distance_z",distance_z
									print "centershot points ", self.center_shot_points,"/50"

						if self.ayasi:
								print self.name, "destance kill:",n
								print "horizontal theta",delta_theta
								print "vertical z",distance_z

			##OS hack
						if self.weapon == RIFLE_WEAPON:
							spread=degrees(asin(2*1.5/100.0))
						elif self.weapon == SMG_WEAPON:
							spread=degrees(asin(3*1.5/100.0))

						if type==1 and self.weapon != SHOTGUN_WEAPON: #headshot
							if fabs(self.world_object.velocity.z)+fabs(hit_player.world_object.velocity.z)<0.0001:

						#		d1 = fabs(self.predeltaphi/ (self.presecdelta*1.0+0.001))+fabs(self.predeltatheta/(self.presecdelta*1.0+0.001))+fabs(self.pre2deltaphi /(self.pre2secdelta*1.0+0.001))+fabs(self.pre2deltatheta/(self.pre2secdelta*1.0+0.001))<10
						#		d2 = fabs(self.predeltaphi/ (self.presecdelta*1.0+0.001))<3 and fabs(self.predeltatheta/(self.presecdelta*1.0+0.001))<3
								if self.presecdelta<0.01:
									dx=100
								elif self.presecdelta<0.05:
									dx=10
								else:
									dx=1

								if self.pre2secdelta<0.01:
									dx2=100
								elif self.presecdelta<0.05:
									dx2=10
								else:
									dx2=1

								d1 = fabs(self.predeltaphi*dx)+fabs(self.predeltatheta*dx)+fabs(self.pre2deltaphi*dx2)+fabs(self.pre2deltatheta*dx2)<1
								d2 = fabs(self.predeltaphi*dx)<0.3 and fabs(self.predeltatheta*dx)<0.3


						#		d22 = fabs(self.pre2deltaphi /(self.pre2secdelta*1.0+0.001)) < 3 and fabs(self.pre2deltatheta/(self.pre2secdelta*1.0+0.001))<3
								d22 = fabs(self.pre2deltaphi*dx2) < 0.3 and fabs(self.pre2deltatheta*dx2)<0.3

								d3 = seconds() - self.presec*1.0>1.0
								d32 = seconds() - self.pre2sec*1.0>1.0

								d4=self.pre2secdelta*self.presecdelta*(seconds() - self.presec*1.0)>0

								if self.weapon == RIFLE_WEAPON:
									spread=degrees(asin(2*1.5/100.0))
								elif self.weapon == SMG_WEAPON:
									spread=degrees(asin(3*1.5/100.0))

								vel_hori_x = (hit_player.world_object.velocity.x - self.world_object.velocity.x) * s_ori_y / distance_ori
								vel_hori_y = (hit_player.world_object.velocity.y - self.world_object.velocity.y) * s_ori_x / distance_ori
								vel_hori = fabs(vel_hori_y - vel_hori_x)

						##vert
								if -20<victim_phi<20:
									ue=-0.35
									st=0.50
									haba=0.55
								else:
									ue=-0.35
									st=0.70
									haba=0.70
								if phi_ori<0:
									hs_ue=ue-0.31+haba*1.41*tan(radians(phi_ori+spread))
									hs_st=st-haba*1.41*tan(radians(phi_ori-spread))
								else:
									hs_ue=ue-haba*1.41*tan(radians(phi_ori+spread))
									hs_st=st+haba*1.41*tan(radians(phi_ori-spread))
								if not hs_ue<distance_z<hs_st:
									if (d1 and d2 and (d22 or d32)) or d3: 
										self.ospt+=10
								else:
									if self.ospt>0:self.ospt-=1
						##hori
								if delta_victim_theta<20:
									if -20<victim_phi<20:
										yokohaba = 1.05
									else:
										yokohaba = 1.15								
								else:
									if -20<victim_phi<20:
										yokohaba = 1.30
									else:
										yokohaba = 1.55
								yokohaba *= vel_hori/0.2+1
								hs_theta=degrees(atan(yokohaba/n))+spread
								if delta_theta>hs_theta:
									if (d1 and d2 and (d22 or d32)) or d3: 
										self.ospt+=10
								else:
									if self.ospt>0:self.ospt-=1

								if self.ayasi:
									print self.name, "destance kill:",n
									print "theta%.3f kijun %.3f"%(delta_theta,hs_theta)
									print "ue%.3f st%.3f z%.3f"%(hs_ue,hs_st,distance_z)
									print "pphi2",self.pre2deltaphi
									print "pthe2",self.pre2deltatheta
									print "psec2",self.pre2secdelta
									print "sec2",seconds() - self.pre2sec*1.0
									print "pphi",self.predeltaphi
									print "pthe",self.predeltatheta
									print "psec",self.presecdelta
									print "sec",seconds() - self.presec*1.0
									print "vel hori",vel_hori


				##wallhack kill
						if self.weapon != SHOTGUN_WEAPON:
							if self.wallhack_num>0:self.wallhack_num-=1

							if n > 10:
								c_x, c_y, c_z = s_pos_x, s_pos_y, s_pos_z	
								block_num=0

								for i in range(int(n/dt)):
									c_x += s_ori_x * dt
									c_y += s_ori_y * dt
									c_z += s_ori_z * dt

									if self.protocol.map.get_solid(c_x, c_y, c_z):
										if 0.15<c_x%1.0<0.85 and 0.15<c_y%1.0<0.85 and 0.15<c_z%1.0<0.85:
											block_num+=1

								for x in [0,45,90,135,180,225,270,315]:
									sub_theta_ori = theta_ori+sin(radians(x))*spread
									sub_phi_ori= phi_ori+cos(radians(x))*spread
									sub_s_ori_z = sin(radians(sub_phi_ori))
									sub_s_ori_x, sub_s_ori_y = cos(radians(sub_phi_ori))*cos(radians(sub_theta_ori)), cos(radians(sub_phi_ori))*sin(radians(sub_theta_ori))
									c_x, c_y, c_z = s_pos_x, s_pos_y, s_pos_z	
									sub_block_num=0
			
									for i in range(int(n/dt)):
										c_x += sub_s_ori_x * dt
										c_y += sub_s_ori_y * dt
										c_z += sub_s_ori_z * dt

										if self.protocol.map.get_solid(c_x, c_y, c_z):
											if 0.15<c_x%1.0<0.85 and 0.15<c_y%1.0<0.85 and 0.15<c_z%1.0<0.85:
												sub_block_num+=1
									if sub_block_num<block_num:block_num=sub_block_num

								if block_num<=0:
									if self.wallhack_points>0:self.wallhack_points -= 1
								elif block_num>15:
									if self.wallhack_num>50:
										self.wallhack_points += (block_num / 7)*self.wallhack_num
										if OUTPUT_CONSOLE:
											print "wallhack",  self.name, block_num
									self.wallhack_num+=5
			return connection.on_hit(self, hit_amount, hit_player, type, grenade)

	##noscope
		noscope_points=0
		short_on = 0
		short_off = 0
		middle_on = 0
		middle_off = 0
		long_on = 0
		long_off = 0
		
		def on_kill(self, killer, type, grenade):
			self.be_killed=True
			if type <=1 and self!=killer and self and killer:
				s_pos_x, s_pos_y, s_pos_z = self.world_object.position.get()
				k_pos_x, k_pos_y, k_pos_z = killer.world_object.position.get()	
				delta_x, delta_y, delta_z = s_pos_x - k_pos_x, s_pos_y - k_pos_y, s_pos_z - k_pos_z
				distance_kill = hypot(delta_x, delta_y)	
				if killer.world_object.secondary_fire:
					if distance_kill < 40:
						killer.short_on += 1
						killer.noscope_points-=4
					elif distance_kill < 80:
						killer.middle_on += 1
						killer.noscope_points-=4
					else:
						killer.long_on += 1
						killer.noscope_points-=4
					if killer.noscope_points<0:
						killer.noscope_points=0
				else:
					if distance_kill < 40:
						killer.short_off += 1
					elif distance_kill < 80:
						killer.middle_off += 1
						killer.noscope_points+=1
					else:
						killer.long_off += 1
						killer.noscope_points+=3

			return connection.on_kill(self, killer, type, grenade)


	return protocol, NR_CS_WH_NS_Connection

