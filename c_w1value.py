class W1Value:
    def __init__(self, addr:int, max_change:float=10.0, max_ignore:int=3):
        """
        :max_change: max accepted change against recent value. set negative to ignore
        :max_ignore: max times to ignore larger change and return recent value
        """
        self.address = addr
        self.value = 0.0
        self.maxchange = max_change
        self.maxignore = max_ignore
        self.ignored = 0
        self.inited = False
    
    def checked(self, newval):
        if self.maxchange <= 0.0:
            # e.g. non-scalar values
            return newval
        elif self.inited:
            if abs(self.value - newval) <= self.maxchange:
                self.value = newval
                self.ignored = 0
            elif(self.ignored <= self.maxignore):
                # keep & return recent value
                self.ignored += 1
            else:
                self.value = newval
                #self.ignored = 0
        else:
            self.value = newval
            self.inited = True
        return self.value




