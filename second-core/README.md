# Second Core for Home Assistant

[!["Buy Me A Coffee"](https://raw.githubusercontent.com/Smeagolworms4/donate-assets/master/coffee.png)](https://www.buymeacoffee.com/smeagolworms4)
[!["Buy Me A Coffee"](https://raw.githubusercontent.com/Smeagolworms4/donate-assets/master/paypal.png)](https://www.paypal.com/donate/?business=SURRPGEXF4YVU&no_recurring=0&item_name=Hello%2C+I%27m+SmeagolWorms4.+For+my+open+source+projects.%0AThanks+you+very+mutch+%21%21%21&currency_code=EUR)

Run a second home assistante core on port 8124

The second core always listens on port 8124 inside the container, whatever the
Home Assistant version (2026.8 changed the default port to 80 under Supervisor).
To reach it on another port, change the host port in the add-on *Network*
settings.

Origonal GitHub: https://github.com/Smeagolworms4/ha_second_core
