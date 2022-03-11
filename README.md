# carotools
 Caroline's Python Tools

## Events

This small module implements a simple stateful event system, using decorators and dataclasses.
It resolves automatically, hence if a event.property is referred by a handler before it's set by another handler, the Carotools.Events library will repeat that first handler afterwards with the correct property set.
TODO: Write documentation