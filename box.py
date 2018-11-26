from commands import add, admin
import buildbox
import cbc

box_limit = 63
box_limit_to_ban = 320

def box(connection, filled = ""):
    if connection.boxing > 0:
        connection.boxing = 0
        return 'Building generator cancelled'
    else:
        connection.boxing = 1
        connection.boxing_filled = filled.lower() == "filled"
        return 'Place first corner block'
add(box)

def apply_script(protocol, connection, config):
    protocol, connection = cbc.apply_script(protocol, connection, config)   
    
    class BoxMakerConnection(connection):
        def __init__(self, *arg, **kw):
            connection.__init__(self, *arg, **kw)
            self.boxing = 0
            self.boxing_filled = 0
            self.box_x = 0
            self.box_y = 0
            self.box_z = 0              
        
        def build_box_filled(self, x1, y1, z1, x2, y2, z2, color = None):
            buildbox.build_filled(self.protocol, x1, y1, z1, x2, y2, z2, color or self.color, self.god, self.god_build)
        
        def build_box(self, x1, y1, z1, x2, y2, z2, color = None):
            buildbox.build_empty(self.protocol, x1, y1, z1, x2, y2, z2, color or self.color, self.god, self.god_build)
        
        def on_block_build(self, x, y, z):

            if self.boxing == 2:
                self.boxing = 0
                # -------------- X -----------------#
                if self.box_x > x :
                    conta_x = self.box_x - x
                else:
                    conta_x = x - self.box_x
                # --------------- Y --------------- #
                if self.box_y > y :
                    conta_y = self.box_y - y
                else:
                    conta_y = y - self.box_y
                #--------------- Z ----------------#
                if self.box_z > z :
                    conta_z = self.box_z - z
                else:
                    conta_z = z - self.box_z
                    
                if conta_x > box_limit or conta_y > box_limit or conta_z > box_limit:
                    print("%s tried to make a giant box of size X : %s Y: %s Z: %s." % (self.name, conta_x, conta_y, conta_z))
                    if conta_x > box_limit_to_ban or conta_y > box_limit_to_ban or conta_z > box_limit_to_ban:
                        if self.admin is not True:
                            self.ban('Tentou bugar o servidor', 0)
                    if self.admin is True:                  
                        if self.boxing_filled == 0:
                            self.build_box(self.box_x, self.box_y, self.box_z, x, y, z)
                        else:                       
                            self.build_box_filled(self.box_x, self.box_y, self.box_z, x, y, z)
                        self.send_chat('Giant Box created!')                
                    else:
                        self.send_chat('Box building cancelled : (GIANT BOX)')
                    return False            
                else:
                    if self.boxing_filled == 0:
                        self.build_box(self.box_x, self.box_y, self.box_z, x, y, z)
                    else:                       
                        self.build_box_filled(self.box_x, self.box_y, self.box_z, x, y, z)
                    self.send_chat('Box created!')
                        
            if self.boxing == 1:
                self.box_x = x
                self.box_y = y
                self.box_z = z
                #print("%s is building a box in  X :%s, Y : %s, Z : %s " % (self.name, x,y,z))
                self.send_chat('Now place opposite corner block')
                self.boxing = 2
            return connection.on_block_build(self, x, y, z)
    
    class BoxMakerProtocol(protocol):       
        def on_map_change(self, map):
            for connection in self.players.values():
                connection.boxing = 0
            protocol.on_map_change(self, map)
    
    return BoxMakerProtocol, BoxMakerConnection