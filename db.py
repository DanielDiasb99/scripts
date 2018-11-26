from commands import add, admin
import clearbox
import cbc

# requires clearbox.py in the /scripts directory

limit = 65
limit_to_ban = 300

def db(connection):
    if connection.deboxing > 0:
        connection.deboxing = 0
        return 'DeBox cancelled'
    else:
        connection.deboxing = 1
        return 'Break first corner block'
add(db)

def apply_script(protocol, connection, config):
    protocol, connection = cbc.apply_script(protocol, connection, config)
    
    class ClearBoxMakerConnection(connection):
        def __init__(self, *arg, **kw):
            connection.__init__(self, *arg, **kw)
            self.deboxing = 0
            self.clearbox_x = 0
            self.clearbox_y = 0
            self.clearbox_z = 0
        
        def clear_box_solid(self, x1, y1, z1, x2, y2, z2):
            clearbox.clear_solid(self.protocol, x1, y1, z1, x2, y2, z2, self.god)
        
        def clear_box(self, x1, y1, z1, x2, y2, z2):
            clearbox.clear(self.protocol, x1, y1, z1, x2, y2, z2, self.god)
        
        def on_block_removed(self, x, y, z):
            if self.deboxing == 2:
                if self.clearbox_x > x :
                    conta_x = self.clearbox_x - x
                else:
                    conta_x = x - self.clearbox_x
                # --------------- Y --------------- #
                if self.clearfloor_y > y :
                    conta_y = self.clearbox_y - y
                else:
                    conta_y = y - self.clearbox_y
                #--------------- Z ----------------#
                if self.clearfloor_z > z :
                    conta_z = self.clearbox_z - z
                else:
                    conta_z = z - self.clearbox_z
                                       
                if conta_x > limit or conta_y > limit or conta_z > limit:
                    print("%s is trying to destroy a giant box of size X : %s Y: %s Z: %s." % (self.name, conta_x, conta_y, conta_z))
                    if conta_x > limit_to_ban or conta_y > limit_to_ban or conta_z > limit_to_ban:
                        if not self.admin:
                            self.ban('Tentou destruir uma area muito grande', 0)
                            return False
                        else:
                            self.send_chat('Giant box destroyed!')
                    else:
                        self.send_chat('Giant Debox cancelled : (GIANT BOX)')                        
                        return False
                else:
                    self.send_chat('Destroying box!')               

                self.deboxing = 0
                self.clear_box(self.clearbox_x, self.clearbox_y, self.clearbox_z, x, y, z)

            if self.deboxing == 1:
                self.clearbox_x = x
                self.clearbox_y = y
                self.clearbox_z = z
                self.send_chat('Now break opposite corner block')
                self.deboxing = 2
            return connection.on_block_removed(self, x, y, z)
    
    class ClearBoxMakerProtocol(protocol):
        def on_map_change(self, map):
            for connection in self.players.values():
                connection.deboxing = 0
            protocol.on_map_change(self, map)
    
    return ClearBoxMakerProtocol, ClearBoxMakerConnection
