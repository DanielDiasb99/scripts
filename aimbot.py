"""
# A component of anti hack tools(AHT)
# this script can detect aimbot and calculate accuracy.
# if you want see accuracy, command /accuracy or /acc

modified by yuyasato from aimbot2.py made by someone
"""

from twisted.internet.task import LoopingCall
from pyspades.constants import *
from math import sqrt, cos, acos, pi, tan
from commands import add,alias,name, admin, get_player
from twisted.internet import reactor
import re

DISABLED, KICK, BAN, WARN_ADMIN = xrange(4)

# This is an option for data collection. Data is outputted to aimbot2log.txt
DATA_COLLECTION = False

# If more than or equal to this number of weapon hit packets are recieved
# from the client in half the weapon delay time, then an aimbot is detected.
# This method of detection should have 100% detection and no false positives
# with the current aimbot.
# Note that the current aimbot does not modify the number of bullets
# of the shotgun, so this method will not work if the player uses a shotgun.
# These values may need to be changed if an update to the aimbot is released.
RIFLE_MULTIPLE_BULLETS_MAX = 8
SMG_MULTIPLE_BULLETS_MAX = 8

# The minimum number of near misses + hits that are fired before kicking, 
# banning, or warning an admin about someone using the hit percentage check
RIFLE_KICK_MINIMUM = 45
SMG_KICK_MINIMUM = 90
SHOTGUN_KICK_MINIMUM = 45

# Kick, ban, or warn when the above minimum is met and the
# bullet hit percentage is greater than or equal to this amount
RIFLE_KICK_PERC = 0.90
SMG_KICK_PERC = 0.80
SHOTGUN_KICK_PERC = 0.90

# If a player gets more kills than the KILL_THRESHOLD in the given
# KILL_TIME, kick, ban, or warn. This check is performed every
# time somebody kills someone with a gun
KILL_TIME = 20.0
KILL_THRESHOLD = 15

# If the number of headshot snaps exceeds the HEADSHOT_SNAP_THRESHOLD in the
# given HEADSHOT_SNAP_TIME, kick, ban, or warn. This check is performed every
# time somebody performs a headshot snap
HEADSHOT_SNAP_TIME = 20.0
HEADSHOT_SNAP_THRESHOLD = 6

# When the user's orientation angle (degrees) changes more than this amount,
# check if the user snapped to an enemy's head. If it is aligned with a head,
# record this as a headshot snap
HEADSHOT_SNAP_ANGLE = 90.0

# Valid damage values for each gun
RIFLE_DAMAGE = (33, 49, 100)
SMG_DAMAGE = (18, 29, 75)
SHOTGUN_DAMAGE = (16, 27, 37)

# Approximate size of player's heads in blocks
HEAD_RADIUS = 0.7

# 128 is the approximate fog distance, but bump it up a little
# just in case
FOG_DISTANCE = 135.0

# Don't touch any of this stuff
FOG_DISTANCE2 = FOG_DISTANCE**2

HEADSHOT_SNAP_ANGLE_COS = cos(HEADSHOT_SNAP_ANGLE * (pi/180.0))

aimbot_pattern = re.compile(".*(aim|bot|ha(ck|x)|cheat).*", re.IGNORECASE)

def aimbot_match(msg):
	return (not aimbot_pattern.match(msg) is None)

def point_distance2(c1, c2):
	if c1.world_object is not None and c2.world_object is not None:
		p1 = c1.world_object.position
		p2 = c2.world_object.position
		return (p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2

def dot3d(v1, v2):
	return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]

def magnitude(v):
	return sqrt(v[0]**2 + v[1]**2 + v[2]**2)

def scale(v, scale):
	return (v[0]*scale, v[1]*scale, v[2]*scale)

def subtract(v1, v2):
	return (v1[0]-v2[0], v1[1]-v2[1], v1[2]-v2[2])

