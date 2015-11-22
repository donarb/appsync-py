from datetime import datetime

from server import OK
from object import Object

TIMESTAMPPRIORITY = 1
SERVERPRIORITY = 2
CLIENTPRIORITY = 3

class Client:
    
    def __init__(self, name, server):
        
        self.name = name
        self.server = server
        self.counter = 0
        self.conflict_handling = TIMESTAMPPRIORITY
        self.lastsync_counter = 0
        self.lastsync_servercounter = 0
        self.objects = []
    
    def sync_from_server(self):
        
        result = self.server.sync_to_client(self.lastsync_servercounter)
        
        for sob in result['objects']:
            
            exists = False
            for o in self.objects:
                
                if o.guid == sob.guid or o.pk == sob.pk:
                    
                    exists = True
                    
                    # Handle pk conflict
                    if o.pk == sob.pk:
                        o.guid = sob.guid
                    
                    # Check for conflict (object updated locally since last sync to server)
                    if o.lastupdate_counter > self.lastsync_counter:
                        # Decide how to handle conflict
                        if self.conflict_handling == SERVERPRIORITY:
                            o.value = sob.value
                            o.deleted = sob.deleted
                        elif self.conflict_handling == CLIENTPRIORITY:
                            ''' no change to local object '''
                        elif self.conflict_handling == TIMESTAMPPRIORITY:
                            if sob.timestampupdated > o.timestampupdated:
                                o.value = sob.value
                                o.deleted = sob.deleted
                                o.timestampupdated = datetime.now()
                    else:
                        # No conflict, update object locally
                        o.value = sob.value
                        o.deleted = sob.deleted
            
            if not exists:
                
                no = Object(sob.pk, sob.name, sob.value, sob.guid)
                no.deleted = sob.deleted
                no.lastupdate_counter = self.counter
                self.objects.append(no)
        
        if result['statuscode'] == OK:
            self.lastsync_servercounter = result['servercounter']
    
    def sync_to_server(self):
        
        objects = [o for o in self.objects if o.lastupdate_counter > self.lastsync_counter]
        result = self.server.sync_from_client(objects)
        if result['statuscode'] == OK:
            self.lastsync_counter = self.counter
            self.lastsync_servercounter = result['servercounter']
    
    def do_sync(self):
        self.sync_from_server()
        self.sync_to_server()
    
    def do_full_sync(self):
        self.lastsync_counter = 0           # force full sync to server
        self.lastsync_servercounter = 0     # force full sync from server
        self.do_sync()
    
    def add_object(self, pk, name, value):
        ''' Create object on client (do not use this function to add object from
        a server sync) '''
        
        # Check for duplicate primary key
        if any(o.pk == pk for o in self.objects):
            print "Error creating new object on client {}: primary key {} already in use".format(self.name, pk)
        
        no = Object(pk, name, value)
        self.counter += 1
        no.lastupdate_counter = self.counter
        self.objects.append(no)
    
    def update_object(self, pk, value):
        ''' Update object on client (do not use this function to update object from
        a server sync) '''
        for o in self.objects:
            if o.pk == pk:
                o.update(value)
                self.counter += 1
                o.lastupdate_counter = self.counter
    
    def delete_object(self, pk):
        ''' Delete object on client (do not use this function to delete object from
        a server sync) '''
        for o in self.objects:
            if o.pk == pk:
                o.delete()
                self.counter += 1
                o.lastupdate_counter = self.counter
    
    def display(self):
        text = " State of client: {} - ".format(self.name)
        text += "Counter: {} - ".format(self.counter)
        text += "Last sync counter: {} - ".format(self.lastsync_counter)
        text += "Last sync server counter: {}\n".format(self.lastsync_servercounter)
        self.debug_output(text, self.objects)
    
    def debug_output(self, text, objects=None):
        print "{}\n".format(text)
        if not objects:
            print " None";
        else:
            for o in self.objects:
                o.display()
        print " -----------------------------------"
        print ""
        