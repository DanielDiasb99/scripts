"""
# A component of anti hack tools(AHT)
# this script can prevent transparent hack

script by yuyasato 2017
"""

from twisted.internet import reactor


def apply_script(protocol,connection,config):
	class LongnameConnection(connection):
		longname_eject=False

		def on_spawn(self,pos):
			if len(self.name)>15:
				self.longname_eject=True
				self.set_location((0, 0, -10000))
				self.longname_chat()
				reactor.callLater(4, self.longname_chat)
				reactor.callLater(15, self.longname_chat)
				reactor.callLater(30, self.longname_chat)
				reactor.callLater(45, self.kick,'name is too long')
			return connection.on_spawn(self,pos)

		def longname_chat(self):
			self.send_chat("------------------------------------------------")
			self.send_chat("------------------------------------------------")
			self.send_chat("------------------------------------------------")
			self.send_chat("------------------------------------------------")
			self.send_chat("------------------------------------------------")
			self.send_chat("so you'd better update Openspades.")
			self.send_chat("And your Openspades may be an older version,")
			self.send_chat("------------------------------------------------")
			self.send_chat("Reset name fewer than 15 letters.")
			self.send_chat("Your name is too long.")


		def on_hit(self, hit_amount, hit_player, type, grenade):
			if self.longname_eject:			
				return False
			return connection.on_hit(self, hit_amount, hit_player, type, grenade)

		def on_fall(self, damage):
			if self.longname_eject:			
				return False
			return connection.on_fall(self, damage)

		def on_block_build_attempt(self, x, y, z):
			if self.longname_eject:			
				return False
			return connection.on_block_build_attempt(self, x, y, z)

		def on_line_build_attempt(self, points):
			if self.longname_eject:			
				return False
			return connection.on_line_build_attempt(self, points)

		def on_block_destroy(self, x, y, z, mode):
			if self.longname_eject:			
				return False
			return connection.on_block_destroy(self, x, y, z, mode)
			
		def on_block_removed(self, x, y, z):
			if self.longname_eject:			
				return False
			return connection.on_block_removed(self, x, y, z)

		def on_command(self, command, parameters):
			if self.longname_eject:			
				return False
			return connection.on_command(self, command, parameters)

		def on_kill(self, killer, type, grenade):
			if self.longname_eject:			
				return False
			return connection.on_kill(self, killer, type, grenade)

		def on_grenade(self, time_left):
			if self.longname_eject:			
				return False
			return connection.on_grenade(self, time_left)

		def on_team_join(self, team):
			if self.longname_eject:			
				return False
			return connection.on_team_join(self, team)

	return protocol, LongnameConnection