def aht_send_accuracy(suspect):
	sr_hit = suspect.rifle_hits
	sr_bullet = suspect.rifle_count
	smg_hit = suspect.smg_hits
	smg_bullet = suspect.smg_count
	sg_hit = suspect.shotgun_hits
	sg_bullet = suspect.shotgun_count

	if sr_bullet:
		sr_acc = sr_hit*1.0/sr_bullet*1.0
	else:
		sr_acc = 0.0

	if smg_bullet:
		smg_acc = smg_hit*1.0/smg_bullet*1.0
	else:
		smg_acc = 0.0

	if sg_bullet:
		sg_acc = sg_hit*1.0/sg_bullet*1.0
	else:
		sg_acc = 0.0

	return sr_hit, sr_bullet, smg_hit, smg_bullet, sg_hit, sg_bullet, sr_acc, smg_acc, sg_acc

def aht_send_aimbot(suspect):
	hstime_point = suspect.hs_snap_point
	killtime_point = suspect.killtime_point
	multi = suspect.multiple_bullets_point

	#in 20sec
	hstime_count = suspect.get_headshot_snap_count()
	killtime_count = suspect.get_kill_count()

	return hstime_point, killtime_point, multi, hstime_count, killtime_count

@name('accuracy')
@alias('acc')
def accuracy(connection, name = None):
	if name is None:
		player = connection
	else:
		player = get_player(connection.protocol, name)
	return accuracy_player(player)

def accuracy_player(player, name_info = True):
	if player.rifle_count != 0:
		rifle_percent = str(int(100.0 * (float(player.rifle_hits)/float(player.rifle_count)))) + '%'
	else:
		rifle_percent = 'None'
	if player.smg_count != 0:
		smg_percent = str(int(100.0 * (float(player.smg_hits)/float(player.smg_count)))) + '%'
	else:
		smg_percent = 'None'
	if player.shotgun_count != 0:
		shotgun_percent = str(int(100.0 * (float(player.shotgun_hits)/float(player.shotgun_count)))) + '%'
	else:
		shotgun_percent = 'None'
	s = ''
	if name_info:
		s += player.name + ' has an accuracy of: '
	s += 'Rifle: %s (%s/%s)  SMG: %s (%s/%s)  Shotgun: %s (%s/%s).' % (rifle_percent, player.rifle_hits, player.rifle_count, smg_percent, player.smg_hits, player.smg_count, shotgun_percent,player.shotgun_hits,player.shotgun_count )
	return s
add(accuracy)

@admin
def hackinfo(connection, name):
	player = get_player(connection.protocol, name)
	return hackinfo_player(player)

def hackinfo_player(player):
	info = "%s #%s (%s) has an accuracy of: " % (player.name, player.player_id, player.address[0])
	info += accuracy_player(player, False)
	ratio = player.ratio_kills/float(max(1,player.ratio_deaths))
	info += " Kill-death ratio of %.2f (%s kills, %s deaths)." % (ratio, player.ratio_kills, player.ratio_deaths)
	info += " %i kills in the last %i seconds." % (player.get_kill_count(), KILL_TIME)
	info += " %i headshot snaps in the last %i seconds." % (player.get_headshot_snap_count(), HEADSHOT_SNAP_TIME)
	return info

add(hackinfo)

