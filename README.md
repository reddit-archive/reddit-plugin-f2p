# reddit April Fools 2013

Required config
---------------
Add the following to your `.update` file:
```ini
[DEFAULT]
f2pcaches = localhost:11211
plugins = f2p

[live_config]
# In seconds (decimals allowed)
# Learn math for more info: http://en.wikipedia.org/wiki/Tolerance_interval
drop_cooldown_mu = 5
drop_cooldown_sigma = 2
# List of name to percentages
f2p_rarity_weights = common: 80, uncommon: 15, rare: 3, artifact: 2
```

Rememer to run `python setup.py develop` in the plugin directory and `write_live_config` if you are running zookeeper.
