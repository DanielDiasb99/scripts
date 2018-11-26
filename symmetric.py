from commands import add, admin,alias
import cbc, buildbox

@alias('s')
def symmetric(self, ):
        if self.doing > 0 :
                self.doing = 0
                self.send_chat("Symmetric build cancelled")
        else:
                self.doing = 1
                self.send_chat("Place the center block for symmetric")
add (symmetric)

def apply_script(protocol, connection, config):
        protocol, connection = cbc.apply_script(protocol, connection, config)
        class SimetricConnection(connection):
        
                doing = 0
                center_x = 0
                center_y = 0
                center_z = 0
                
                def on_block_build(self, x, y, z):

                        if self.doing == 2:
                                block_x = self.center_x - x
                                block_y = y - self.center_y
                                block_z = z                             

                                tp_x = self.center_x + block_x
                                tp_y = block_y + self.center_y                          
                                tp_z = block_z
                                
                                #print ('X: %s, Y: %s, Z: %s' % (x,y,z))                                
                                #print ('Symetric coordinates : X: %s, Y: %s, Z: %s' % (block_x, block_y, block_z))
                                #print ('Where to place : X: %s, Y: %s, Z: %s ' % (tp_x, tp_y, tp_z))
                                self.build_box(tp_x, tp_y, tp_z, tp_x, tp_y, tp_z)
                                self.send_chat('Symmetrick block created')
                
                        if self.doing == 1:
                                self.center_x = x
                                self.center_y = y
                                self.center_z = z
                                #print ('Center : X: %s, Y: %s, Z: %s' % (self.center_x, self.center_y, self.center_z))
                                self.send_chat('Now place blocks to build with symmetric')
                                self.doing = 2
                                
                        return connection.on_block_build(self, x, y, z)
        
        class SimetricProtocol(protocol):
                def on_map_change(self, map):
                        for connection in self.players.values():
                                connection.doing = 0
                        protocol.on_map_change(self, map)       
        
        return SimetricProtocol, SimetricConnection