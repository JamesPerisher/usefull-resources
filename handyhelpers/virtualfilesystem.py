from collections import OrderedDict


class VirtualObject(object):
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = self if not parent else parent
    def _add(self):
        pass
    
    def render(self):
        # return [str(self.name)]
        return ["{}.{}".format(self.__class__.__name__, self.name)]

class VirtualDir(VirtualObject):
    def __init__(self, name, autoadd=False):
        super().__init__(name)
        self.data = OrderedDict()
        self.autoadd = autoadd
        self.append(self)
    def _add(self):
        self.autoadd = self.parent.autoadd

    def __repr__(self) -> str:
        # return "{}.{}".format(self.__class__.__name__, self.name)
        return "{}(name='{}', {})".format(self.__class__.__name__, self.name, self.data)

    def __iter__(self):
        _iter = iter(self.data.values())
        next(_iter)
        return _iter
    
    def __getitem__(self, key) -> None:
        return self.data[key]

    def append(self, item: VirtualObject):
        self.data[item.name] = item
        item.parent = self
        item._add()

    def get_children(self):
        return list(self.data.values())[1::]
    def get_parent(self):
        return self.parent
    
    def _open(self, filepath, file):
        current = self
        walk = filepath.replace("\\", "/").split("/")
        while len(walk) > 0:
            itemname = walk.pop(0)
            try:
                current = current[itemname]
            except KeyError as e:
                if self.autoadd:
                    if len(walk) == 0 and file:
                        _current = VirtualFile(itemname)
                    else:
                        _current = VirtualDir(itemname, True)
                    current.append(_current)
                    current = _current
                    continue
                raise e          
        return current

    def openfile(self, filepath):
        _obj = self._open(filepath, True)
        if isinstance(_obj, VirtualFile):
            return _obj
        raise ValueError("Value for '{}' is not of type '{}'.".format(filepath, VirtualFile.__class__.__name__))

    def open(self, filepath):
        return self._open(filepath, False)
    
    def opendir(self, filepath):
        _obj = self._open(filepath, True)
        if isinstance(_obj, VirtualDir):
            return _obj
        raise ValueError("Value for '{}' is not of type '{}'.".format(filepath, VirtualDir.__class__.__name__))

    def render(self):
        out = []
        out.append(super().render()[0])
        for i in self:
            out += ["    "+str(x) for x in i.render()]

        return out


class VirtualDrive(VirtualDir):
    def __init__(self, drivename="V:", autoadd=False):
        super().__init__(drivename, autoadd)


class VirtualFile(VirtualObject):
    def __init__(self, name, method="t", doclose=True):
        super().__init__(name)
        self.method = list(method)
        self.data = b'' if "b" in self.method else ""
        self.closed = False
        self.doclose = doclose

    def __repr__(self):
        return "{}(name='{}',methods='{}', doclose={})".format(self.__class__.__name__, self.name, "".join(self.method), self.doclose)

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    def check(function):
        def func(self, *args, **kwargs):
            if not self.doclose:
                return function(self, *args, **kwargs)
            if self.closed:
                raise ValueError("I/O operation on closed file.")
            return function(self, *args, **kwargs)
        return func

    @check
    def close(self):
        self.closed = True

    @check
    def truncate(self):
        self.data = b'' if "b" in self.method else ""

    @check
    def read(self):
        return self.data

    @check
    def write(self, data):
        self.data = self.data + data
