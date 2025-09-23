from mcrcon import MCRcon

with MCRcon('10.0.0.70', '1234', port=25575) as mcr:
    print(mcr.command('time set day'))