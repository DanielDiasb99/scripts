def apply_script(protocol,connection,config):
	class LockBlueProtocol(protocol):
		
		def __init__(self, *arg, **kw):        	
			protocol.__init__(self, *arg, **kw)
			self.blue_team.locked = True
			self.balanced_teams = 0

	return LockBlueProtocol,connection