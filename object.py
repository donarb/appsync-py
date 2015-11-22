from datetime import datetime
import uuid

class Object:
    
    def __init__(self, pk, name, value, guid=None):
        
        self.pk = pk
        self.name = name
        self.value = value
        self.deleted = False
        self.timestampcreated = datetime.now()
        
        # Do not update this during sync, only when create/update/delete on client or server
        self.timestampupdated = datetime.now()
        self.guid = guid if guid else str(uuid.uuid4())
        self.lastupdate_counter = 0

    def update(self, value):
        self.value = value
        self.timestampupdated = datetime.now()
    
    def delete(self):
        self.deleted = True
        self.timestampupdated = datetime.now()
    
    def display(self):
        text = []
        text.append(" guid: " + self.guid + " - ")
        text.append("pk: " + str(self.pk) + " - ")
        text.append("name: " + self.name + " - ")
        text.append("value: " + self.value + " - ")
        text.append("last update timestamp: " + str(self.timestampupdated) + " - ")
        text.append("last update counter: " + str(self.lastupdate_counter))
        print "".join(text)
        
    