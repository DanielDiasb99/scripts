from commands import add, admin
import clearbox
import cbc

# requires clearbox.py in the /scripts directory

limit = 65
limit_to_ban = 300

def df(connection):
    if connection.deflooring > 0:
        connection.deflooring = 0
        return 'DeFloor cancelled'
    else:
        connection.deflooring = 1
        return 'Break first corner block'
add(df)

def apply_script(protocol, connection, config):
    protocol, connection = cbc.apply_script(protocol, connection, config)
    
    class ClearFloorMakerConnection(connection):
        def __init__(self, *args, **kwargs):
            connection.__init__(self, *args, **kwargs)
            self.deflooring = 0
            self.clearfloor_x = 0
            self.clearfloor_y = 0
            self.clearfloor_z = 0
        
        def on_block_removed(self, x, y, z):
            if self.deflooring == 2:
                if self.clearfloor_x > x :
                    conta_x = self.clearfloor_x - x
                else:
                    conta_x = x - self.clearfloor_x
                # --------------- Y --------------- #
                if self.clearfloor_y > y :
                    conta_y = self.clearfloor_y - y
                else:
                    conta_y = y - self.clearfloor_y
                #--------------- Z ----------------#
                if self.clearfloor_z > z :
                    conta_z = self.clearfloor_z - z
                else:
                    conta_z = z - self.clearfloor_z
                                       
                if conta_x > limit or conta_y > limit or conta_z > limit:
                    print("%s is trying to destroy a giant area of size X : %s Y: %s Z: %s." % (self.name, conta_x, conta_y, conta_z))
                    if conta_x > limit_to_ban or conta_y > limit_to_ban or conta_z > limit_to_ban:
                            if not self.admin:
                                self.ban('Tentou destruir uma area muito grande', 0)
                    if self.admin is True:
                        self.send_chat('Giant area destroyed!')
                    else:
                        self.send_chat('DeFloor giant area cancelled : (GIANT AREA)')                        
                        return False
                self.deflooring = 0
                if self.clearfloor_z != z:
                    self.send_chat('Surface is uneven! Using first height.')
                clearbox.clear_solid(self.protocol, self.clearfloor_x, self.clearfloor_y, self.clearfloor_z, x, y, self.clearfloor_z, self.god)

                self.send_chat('Floor destroyed!')
            if self.deflooring == 1:
                self.clearfloor_x = x
                self.clearfloor_y = y
                self.clearfloor_z = z
                self.send_chat('Now break opposite corner block')
                self.deflooring = 2
            return connection.on_block_removed(self, x, y, z)
    
    class ClearFloorMakerProtocol(protocol):
        def on_map_change(self, map):
            for connection in self.players.values():
                connection.deflooring = 0
            protocol.on_map_change(self, map)
    
    return ClearFloorMakerProtocol, ClearFloorMakerConnection
