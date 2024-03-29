# ADRAD python scripts
---
Instructions for processing archived data:

- Place input sigmet raw files in `input-archive/`
- Install the [python arm radar toolkit](https://github.com/ARM-DOE/pyart) version 1.12.8 or later to your conda environment. (at the time of this writing, this has not yet been released and you'll need to clone py-art and build from source using pip)
- Install [lrose-core](https://github.com/NCAR/lrose-core) version 20220222 (Topaz) or newer
- run `python3 processArchive.py`. Optionally add `--correct-az` flag to apply 1.8 degree offset to azimuth for all scans

Instructions for running realtime processing of radar files while ADRAD is running:

- Install the [python arm radar toolkit](https://github.com/ARM-DOE/pyart) version 1.12.8 or later to your conda environment. (at the time of this writing, this has not yet been released and you'll need to clone py-art and build from source using pip)
- Install [lrose-core](https://github.com/NCAR/lrose-core) version 20220222 (Topaz) or newer
- Edit config.txt with the path to your python interpreter desired output paths for archival and real-time data. Make sure that the user account that executes these scripts has read and write permissions for the output directories
- On the ADRAD computer, copy "run_on_adrad.sh" to /home/operator/ and add `* * * * * /bin/bash /home/operator/run_on_adrad.sh` to to crontab by running `crontab -e`
- Start the radar
- Run "run.sh"
- After 15 minutes of not receiving any new data, ALL of the previously received files will be processed in archive mode

Instructions for automatically running realtime processing of radar files when ADRAD starts up (as a systemd service):
- on the processing server, run the following commands:
`sudo cp adrad_proc.service /etc/systemd/system`
`sudo systemctl enable adrad_proc.service`
`sudo systemctl start adrad_proc.service`

Check status using `sudo systemctl status adrad_proc.service` and view stdout using `sudo journalctl -u adrad_proc.service -f -n`
