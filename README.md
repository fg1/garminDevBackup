garminDevBackup.py
==================

`garminDevBackup.py` is a script for backing up the activity files (`.FIT`)
stored on your Garmin sport devices (Edge, Forerunner...). Files are
automatically backuped in a tar file. The script works as follows:

1. Detect Garmin devices based on the vendor id of the connected device
2. Mount devices (using [gio](https://developer.gnome.org/gio/) at the moment)
3. Fetch recent activities which have not been yet backuped and store them in
   a tar archive file
4. Optional: umount and eject the device from the computer


Note: _The script only works on Linux at the moment using Gnome specific code.
Additional backends (KDE, pure CLI, Windows...) may be added in the future._



## Installation

On Debian/Ubuntu:
```
# apt-get install python-lxml python-gnome2
$ git clone https://github.com/fg1/garminDevBackup
```


## Usage

```
usage: garminDevBackup.py [-h] [-f F] [-v] [--auto-umount] [--auto-eject]

Backup activities from Garmin devices

optional arguments:
  -h, --help     show this help message and exit
  -f F           Output archive for backup
  -v             Verbose output
  --auto-umount  Automatically unmount Garmin devices after done
  --auto-eject   Automatically eject Garmin devices after done
```

It is possible to store configuration parameters in a config file:
```
$ cp garminDevBackup.conf.example garminDevBackup.conf
$ vim garminDevBackup.conf
```



## Contributing

Contributions are welcome.

1. [Fork the repository](https://github.com/fg1/garminDevBackup/fork)
2. Create your feature branch (`git checkout -b my-feature`)
3. Commit your changes (`git commit -am 'Commit message'`)
4. Push to the branch (`git push origin my-feature`)
5. Create a pull request

