"""
# A component of anti hack tools(AHT)
# if this script work, hacker is ejected to sky, and freeze hacker's PC.
# if you need not performance ejecting to sky, turn False EJECT_Performance in line 16.

script by yuyasato 2017
"""
from twisted.internet import reactor
from pyspades.constants import *
from pyspades.server import fog_color
from pyspades.common import make_color
from commands import admin, add, name, get_team, get_player,alias
from pyspades.contained import KillAction

DEFAULT_BAN_MASSAGE = 'hack'
EJECT_Performance = True

# ban duration depend ban records. The forth time is permanent.
BAN_DURATION_1 = 1   #minutes
BAN_DURATION_2 = 5
BAN_DURATION_3 = 60

MESSAGE_1 = "YOU'RE BANNED (%d minute). uninstall the fuckin hack tool, so you can replay this server."%BAN_DURATION_1
MESSAGE_2 = "YOU'RE BANNED (%d minutes). Auto hack detect working. Don't use cheat next time."%BAN_DURATION_2
MESSAGE_3 = "YOU'RE BANNED (%d minutes). This is the last chance. Next is permanent BAN."%BAN_DURATION_3
MESSAGE_4 = "YOU'RE BANNED (permanent). GOODBYE FUCKIN CHEATER."

def aht_hacker_eject(hacker,reason=None,num=0):
	hacker.baneject(reason,num)

def apply_script(protocol,connection,config):
	class HackerejectConnection(connection):
		banflying = False
		reason = None
		z_time=0
		ban_durat=0

		def banfly(self, x, y, z, z_time):
			if self.banflying:
				if z<-500:
					x = -255
					y = -255
				if z<-1000:
					self.kick('')
				z_v=-0.001-z_time
				z += z_v
				z_time += 0.001
				if not EJECT_Performance:
					self.set_location((0,0,-10000))
					reactor.callLater(10, self.kick,'hack')
				else:
					self.set_location((x, y, z))
					reactor.callLater(0.01, self.banfly, x, y, z,z_time)

		def baneject(self,reason=None,num=0):
				self.drop_flag()
				self.reason = reason
				self.banflying = True
				self.respawn_time = -1
				kill_action = KillAction()
				kill_action.kill_type = FALL_KILL
				kill_action.player_id = kill_action.killer_id = self.player_id
				self.send_contained(kill_action)
				self.protocol.send_chat("Auto hack detect script working. Don't use hack.")
				if reason!=None:
					self.protocol.send_chat("The fuckin cheater '%s' was BANNED!   GOODBYE!  (%s detected)"% (self.name, reason))
				else:					
					self.protocol.send_chat("The fuckin cheater '%s' was BANNED!   GOODBYE!"% self.name)

				if num<=1:
					self.ban_durat=BAN_DURATION_1
					self.send_chat(MESSAGE_1)
					reactor.callLater(4, self.send_chat,MESSAGE_1)
				elif num <= 2:
					self.ban_durat=BAN_DURATION_2
					self.send_chat(MESSAGE_2)
					reactor.callLater(4, self.send_chat,MESSAGE_2)
				elif num == 3:
					self.ban_durat=BAN_DURATION_3
					self.send_chat(MESSAGE_3)
					reactor.callLater(4, self.send_chat,MESSAGE_3)
				elif num >= 4:
					self.ban_durat=9999999999999999999999999999999999-639
					self.send_chat(MESSAGE_4)
					reactor.callLater(4, self.send_chat,MESSAGE_4)
				z_time=0
				if self.team.spectator:
					x, y, z = 255,255,64
				else:
					x, y, z = self.world_object.position.get()
				self.banfly(x, y, z,z_time) 
		
		def respawn(self):
			if self.banflying:
				return False
			return connection.respawn(self)
		
		def on_disconnect(self):
			if self.banflying:
				if self.reason:
					ban_reason = self.reason
				else:
					ban_reason = DEFAULT_BAN_MASSAGE
				if self.ban_durat>0:
					BAN_DURATION = self.ban_durat
				else:
					BAN_DURATION = 9999999999999999999999999999999999-639
				self.ban(ban_reason, BAN_DURATION)
				print self.name ," banned for ", BAN_DURATION ," minutes : ", ban_reason
				self.banflying=False
			return connection.on_disconnect(self)


		def on_hit(self, hit_amount, hit_player, type, grenade):
			if self.banflying:			
				return False
			return connection.on_hit(self, hit_amount, hit_player, type, grenade)

		def on_block_destroy(self, x, y, z, mode):
			if self.banflying:			
				return False
			return connection.on_block_destroy(self, x, y, z, mode)
			
		def on_block_removed(self, x, y, z):
			if self.banflying:			
				return False
			return connection.on_block_removed(self, x, y, z)

		def on_command(self, command, parameters):
			if self.banflying:			
				return False
			return connection.on_command(self, command, parameters)

		def on_team_join(self, team):
			if self.banflying:			
				return False
			return connection.on_team_join(self, team)

		
	return protocol, HackerejectConnection