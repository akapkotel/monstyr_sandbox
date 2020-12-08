# Monastyr RPG Sandbox Application
### General info
This is my special project written for me and my friends playing the Monastyr Role-Playing game campaign.
It is a pack of tools for players and GM, which makes easier to manage some aspects of game. It contains
two main elements:
1. Lords Manager Tool: simple tkinter window app which allows browsing through the local feudal hierarchy 
of noblemen.
![Manager](https://github.com/akapkotel/monstyr_sandbox/blob/master/lords_manager.png)

2. Interactive Map application written with arcade library, which allows to explore game-area map. The Map
 is under construction.
![Map_window]()

### Technologies
Both applications use a common database, which is a simple shelve file. Code is written in Python 3.8 and
 library used is arcade 2.4.1.

### Setup
Clone or download this repo. Setup virtual environment. Install
requirements. Then you can run:

1. Lords Manager tkinter app by running:

    python lords_manager.tool.py

Inside root directory there is a admin.auth file, which allows you to
modify shelve database in the application. If you leave user.auth only,
modifying data would be impossible. In the future, the user-distributed
version for players would contain only the user.auth file, and the
admin.auth will be available for game-masters version.

2. Lords generator (generating new set of lords and locations) by:

    python lords_manager.py

It is also possible to manually mess with the data by importing
LordsManager class from this file and call it's methods. See -> 4.

4. Manualy modify database.

Open python console, and wrote:

    from lords_manager import LordsManager
    manager = LordsManager()
    manager.load()

Then you can manipulate the data as you wish. For now read docstrings
and comments inside lords_manager.py. In the future there will be a
documentation available.

### Status
In development.

### To be done:
1. Documentation
2. Add tests
3. Better-looking roads (not stright-lines, but some curves).
4. Regions representing nobleman-fiefs.
5. More filtering-options to browse lords and locations.
6. Create single-file executables for linux and windows.
7. Migrate map from arcade to tkinter using canvas to draw locations.
