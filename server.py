from object import Object


OK  = 1
NOK = 0



class Server():
    
    def __init__(self, name):
        self.name = name
        self.counter = 0
        self.objects = []
    
    def sync_to_client(self, counter):
        
        objects = [o for o in self.objects if o.lastupdate_counter > counter]
        result = {
            'statuscode': OK,
            'servercounter': self.counter,
            'objects': objects
        }
        return result
    
    def sync_from_client(self, objects):
        
        result = {}
        for sob in objects:
            
            exists = False
            conflict = False
            
            for o in self.objects:
                if o.guid == sob.guid:
                    exists = True
                    o.value = sob.value
                    o.deleted = sob.deleted
                    self.counter += 1
                    o.lastupdate_counter = self.counter
                elif o.pk == sob.pk:
                    # pk conflict: do nothing because this should not occur on server
                    # client will always sync from server to client first and handle
                    # any pk conflicts before syncing from client to server
                    exists = True
                    conflict = True
                    result['statuscode'] = NOK
            
            if not exists:
                no = Object(pk=sob.pk, name=sob.name, value=sob.value, guid=sob.guid)
                no.deleted = sob.deleted
                self.counter += 1
                no.lastupdate_counter = self.counter
                self.objects.append(no)
        
        if 'statuscode' not in result:
            result['statuscode'] = OK
        result['servercounter']  = self.counter
        return result
    
    def add_object(self, pk, name, value):
        ''' Create object on server (do not use this function to add
        object from a client sync '''
        obj = Object(pk=pk, name=name, value=value)
        self.counter += 1
        obj.lastupdate_counter = self.counter
        self.objects.append(obj)
    
    def update_object(self, pk, value):
        ''' Update object on server (do not use this function to update
        object from a client sync '''
        for o in self.objects:
            if o.pk == pk:
                o.update(value)
                self.counter += 1
                o.lastupdate_counter = self.counter
    
    def delete_object(self, pk):
        ''' Delete object on server (do not use this function to delete
        object from a client sync '''
        for o in self.objects:
            if o.pk == pk:
                o.delete()
                self.counter += 1
                o.lastupdate_counter = self.counter
    
    def display(self):
        text = []
        text.append(" State of server: " + self.name + " - ")
        text.append("Counter: " + str(self.counter) + "\n")
        self.debug_output("".join(text), self.objects)
    
    def debug_output(self, text, objects=None):
        print "{}\n".format(text)
        for o in self.objects:
            o.display()
        print " -----------------------------------"
        print ""