def apply_script(protocol, connection, config):
	class Aimbot2Protocol(protocol):
		def start_votekick(self, payload):
			if aimbot_match(payload.reason):
				payload.target.warn_admin('Hack related votekick.')
			return protocol.start_votekick(self, payload)

	class Aimbot2Connection(connection):
		def __init__(self, *arg, **kw):
			connection.__init__(self, *arg, **kw)
			self.rifle_hits = self.smg_hits = self.shotgun_hits = 0
			self.rifle_count = self.smg_count = self.shotgun_count = 0
			self.last_target = None
			self.first_orientation = True
			self.kill_times = []
			self.headshot_snap_times = []
			self.bullet_loop = LoopingCall(self.on_bullet_fire)
			self.shot_time = 0.0
			self.multiple_bullets_count = 0
			self.headshot_snap_warn_time = self.hit_percent_warn_time = 0.0
			self.kills_in_time_warn_time = self.multiple_bullets_warn_time = 0.0
			self.hs_snap_point=0
			self.multiple_bullets_point=0
			self.killtime_point=0
			self.bullet_count=0
		
		def on_spawn(self, pos):
			self.first_orientation = True
			return connection.on_spawn(self, pos)

		def bullet_loop_start(self, interval):
			if not self.bullet_loop.running:
				self.bullet_loop.start(interval)
		
		def bullet_loop_stop(self):
			if self.bullet_loop.running:
				self.bullet_count=0
				self.bullet_loop.stop()

		def on_tool_changed(self, tool):
			if tool != WEAPON_TOOL:
				self.bullet_loop_stop()
			return connection.on_tool_changed(self, tool)

		def on_reset(self):
			self.bullet_loop_stop()
			return connection.on_reset(self)
		
		def get_headshot_snap_count(self):
			pop_count = 0
			headshot_snap_count = 0
			current_time = reactor.seconds()
			for old_time in self.headshot_snap_times:
				if current_time - old_time <= HEADSHOT_SNAP_TIME:
					headshot_snap_count += 1
				else:
					pop_count += 1
			for i in xrange(0, pop_count):
				self.headshot_snap_times.pop(0)
			return headshot_snap_count

		def on_orientation_update(self, x, y, z):
			if not self.first_orientation and self.world_object is not None:
				orient = self.world_object.orientation
				old_orient_v = (orient.x, orient.y, orient.z)
				new_orient_v = (x, y, z)
				theta = dot3d(old_orient_v, new_orient_v)
				if theta <= HEADSHOT_SNAP_ANGLE_COS:
					self_pos = self.world_object.position
					if self.protocol.friendly_fire:
						for enemy in self.protocol.players.values():
							if not enemy.team.spectator:
								if self!=enemy:
									if enemy.world_object:
										if not enemy.world_object.dead:
											enemy_pos = enemy.world_object.position
											position_v = (enemy_pos.x - self_pos.x, enemy_pos.y - self_pos.y, enemy_pos.z - self_pos.z)
											c = scale(new_orient_v, dot3d(new_orient_v, position_v))
											h = magnitude(subtract(position_v, c))
											if h <= HEAD_RADIUS:
												current_time = reactor.seconds()
												self.headshot_snap_times.append(current_time)
												if self.get_headshot_snap_count() >= HEADSHOT_SNAP_THRESHOLD:
														self.hs_snap_point+=1			
					else:
						for enemy in self.team.other.get_players():
							if enemy.world_object:
								if not enemy.world_object.dead:
									enemy_pos = enemy.world_object.position
									position_v = (enemy_pos.x - self_pos.x, enemy_pos.y - self_pos.y, enemy_pos.z - self_pos.z)
									c = scale(new_orient_v, dot3d(new_orient_v, position_v))
									h = magnitude(subtract(position_v, c))
									if h <= HEAD_RADIUS:
										current_time = reactor.seconds()
										self.headshot_snap_times.append(current_time)
										if self.get_headshot_snap_count() >= HEADSHOT_SNAP_THRESHOLD:
												self.hs_snap_point+=1

			else:
				self.first_orientation = False
			return connection.on_orientation_update(self, x, y, z)
		
		def on_shoot_set(self, shoot):
			if self.tool == WEAPON_TOOL:
				if shoot and not self.bullet_loop.running:
					if self.weapon == SMG_WEAPON:
						self.bullet_loop_start(0.1)
					else:
						self.bullet_loop_start(self.weapon_object.delay)
				elif not shoot:
					self.bullet_loop_stop()
			return connection.on_shoot_set(self, shoot)
		
		def get_kill_count(self):
			current_time = reactor.seconds()
			kill_count = 0
			pop_count = 0
			for old_time in self.kill_times:
				if current_time - old_time <= KILL_TIME:
					kill_count += 1
				else:
					pop_count += 1
			for i in xrange(0, pop_count):
				self.kill_times.pop(0)
			return kill_count

		def on_kill(self, by, type, grenade):
			if by is not None and by is not self:
				if type == WEAPON_KILL or type == HEADSHOT_KILL:
					by.kill_times.append(reactor.seconds())
					if by.get_kill_count() >= KILL_THRESHOLD:
						by.killtime_point+=1
			return connection.on_kill(self, by, type, grenade)

		def on_hit(self, hit_amount, hit_player, type, grenade):
			if (self.team is not hit_player.team) or self.protocol.friendly_fire:
				if type == WEAPON_KILL or type == HEADSHOT_KILL:
					current_time = reactor.seconds()
					shotgun_use = False
					if current_time - self.shot_time > (0.1 * self.weapon_object.delay):
						shotgun_use = True
						self.multiple_bullets_count = 0
						self.shot_time = current_time
						if self.multiple_bullets_point>0:self.multiple_bullets_point-=1

					if not grenade:
						self.multiple_bullets_count += 1
					if self.weapon == RIFLE_WEAPON:
						self.rifle_hits += 1
						if self.multiple_bullets_count >= 3:
							self.multiple_bullets_point+=1
							return False
					elif self.weapon == SMG_WEAPON:
						self.smg_hits += 1
						if self.multiple_bullets_count >= 4:
							self.multiple_bullets_point+=1
							return False
					elif self.weapon == SHOTGUN_WEAPON:
						if shotgun_use:
							self.shotgun_hits += 1

			return connection.on_hit(self, hit_amount, hit_player, type, grenade)

		def _on_reload(self):
			self.bullet_count=0			
			return connection._on_reload(self)

		def on_bullet_fire(self):
			# Remembering the past offers a performance boost, particularly with the SMG
			if self:
				if self.weapon_object.current_ammo-self.bullet_count>0 and not self.world_object.sprint:
					self.bullet_count+=1
					self.possible_targets = []
					if self.protocol.friendly_fire:
						for enemy in self.protocol.players.values():
							if self != enemy:
								if point_distance2(self, enemy) <= FOG_DISTANCE2:
									self.possible_targets.append(enemy)
					else:
						for enemy in self.team.other.get_players():
							if point_distance2(self, enemy) <= FOG_DISTANCE2:
								self.possible_targets.append(enemy)					
					for enemy in self.possible_targets:
				#		if enemy.hp is not None:
							if self.check_near_miss(enemy):
								self.last_target = enemy
								return

		def check_near_miss(self, target):
			if self.world_object is not None and target.world_object is not None:
				p_self = self.world_object.position
				p_targ = target.world_object.position
				position_v = (p_targ.x - p_self.x, p_targ.y - p_self.y, p_targ.z - p_self.z)
				position_leg = (p_targ.x - p_self.x, p_targ.y - p_self.y, p_targ.z - p_self.z+2.7)
				orient = self.world_object.orientation
				orient_v = (orient.x, orient.y, orient.z)
				position_v_mag = magnitude(position_v)
				position_leg_mag = magnitude(position_leg)
				if position_v_mag < 6:
					if self.weapon == SHOTGUN_WEAPON:
						NEAR_MISS_COS = cos((19+(7-position_v_mag)**2) * (pi/180.0)*2)
					else:
						NEAR_MISS_COS = cos((19+(7-position_v_mag)**2) * (pi/180.0))
				elif position_v_mag < 15:
					if self.weapon == SHOTGUN_WEAPON:
						NEAR_MISS_COS = cos((25-position_v_mag) * (pi/180.0)*2)
					else:
						NEAR_MISS_COS = cos((25-position_v_mag) * (pi/180.0))
				else:
					if self.weapon == SHOTGUN_WEAPON:
						NEAR_MISS_COS = cos(10 * (pi/180.0)*2)
					else:
						NEAR_MISS_COS = cos(10 * (pi/180.0))
				if position_v_mag < 2 or (dot3d(orient_v, position_v)/position_v_mag) >= NEAR_MISS_COS or (dot3d(orient_v, position_leg)/position_leg_mag) >= NEAR_MISS_COS:
					if self.weapon == RIFLE_WEAPON:
						self.rifle_count += 1
					elif self.weapon == SMG_WEAPON:
						self.smg_count += 1
					elif self.weapon == SHOTGUN_WEAPON:
						self.shotgun_count += 1
					return True
			return False
		
		# Data collection stuff
		def on_disconnect(self):
			self.bullet_loop_stop()
			if DATA_COLLECTION:
				if self.name != None:
					with open('aimbot2log.txt','a') as myfile:
						output = self.name.encode('ascii','ignore').replace(',','') + ','
						output += str(self.rifle_hits) + ',' + str(self.rifle_count) + ','
						output += str(self.smg_hits) + ',' + str(self.smg_count) + ','
						output += str(self.shotgun_hits) + ',' + str(self.shotgun_count) + '\n'
						myfile.write(output)
						myfile.close()
			return connection.on_disconnect(self)
	
	return Aimbot2Protocol, Aimbot2Connection