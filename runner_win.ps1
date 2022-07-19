# In case of stupid policies, run this as admin:
# Set-ExecutionPolicy -Scope CurrentUser Unrestricted

# change this dir to the real location on the device
cd C:\path_to_poketrader
. .\env\Scripts\activate.ps1
python poketrader.py
