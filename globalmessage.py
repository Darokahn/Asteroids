from dataclasses import dataclass

class Global:
    def __init__(self, channel_names):
        self.channels = dict.fromkeys(channel_names, Channel())
        
    def add_channel(self, ch_name):
        self.channels.update({ch_name: Channel()})
    
    def add_channels(self, ch_names):
        self.channels.update(dict.fromkeys(ch_names, Channel()))
        
    def get_messages(self, ch_name, recipient):
        messages_out = []
        channel = self.channels[ch_name]
        for message in channel:
            message = message.read(recipient)
            if message:
                messages_out.append(message)
        return messages_out
    
    def broadcast(self, channel, message, persistence = 2):
        channel = self.channels[channel]
        channel.append(Message(message, channel, persistence))
        
    def add_listener(self, listener, ch_name):
        channel = self.channels[ch_name]
        channel.add_listener(listener)
        
    def refresh(self):
        for channel in self.channels.values():
            channel.refresh()
        
class Channel:
    def __init__(self, listeners = ()):
        self.messages = []
        self.listeners = set(listeners)

    def add_listener(self, listener):
        self.listeners.add(listener)

    def append(self, item):
        if isinstance(item, Message):
            self.messages.append(item)
        else:
            raise TypeError("Can only append type Message to Channel")
    
    def refresh(self):
        not_expired = lambda message: message.lifetime > 0
        not_all_recipients_read = lambda message: self.listeners != set(message.recipients)
        messages = []
        for message in self.messages:
            if not_all_recipients_read(message) and not_expired(message):
                messages.append(message)
            message.lifetime -= 1
        self.messages = messages
        
    def __iter__(self):
        return iter(self.messages)
            

class Message:
    def __init__(self, message, channel, lifetime):
        self.message = message
        self.lifetime = lifetime
        self.recipients = []
        self.channel = channel
    
    def read(self, r):
        if r not in self.channel.listeners:
            return None
        if r not in self.recipients:
            self.recipients.append(r)
            return self.message
        return None
   
@dataclass
class Obj:
    data: str
    
GLOBAL = Global([])

