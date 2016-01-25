Sentient Home Event Engine
==========================

This is a very simple realtime event engine of the Sentient Home project. It
enables the ability to deploy realtime rules and plugins.
The event engine consists of three main modules:

    * The event engine itself: event.engine.py
    * The memory manager: eememory.py
    * The restful API: eeapi.py

Event Engine - event.engine.py
------------------------------

The event engine is an asynchronous multi threaded engine based on Python 3.4
asyncio and the aiohttp package. In addition to the asyncronous webserver, the
engine is - like the rest of the project - based on the Cement framework -
allowing us to define plugins and rules as extensions that can be registered at
runtime through their respective config files.

Because of the underlying frameworks the event engine is very compact and only a
few hundred lines total.

Memory Manager - eememory.py
----------------------------

The memory manager is a simple helper class that manages various in memory
caches for the event engine.
It has the ability to checkpoint the various memory caches to disk using
python's pickle module. This enables the event engine to restart while
preserving in memory caches and states.
