from time import sleep
import unittest

from server import Server
from client import Client, TIMESTAMPPRIORITY
from object import Object

#
# Test scenarios:
# 1. sync from server to client: new objects and object updates
# 2. sync from client to server: new objects and object updates
# 3. sync from client to server to other client
# 4. no unneeded syncing (e.g. client syncs update to server, and when client syncs again it receives its own update again, this should not occur)
# 5. syncing of deleted objects (isdeleted=1)
# 6. syncing with conflict handling: object is updated on client and on server and then syncing takes place
# 7. syncing with primary key conflict: object with same PK is created both on client and on server and then syncing takes place
# 8. syncing with primary key conflict: object with same PK is created client A and client B and then syncing takes place
# 9. full sync, with locally created objects that are not synced yet
#


class ClientServerTest(unittest.TestCase):
    
    def setUp(self):
        self.server = Server("server")
        self.client1 = Client("client1", self.server)
        self.client1.handling = TIMESTAMPPRIORITY
        self.client2 = Client("client2", self.server)
        self.client2.handling = TIMESTAMPPRIORITY
    
    def testSyncFromServerToClient(self):
        ''' Add an object on the server and sync with the client '''
        
        self.server.add_object("2014-05-10", "apples", "3")
        self.assertEqual(len(self.server.objects), 1)
        
        o = self.server.objects[0]
        self.assertEqual(o.pk, "2014-05-10")
        self.assertEqual(o.name, "apples")
        self.assertEqual(o.value, "3")
        self.assertEqual(self.server.counter, 1)
        
        # Make sure the client has no objects
        self.assertEqual(len(self.client1.objects), 0)
        
        # Now sync the server to the client
        self.client1.do_sync()
        self.assertEqual(len(self.client1.objects), 1)
        
        # Sync the client to the server again, should be no change
        self.client1.do_sync()
        self.assertEqual(len(self.client1.objects), 1)
        
        # Update the object on the server
        self.server.update_object("2014-05-10", "5")
        self.assertEqual(self.server.counter, 2)
        
        # Sync the client
        self.client1.do_sync()
        self.assertEqual(len(self.client1.objects), 1)
        
        # Check that the object was updated on the client
        o = self.client1.objects[0]
        self.assertEqual(o.pk, "2014-05-10")
        self.assertEqual(o.value, "5")
    
    def testSyncFromClientToServer(self):
        ''' Add an object on the client and sync with the server '''
        
        self.client1.add_object("2014-05-10", "apples", "3")
        self.assertEqual(len(self.client1.objects), 1)
        
        o = self.client1.objects[0]
        self.assertEqual(o.pk, "2014-05-10")
        self.assertEqual(o.name, "apples")
        self.assertEqual(o.value, "3")
        self.assertEqual(self.client1.counter, 1)
        
        # Make sure the server has no objects
        self.assertEqual(len(self.server.objects), 0)
        
        # Now sync the client to the server
        self.client1.do_sync()
        
        # Server should now have 1 object
        self.assertEqual(len(self.server.objects), 1)
        
        # Sync the client to the server again, should be no change
        self.client1.do_sync()
        self.assertEqual(len(self.client1.objects), 1)
        self.assertEqual(len(self.server.objects), 1)
        
        # Update the object on the client
        self.client1.update_object("2014-05-10", "5")
        self.assertEqual(self.client1.counter, 2)
        
        # Sync the client
        self.client1.do_sync()
        
        # Check that the object was updated on the server
        o = self.server.objects[0]
        self.assertEqual(o.pk, "2014-05-10")
        self.assertEqual(o.value, "5")
    
    def testSyncFromClient1ToServerToClient2(self):
        ''' Add an object on client1, sync with the server, then sync with client2 '''
        
        self.client1.add_object("2014-05-10", "apples", "3")
        self.assertEqual(len(self.client1.objects), 1)
        
        # Make sure the server and client2 have no objects
        self.assertEqual(len(self.server.objects), 0)
        self.assertEqual(len(self.client2.objects), 0)
        
        # Now sync the client to the server
        self.client1.do_sync()
        
        # Server should now have 1 object
        self.assertEqual(len(self.server.objects), 1)
        
        # Sync client2 to the server
        self.client2.do_sync()
        
        # Client2 should now have 1 object
        self.assertEqual(len(self.client2.objects), 1)
        self.assertEqual(self.client2.counter, 0)
        
        # Sync client1 to the server again, should be no change
        self.client1.do_sync()
        self.assertEqual(len(self.client1.objects), 1)
        
        # Sync client2 to the server again, should be no change
        self.client2.do_sync()
        self.assertEqual(len(self.client2.objects), 1)
        
        # Update the object on client1
        self.client1.update_object("2014-05-10", "5")
        self.assertEqual(self.client1.counter, 2)
        
        # Sync client1
        self.client1.do_sync()
        self.assertEqual(self.client1.counter, 2)
        
        # Sync client2
        self.client2.do_sync()
        self.assertEqual(self.client2.counter, 0)
        
        # Check that the object on client2 has been updated from the server
        o = self.client2.objects[0]
        self.assertEqual(o.pk, "2014-05-10")
        self.assertEqual(o.value, "5")
        
        # Update the object on client2
        self.client2.update_object("2014-05-10", "7")
        self.assertEqual(self.client2.counter, 1)
         
        # Sync client2
        self.client2.do_sync()
        self.assertEqual(self.client2.counter, 1)
       
        # Check that the object on server has been updated from client2
        o = self.server.objects[0]
        self.assertEqual(o.pk, "2014-05-10")
        self.assertEqual(o.value, "7")
        
        # Sync client1
        self.client1.do_sync()
        self.assertEqual(self.client1.counter, 2)
       
        # Check that the object on client1 has been updated from the server
        o = self.client1.objects[0]
        self.assertEqual(o.pk, "2014-05-10")
        self.assertEqual(o.value, "7")
    
    def testForUnneededSync(self):
        '''  '''
        
        self.client1.add_object("2014-05-10", "apples", "3")
        self.assertEqual(len(self.client1.objects), 1)
        
        # Sync client1 to the server
        self.client1.do_sync()
        self.assertEqual(len(self.server.objects), 1)
        
        # Sync client1 to the server again, should be no change
        self.client1.do_sync()
        self.assertEqual(len(self.client1.objects), 1)
        
        # Sync client2 to the server
        self.client2.do_sync()
        self.assertEqual(len(self.client2.objects), 1)
        
        # Sync client1 to the server again, should be no change
        self.client1.do_sync()
        self.assertEqual(len(self.client1.objects), 1)
        
        # Sync client2 to the server again, should be no change
        self.client2.do_sync()
        self.assertEqual(len(self.client2.objects), 1)
        
        # Sync client1 to the server again, should be no change
        self.client1.do_sync()
        self.assertEqual(len(self.client1.objects), 1)
        
        # Sync client2 to the server again, should be no change
        self.client2.do_sync()
        self.assertEqual(len(self.client2.objects), 1)
    
    def testDeletedItems(self):
        ''' Syncing of deleted items '''
        
        self.client1.add_object("2014-05-10", "apples", "3")
        self.assertEqual(len(self.client1.objects), 1)
        
        o = self.client1.objects[0]
        self.assertEqual(o.pk, "2014-05-10")
        self.assertEqual(o.name, "apples")
        self.assertEqual(o.value, "3")
        self.assertEqual(self.client1.counter, 1)
        
        # Make sure the server has no objects
        self.assertEqual(len(self.server.objects), 0)
        
        # Sync the client to the server
        self.client1.do_sync()
        
        # Delete the object
        self.client1.delete_object("2014-05-10")
        
        # Sync the client to the server
        self.client1.do_sync()
        
        # Check that the object was marked deleted
        o = self.server.objects[0]
        self.assertTrue(o.deleted)
    
    def testSyncConflict(self):
        ''' Syncing with conflict handling - ojbect is updated on client and on server,
        then syncing takes place '''
        
        self.client1.add_object("2014-05-10", "apples", "3")
        self.assertEqual(len(self.client1.objects), 1)
        
        o = self.client1.objects[0]
        self.assertEqual(o.pk, "2014-05-10")
        self.assertEqual(o.name, "apples")
        self.assertEqual(o.value, "3")
        self.assertEqual(self.client1.counter, 1)
        
        # Make sure the server has no objects
        self.assertEqual(len(self.server.objects), 0)
        
        # Sync the client to the server
        self.client1.do_sync()
        
        # Update the object on the client
        self.client1.update_object("2014-05-10", "5")
        
        # Make sure timestamplastupdate on client and server is different
        sleep(2)
        
        # Update the object on the server
        self.server.update_object("2014-05-10", "7")
        self.assertEqual(self.server.counter, 2)
        
        # Sync the client to the server
        self.client1.do_sync()
        
        o = self.client1.objects[0]
        self.assertEqual(o.pk, "2014-05-10")
        self.assertEqual(o.value, "7")
        
if __name__ == '__main__':
    unittest.main()
