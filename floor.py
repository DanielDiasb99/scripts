from commands import add, admin
import buildbox
import cbc

floor_limit_size = 169
floor_limit_size_to_ban = 320

# requires buildbox.py script in the /scripts folder

def floor(connection):
	if connection.flooring > 0:
		connection.flooring = 0
		return 'Floor generator cancelled'
	else:
		connection.flooring = 1
		return 'Place first corner block'
add(floor)

def apply_script(protocol, connection, config):
	protocol, connection = cbc.apply_script(protocol, connection, config)
	
	class FloorMakerConnection(connection):
		def __init__(self, *arg, **kw):
			connection.__init__(self, *arg, **kw)
			self.flooring = 0
			self.floor_x = 0
			self.floor_y = 0
			self.floor_z = 0
		
		def on_block_build(self, x, y, z):
			if self.flooring == 2:
				self.flooring = 0				
				#-----------X-----------#
				if self.floor_x > x:
					conta_x = self.floor_x - x
				else:
					conta_x = x - self.floor_x
				#-----------Y-----------#
				if self.floor_y > y:
					conta_y = self.floor_y - y
				else:
					conta_y = y - self.floor_y
				#-----------Z-----------#				
				print "%s is building a Floor with size: X: %s Y: %s " % (self.name, conta_x, conta_y)
				
				if conta_x > floor_limit_size or conta_y > floor_limit_size:
					if conta_x > floor_limit_size_to_ban:
						if not self.admin:
							self.ban('Tentou bugar o servidor', 0)
						else:
							buildbox.build_filled(self.protocol, self.floor_x, self.floor_y, self.floor_z, x, y, self.floor_z, self.color, self.god, self.god_build)
							self.send_chat('Building giant box')
					else:
						self.send_chat('Floor building cancelled (GIANT FLOOR)')
					return False
				else:	
					if self.floor_z != z:
						self.send_chat('Surface is uneven! Using first height.')					
					buildbox.build_filled(self.protocol, self.floor_x, self.floor_y, self.floor_z, x, y, self.floor_z, self.color, self.god, self.god_build)
					
			if self.flooring == 1:
				self.floor_x = x
				self.floor_y = y
				self.floor_z = z
				self.send_chat('Now place opposite corner block')
				self.flooring = 2
			return connection.on_block_build(self, x, y, z)
	
	class FloorMakerProtocol(protocol):
		def on_map_change(self, map):
			for connection in self.players.values():
				connection.flooring = 0
			protocol.on_map_change(self, map)
	
	return FloorMakerProtocol, FloorMakerConnection
