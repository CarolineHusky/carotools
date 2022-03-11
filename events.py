import traceback
from dataclasses import dataclass, make_dataclass
import functools
from typing import Any, Dict, List, Callable, Tuple

class Handler:
    def __init__(self, fire, shouldRun, *args, **kwargs):
        self.fire = fire
        self.shouldRun = shouldRun
        self.args = args
        self.kwargs = kwargs

class Event:
    @classmethod
    def addHandler(
        cls, 
        fire: Callable[[Any], None], 
        shouldRun: Callable[[Any], bool] = None, 
        *args,
        **kwargs):
        if not cls.__name__ in _handlers:
            _handlers[cls.__name__]=[]
        _handlers[cls.__name__].append(Handler(fire, shouldRun, *args, **kwargs))

    def __post_init__(self):
        self.fire(lambda handler: handler.fire)

    def fire(self, function: Callable[[Handler], None]):
        handlerlist=_handlers[type(self).__name__]
        processing = True
        exceptions = {}
        #process the handlers until there ain't no advancement left
        while processing:
            processing = False
            for index,handler in enumerate(handlerlist):
                try:
                    if (not handler.shouldRun) or (handler.shouldRun(self)):
                        function(handler)(self)
                        if handler in exceptions:
                            del exceptions[handler]
                        del handlerlist[index]
                        processing = True
                except UnavailableAttributeError as e:
                    exceptions[handler] = e
        #post-processing: look if any of the unhandled handlers were due to not run
        for index,handler in enumerate(handlerlist):
            try:
                if handler.shouldRun and not handler.shouldRun(self):
                    if handler in exceptions:
                        del exceptions[handler]
                    del handlerlist[index]
            except UnavailableAttributeError as e:
                exceptions[handler] = e
        if len(handlerlist):
            raise UnhandledHandlesException(exceptions)

    # Regenerate object dictionary upon adding field
    def __setattr__(self, name, value):
        self.__dict__[name] = value
        object.__setattr__( # *mild panik* Use object's __setattr__ to avoid infinite recursion
             self,           # ...with ourself
             "__class__",    # ...on our own class behaviour
             make_dataclass( # ...to make a new dataobject
                type(self).__name__,          # ...with name
                fields=self.__dict__,   # ...fields according to our own newly defined fields
                bases=(type(self),)    # ...and based on this own object's definition
                ))

    # Raise custom exception for missing attributes that might be filled in later
    def __getattr__(self, attribute):
        raise UnavailableAttributeError(attribute, self)


_handlers: Dict[str, List[Handler]] = {}

class UnhandledHandlesException(Exception):
    def __init__(self, exceptions):
        for handler in exceptions:
            traceback.print_exception(type(exceptions[handler]), exceptions[handler], exceptions[handler].__traceback__)
        super().__init__("Cannot resolve event, see above")

class UnavailableAttributeError(AttributeError):
    def __init__(self, attribute: str, event: Event):
        self.attribute = attribute
        super().__init__("Unavailable attribute '%s' in %s"%(attribute,event))


def on(eventType: Event, shouldRun: Callable[[Event], bool] = None, *args, **kwargs):
    def decorator(func):
        eventType.addHandler(func, shouldRun, *args, **kwargs)
        @functools.wraps(func)
        def wrapper(item):
            raise SyntaxError("Don't run a event handler directly, please use the event system instead")
        return wrapper
    return decorator


### Small demo program
if __name__=="__main__":
    @dataclass
    class TestEvent(Event):
        text: str
        
    @on(TestEvent, lambda event: event.has_repeated)
    def handler_C(event):
        print("Trying handler C")
        event.text="Repeated: "+event.text
        print("- Handled '%s' inside Handler C"%event)
        
    @on(TestEvent)
    def handler_B(event):
        print("Trying handler B")
        event.text*=event.repeat
        event.has_repeated = True
        print("- Handled '%s' inside Handler B"%event)

    @on(TestEvent)
    def handler_A(event):
        print("Trying handler A")
        event.repeat = 4
        print("- Handled '%s' inside Handler A"%event)

    event = TestEvent(text = "hello")
    print("Result: %s"%event)