#!/usr/bin/env python3
# Processes arvhived ADRAD sigmet data files into L2 (for gr2analyst) and UF (for NOAA Weather/Climate Toolkit)
# Created 18 July 2022 by Sam Gardner <stgardner4@tamu.edu>

from os import path, listdir, system, remove
from pathlib import Path
import pyart
import numpy as np
import sys


if __name__ == "__main__":
    basePath = path.dirname(path.realpath(__file__))
    inputDir = path.join(basePath, "input-archive")
    # Check to be sure input directory exists
    if not path.exists(inputDir):
        Path(inputDir).mkdir(parents=True, exist_ok=True)
        print("Please place files to be converted in input-archive/")
        exit()
    # Check command line args to determine if we need to correct azimuth or not
    if len(sys.argv) > 1 and sys.argv[1] == "--correct-az":
        l2paramsPath = path.join(basePath, "params_L2_az-offset.txt")
        ufparamsPath = path.join(basePath, "params_UF_az-offset.txt")
    else:
        l2paramsPath = path.join(basePath, "l2_params.txt")
        ufparamsPath = path.join(basePath, "uf_params.txt")
    # Create output directory if it doesn't already exist
    outputDir = path.join(basePath, "output-archive")
    Path(outputDir).mkdir(parents=True, exist_ok=True)
    # Loop through files in input directory
    inputFiles = sorted(listdir(inputDir))
    for file in inputFiles:
        # Get path to file to read
        pathToRead = path.join(inputDir, file)
        print(f"Reading {pathToRead}")
        # Read file
        radar = pyart.io.read(pathToRead)
        # Get datetime object of radar scan time
        radarScanDT = pyart.util.datetime_from_radar(radar)
        print(radarScanDT.strftime("%Y-%m-%d %H:%M:%S"))
        # Get pulse repetition frequency to determine if this is a volume or survey scan
        if "prt"  not in radar.instrument_parameters:
            # If we don't have a PRT, skip this file
            print("Unable to determine PRF from file "+file)
            continue
        # Frequency is 1/period
        prf = np.round(1/np.mean(radar.instrument_parameters["prt"]["data"]), 0)
        # For reasons that are entirely beyond me, GR2Analyst will only load volume scan files that are converted sigmet->uf by py-ART, then that UF file converted to msg31 by RadxConvert.
        # However, for survey scans, GR2Analyst doesn't accept files that were exported to UF by py-ART. So we convert sigmet->UF using RadxConvert, then UF->L2.
        # *sigh*... I'm not sure if anyone will ever read these comments, but figuring this out took several months and there's next to no documentation on how GR2Analyst reads files and doesn't give error messages.
        if prf > 623.5:
            # If average PRF is greater than 623.5Hz, assume this is a volume scan
            # Use py-ART to convert sigmet->uf
            print(">>> WRITING DATA >>>")
            tmpOutputPath = path.join(outputDir, "tmp_save")
            pyart.io.write_uf(tmpOutputPath, radar)
            # Now we use RadxConvert to convert the tmp UF file to UF (converting py-ART UF to Radx UF allows the azimuth correction to be applied) and to L2 (converting py-ART UF to msg31 L2 for GR2Analyst users)
            # Get paths to output files
            ufoutputPath = path.join(outputDir, "UF", radarScanDT.strftime("%Y%m%d"), "vol", f"TAMU_{radarScanDT.strftime('%Y%m%d')}_{radarScanDT.strftime('%H%M')}")
            L2outputPath = path.join(outputDir, "L2", radarScanDT.strftime("%Y%m%d"), "vol", f"TAMU_{radarScanDT.strftime('%Y%m%d')}_{radarScanDT.strftime('%H%M')}")
            print(">>> CONVERTING >>> "+file+" TO UF")
            # Create output directory if it doesn't already exist
            Path(path.dirname(ufoutputPath)).mkdir(parents=True, exist_ok=True)
            # Convert tmp file to UF
            system(f"/usr/local/lrose/bin/RadxConvert -f {tmpOutputPath} -params {ufparamsPath} -outdir {path.dirname(ufoutputPath)} -outname {path.basename(ufoutputPath)}")
            print(">>> CONVERTING >>> "+file+" TO L2")
            # Create output directory if it doesn't already exist
            Path(path.dirname(L2outputPath)).mkdir(parents=True, exist_ok=True)
            # Convert tmp file to L2
            system(f"/usr/local/lrose/bin/RadxConvert -f {tmpOutputPath} -params {l2paramsPath} -outdir {path.dirname(L2outputPath)} -outname {path.basename(L2outputPath)}")
            remove(tmpOutputPath)
        else:
            # If average PRF is less than 623.5Hz, assume this is a survey scan
            ufoutputPath = path.join(outputDir, "UF", radarScanDT.strftime("%Y%m%d"), "surv", f"TAMU_{radarScanDT.strftime('%Y%m%d')}_{radarScanDT.strftime('%H%M')}")
            L2outputPath = path.join(outputDir, "L2", radarScanDT.strftime("%Y%m%d"), "surv", f"TAMU_{radarScanDT.strftime('%Y%m%d')}_{radarScanDT.strftime('%H%M')}")
            # Use RadxConvert to convert directly from sigmet to UF
            print(">>> CONVERTING >>> "+file+" TO UF")
            # Create output directory if it doesn't already exist
            Path(path.dirname(ufoutputPath)).mkdir(parents=True, exist_ok=True)
            # Convert file to UF
            system(f"/usr/local/lrose/bin/RadxConvert -f {pathToRead} -params {ufparamsPath} -outdir {path.dirname(ufoutputPath)} -outname {path.basename(ufoutputPath)}")
            # Now we take the converted UF file and convert it to L2
            print(">>> CONVERTING >>> "+file+" TO L2")
            # Create output directory if it doesn't already exist
            Path(path.dirname(L2outputPath)).mkdir(parents=True, exist_ok=True)
            # Convert tmp file to L2
            system(f"/usr/local/lrose/bin/RadxConvert -f {ufoutputPath} -params {l2paramsPath} -outdir {path.dirname(L2outputPath)} -outname {path.basename(L2outputPath)}")
        # Clean up
        remove(pathToRead)
        del(radar)
