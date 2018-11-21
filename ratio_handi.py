"""
# A component of anti hack tools(AHT)
# this script can confirm HS/kill ratio
modified by yuyasato

# this script can make damage handicap by K/Dratio
# you can use handicap to command /handi

modified from:
  ratio.py
  K/D ratio script.
  Author: LinktersHD, Infogulch, Yourself
  Maintainer: mat^2
"""

from commands import get_player, add,alias,name,admin
from pyspades.constants import *

# True if you want to include the headshot-death ratio in the ratio
# NOTE: this makes the message overflow into two lines
HEADSHOT_RATIO = True

# "ratio" must be AFTER "votekick" in the config.txt script list
RATIO_ON_VOTEKICK = True
IRC_ONLY = False
handicapping = False

def aht_send_ratio(suspect):
	kill = suspect.ratio_kills
	hs = suspect.ratio_headshotkills
	melee = suspect.ratio_meleekills
	grenade = suspect.ratio_grenadekills
	death = suspect.ratio_deaths
	shotkill = kill - melee - grenade
	if shotkill:
		hs_ratio = hs*1.0 / shotkill*1.0
	else:
		hs_ratio = 0.0

	if death:
		kd_ratio = kill*1.0 / death *1.0
	elif kill:
		kd_ratio = 1.0
	else:
		kd_ratio = 0.0
	return kill, hs, melee, grenade, death, shotkill, hs_ratio, kd_ratio

@alias('dmg')
@name('dmgmag')
def dmgmag(connection, player = None):
	protocol = connection.protocol
	if player is not None:
		player = get_player(protocol, player)
	elif connection in protocol.players:
			return "your level is %.2f" %connection.level
	else:
		raise ValueError()
	level_diff = player.level - connection.level
	if level_diff>=0:
		dmg_mag = level_diff*1.5+1
	else:
		dmg_mag = 1/(level_diff*-1.5+1)
	return "damage magnification is %.2f  (Lv.%.2f - Lv.%.2f)" % (dmg_mag, connection.level,player.level)
add(dmgmag)

@alias('handi')
@admin
@name('handi_enable')
def handi_enable(connection):
	global handicapping
	handicapping = not handicapping
	if handicapping:
		return connection.protocol.send_chat("handicap enabled")
	else:
		return connection.protocol.send_chat("handicap disabled")
add(handi_enable)

def ratio(connection, user=None):
	msg = "You have"
	if user != None:
		connection = get_player(connection.protocol, user)
		msg = "%s has"
		if connection not in connection.protocol.players:
			raise KeyError()
		msg %= connection.name
	if connection not in connection.protocol.players:
		raise KeyError()
	
	deaths = float(max(1,connection.ratio_deaths))
	kills = float(max(1,connection.ratio_kills))
	headshotkills = connection.ratio_headshotkills
	meleekills = connection.ratio_meleekills
	grenadekills = connection.ratio_grenadekills
	
	msg += " a kill-death ratio of %.2f" % (connection.ratio_kills/deaths)
	if HEADSHOT_RATIO:
		if kills-grenadekills-meleekills==0:
			HSratio = 0
		else:
			HSratio = headshotkills/float((kills-grenadekills-meleekills))
		msg += ", headshot-shotkill ratio of %.2f" % HSratio
	msg += "					   \n(%s kills, %s deaths, %s shotkills, %s headshot, %s melee, %s grenade)." % (connection.ratio_kills, connection.ratio_deaths,int(connection.ratio_kills-grenadekills-meleekills), headshotkills, meleekills, grenadekills)
	return msg

add(ratio)

def apply_script(protocol, connection, config):
	class RatioConnection(connection):
		ratio_kills = 0
		ratio_headshotkills = 0
		ratio_meleekills = 0
		ratio_grenadekills = 0
		ratio_deaths = 0
		level=0
		
		def on_kill(self, killer, type, grenade):
			if killer is not None and ((self.team is not killer.team) or self.protocol.friendly_fire):
				if self != killer:
					killer.ratio_kills += 1
					killer.ratio_headshotkills += type == HEADSHOT_KILL
					killer.ratio_meleekills	+= type == MELEE_KILL
					killer.ratio_grenadekills  += type == GRENADE_KILL
					if killer.ratio_deaths+killer.ratio_kills>5:
						killer.level = (killer.ratio_kills - killer.ratio_deaths)*1.0 / (killer.ratio_kills + killer.ratio_deaths)*1.0
						if killer.ratio_deaths<=0:
							killer.level = (killer.ratio_kills - killer.ratio_deaths-1)*1.0 / (killer.ratio_kills + killer.ratio_deaths+1)*1.0
			self.ratio_deaths += 1

			if self.ratio_deaths+self.ratio_kills>5:
				self.level = (self.ratio_kills - self.ratio_deaths)*1.0 / (self.ratio_kills + self.ratio_deaths)*1.0
				if self.ratio_kills<=0:
					self.level = (self.ratio_kills+1 - self.ratio_deaths)*1.0 / (self.ratio_kills+1 + self.ratio_deaths)*1.0
			return connection.on_kill(self, killer, type, grenade)

		def on_hit(self, hit_amount, hit_player, type, grenade):
			if handicapping:
				level_diff = hit_player.level - self.level
				if level_diff>=0:
					dmg_mag = level_diff*1.5+1
				else:
					dmg_mag = 1/(level_diff*-1.5+1)

				return_on_hit = connection.on_hit(self, hit_amount, hit_player, type, grenade)
				if return_on_hit != False:
					if return_on_hit is not None:hit_amount=return_on_hit
					hit_amount *= dmg_mag
					handi_hit_amount = int(hit_amount)
					return handi_hit_amount	
				else:
					return False
			return connection.on_hit(self, hit_amount, hit_player, type, grenade)
	
	class RatioProtocol(protocol):
		def on_votekick_start(self, instigator, victim, reason):
			result = protocol.on_votekick_start(self, instigator, victim, reason)
			if result is None and RATIO_ON_VOTEKICK:
				message = ratio(instigator, victim.name)
				if IRC_ONLY:
					self.irc_say('* ' + message)
				else:
					self.send_chat(message, irc = True)
			return protocol.on_votekick_start(self, instigator, victim, reason)
	
	return RatioProtocol, RatioConnection
