import logging

from contextvars import ContextVar
from datetime import datetime
from typing import Any, Callable, Dict, Optional


log = logging.getLogger(__name__)


class DebugObject:
    def __init__(self, parent, name=None, serialize: Optional[Callable[[Dict], Dict]] = None):
        self.parent = parent
        if self.parent:
            self.parent.add_child(self)
        self.children = []
        self.name = name
        self.serialize_callback = serialize
        self.values = {}
        self.buttons = {}
        self.change_callbacks = []

    def add_child(self, child: 'DebugObject'):
        self.children.append(child)

    def remove_child(self, child):
        if child:
            try:
                self.children.remove(child)
            except ValueError:
                log.warning(f'Child {child} not found in {self.children}')

    def track(self, name, value):
        self.values[name] = value
        self.notify_change()

    def serialize(self) -> Dict[str, Any]:
        out = {}
        if self.name:
            out[self.name] = {
                'values': self.values.copy(),
                'buttons': self.buttons,
            }
            out[self.name]['values']['timestamp'] = datetime.now().isoformat()
            if self.serialize_callback:
                out[self.name] = self.serialize_callback(out[self.name])
            return out
        out['global'] = {
            'values': {
                'change_callbacks': len(self.change_callbacks),
                'children': len(self.children),
            },
            'buttons': {},
        }
        for child in self.children:
            out.update(child.serialize())
        return out

    def add_notify(self, cb):
        self.change_callbacks.append(cb)

    def remove_notify(self, cb):
        try:
            self.change_callbacks.remove(cb)
        except ValueError:
            log.warning(f'Callback {cb} not found in {self.change_callbacks}')

    def __repr__(self) -> str:
        return f'<DebugObject (name={self.name} id={id(self)})'

    def notify_change(self):
        if self.parent:
            return self.parent.notify_change()

        data = self.serialize()
        for cb in self.change_callbacks:
            try:
                cb(data)
            except Exception as e:
                log.exception(f'Exception in debug callback: {e}')


DEBUG_GLOBAL = ContextVar('debug_global', default=DebugObject(None))
