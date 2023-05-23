import communication


class Player:
    def __init__(self, organizer, **setup) -> None:
        # should connect to organizer and get list
        # but for now gets it in kwargs
        # so setup needs to contain playid & participants
        if "playid" in setup.keys():
            self.playid_ = setup["playid"]
            self.participants_ = setup["participants"]
            self.setup = True
        
    def setup(self) -> None:
        for i in range(self.playid_):

    
